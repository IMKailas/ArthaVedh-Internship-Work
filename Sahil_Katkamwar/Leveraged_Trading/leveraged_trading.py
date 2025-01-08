import pandas as pd
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    filename='leveraged_trading_strategy.log',  # Log file name
    level=logging.DEBUG,  # Log level (DEBUG will log all levels)
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_market_data(file_path):
    """Load and prepare market data from CSV"""
    data = pd.read_csv(file_path)
    logging.info(f"Market data loaded from {file_path}")
    return data


def calculate_position_size(balance, leverage, current_price, risk_per_trade_pct):
    """Calculate position size based on account balance and leverage"""
    max_position_value = balance * leverage * risk_per_trade_pct
    units = max_position_value / current_price
    return units


def calculate_liquidation_price(entry_price, position_type, leverage, margin_requirement):
    """Calculate liquidation price for leveraged position"""
    if position_type == "Long":
        return entry_price * (1 - (1 / leverage) + margin_requirement)
    return entry_price * (1 + (1 / leverage) - margin_requirement)


def leveraged_trading_strategy(data, params):
    """Enhanced leveraged trading strategy"""
    balance = params['initial_balance']
    initial_balance = balance
    leverage = params['leverage']
    margin_requirement = params['margin_requirement']
    position = None
    position_size = 0
    entry_price = 0
    trades = []

    for i in range(1, len(data)):
        current_row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        current_price = current_row['close']

        # Skip if any critical indicators are NaN
        if pd.isna(current_row['RSI']) or pd.isna(current_row['MACD']) or pd.isna(current_row['Signal']):
            continue

        # Entry and exit signals
        rsi_oversold = current_row['RSI'] < 30
        rsi_overbought = current_row['RSI'] > 70
        macd_crossover = prev_row['MACD'] < prev_row['Signal'] and current_row['MACD'] > current_row['Signal']
        macd_crossunder = prev_row['MACD'] > prev_row['Signal'] and current_row['MACD'] < current_row['Signal']
        price_above_vwap = current_price > current_row['VWAP']
        price_below_vwap = current_price < current_row['VWAP']

        # Volume confirmation
        volume_spike = current_row['Volume'] > current_row['Volume MA']

        # Position Management
        if position is None:
            # Long Entry
            if (rsi_oversold or macd_crossover) and price_above_vwap and volume_spike:
                position_size = calculate_position_size(
                    balance, leverage, current_price, params['risk_per_trade_pct']
                )
                position = "Long"
                entry_price = current_price
                liquidation_price = calculate_liquidation_price(
                    entry_price, position, leverage, margin_requirement
                )
                logging.info(f"Long Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, Balance: {balance:.2f}, Reason: RSI oversold or MACD crossover")

            # Short Entry
            elif (rsi_overbought or macd_crossunder) and price_below_vwap and volume_spike:
                position_size = calculate_position_size(
                    balance, leverage, current_price, params['risk_per_trade_pct']
                )
                position = "Short"
                entry_price = current_price
                liquidation_price = calculate_liquidation_price(
                    entry_price, position, leverage, margin_requirement
                )
                logging.info(f"Short Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, Balance: {balance:.2f}, Reason: RSI overbought or MACD crossunder")

        else:  # Managing existing position
            # Calculate current profit/loss
            if position == "Long":
                unrealized_pnl = position_size * (current_price - entry_price) * leverage

                # Exit conditions for long
                if (current_price <= liquidation_price or  # Liquidation
                        rsi_overbought or  # RSI exit
                        macd_crossunder or  # MACD exit
                        unrealized_pnl <= -balance * params['max_loss_per_trade']):  # Stop loss

                    pnl = position_size * (current_price - entry_price) * leverage
                    balance += pnl

                    trades.append({
                        'type': 'Long',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })

                    logging.info(f"Long Exit - Price: {current_price:.2f}, PnL: {pnl:.2f}, Balance: {balance:.2f}, Reason: Liquidation or Stop loss")
                    position = None

            else:  # Short position
                unrealized_pnl = position_size * (entry_price - current_price) * leverage

                # Exit conditions for short
                if (current_price >= liquidation_price or  # Liquidation
                        rsi_oversold or  # RSI exit
                        macd_crossover or  # MACD exit
                        unrealized_pnl <= -balance * params['max_loss_per_trade']):  # Stop loss

                    pnl = position_size * (entry_price - current_price) * leverage
                    balance += pnl

                    trades.append({
                        'type': 'Short',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })

                    logging.info(f"Short Exit - Price: {current_price:.2f}, PnL: {pnl:.2f}, Balance: {balance:.2f}, Reason: Liquidation or Stop loss")
                    position = None

        # Risk management - stop trading if significant losses
        if balance < initial_balance * 0.5:
            logging.warning(f"Strategy stopped - Significant losses. Balance: {balance:.2f}")
            break

    # Calculate strategy metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['pnl'] for t in trades)
        max_drawdown = min(t['balance'] for t in trades) - initial_balance if trades else 0
    else:
        profitable_trades = 0
        win_rate = 0
        total_profit = 0
        max_drawdown = 0

    logging.info("Strategy results: ")
    logging.info(f"Initial Balance: ${initial_balance:.2f}")
    logging.info(f"Final Balance: ${balance:.2f}")
    logging.info(f"Total Profit/Loss: ${total_profit:.2f}")
    logging.info(f"Return: {((balance - initial_balance) / initial_balance) * 100:.2f}%")
    logging.info(f"Total Trades: {total_trades}")
    logging.info(f"Profitable Trades: {profitable_trades}")
    logging.info(f"Win Rate: {win_rate:.2f}%")
    logging.info(f"Max Drawdown: ${abs(max_drawdown):.2f}")

    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'max_drawdown': max_drawdown,
        'return_pct': ((balance - initial_balance) / initial_balance) * 100,
        'trades': trades
    }

# Strategy parameters
params = {
    'initial_balance': 10000,
    'leverage': 10,  # Increased leverage for more aggressive trading
    'margin_requirement': 0.1,  # 10% margin requirement
    'risk_per_trade_pct': 0.1,  # Risk 10% per trade
    'max_loss_per_trade': 0.05  # Maximum 5% loss per trade
}

# File path - adjust this to your actual file path
file_path = './NSE_NIFTY_Intraday.csv'  # Update this path

try:
    # Load and run strategy
    data = load_market_data(file_path)
    results = leveraged_trading_strategy(data, params)

    # Print detailed results
    print("\nStrategy Results:")
    print(f"Initial Balance: ${results['initial_balance']:.2f}")
    print(f"Final Balance: ${results['final_balance']:.2f}")
    print(f"Total Profit/Loss: ${results['total_profit']:.2f}")
    print(f"Return: {results['return_pct']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Profitable Trades: {results['profitable_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Max Drawdown: ${abs(results['max_drawdown']):.2f}")

    # Print individual trades if requested
    print("\nRecent Trades:")
    for trade in results['trades'][-5:]:  # Show last 5 trades
        print(f"Type: {trade['type']}, Entry: {trade['entry']:.2f}, "
              f"Exit: {trade['exit']:.2f}, PnL: ${trade['pnl']:.2f}")

except FileNotFoundError:
    logging.error(f"File not found: {file_path}")
except Exception as e:
    logging.error(f"Error occurred: {str(e)}")
