import pandas as pd
import logging
from datetime import datetime
import config

# Set up logging
logging.basicConfig(
    filename=config.LOG_CONFIG['filename'],
    level=getattr(logging, config.LOG_CONFIG['level']),
    format=config.LOG_CONFIG['format']
)


def load_market_data(file_path):
    """Load and prepare market data from CSV"""
    data = pd.read_csv(file_path)
    logging.info(f"Market data loaded from {file_path}")
    return data


def calculate_position_size(balance, risk_per_trade_pct, current_price):
    """Calculate position size based on account balance"""
    position_value = balance * risk_per_trade_pct
    units = position_value / current_price
    return units


def rebate_trading_strategy(data):
    """Rebate trading strategy implementation"""
    balance = config.INITIAL_BALANCE
    initial_balance = balance
    position = None
    position_size = 0
    entry_price = 0
    trades = []
    rebate_earned = 0

    for i in range(1, len(data)):
        current_row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        current_price = current_row['close']

        # Skip if any critical indicators are NaN
        if pd.isna(current_row['RSI']) or pd.isna(current_row['VWAP']):
            continue

        # Calculate price levels for limit orders
        upper_band = current_row['Upper Band #1']
        lower_band = current_row['Lower Band #1']
        vwap = current_row['VWAP']

        # Volume analysis
        volume_spike = current_row['Volume'] > current_row['Volume MA']

        # Position Management
        if position is None:
            # Long Entry Conditions (Limit order below market)
            if (current_row['RSI'] < config.LONG_ENTRY['rsi_threshold'] and
                    current_price < vwap and
                    current_price > lower_band and
                    volume_spike):

                limit_price = current_price * config.LONG_ENTRY['price_adjustment']
                position_size = calculate_position_size(
                    balance, config.RISK_PER_TRADE_PCT, limit_price
                )
                position = "Long"
                entry_price = limit_price

                # Calculate rebate earned
                rebate_earned = position_size * limit_price * config.MAKER_REBATE
                balance += rebate_earned

                logging.info(f"Long Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, "
                           f"Balance: {balance:.2f}, Rebate Earned: {rebate_earned:.2f}, "
                           f"Reason: RSI < {config.LONG_ENTRY['rsi_threshold']} & Price < VWAP")

            # Short Entry Conditions (Limit order above market)
            elif (current_row['RSI'] > config.SHORT_ENTRY['rsi_threshold'] and
                  current_price > vwap and
                  current_price < upper_band and
                  volume_spike):

                limit_price = current_price * config.SHORT_ENTRY['price_adjustment']
                position_size = calculate_position_size(
                    balance, config.RISK_PER_TRADE_PCT, limit_price
                )
                position = "Short"
                entry_price = limit_price

                # Calculate rebate earned
                rebate_earned = position_size * limit_price * config.MAKER_REBATE
                balance += rebate_earned

                logging.info(f"Short Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, "
                           f"Balance: {balance:.2f}, Rebate Earned: {rebate_earned:.2f}, "
                           f"Reason: RSI > {config.SHORT_ENTRY['rsi_threshold']} & Price > VWAP")

        else:  # Managing existing position
            if position == "Long":
                # Exit conditions for long
                if (current_row['RSI'] > config.LONG_EXIT['rsi_threshold'] or
                        current_price > upper_band or
                        current_row['%K'] > config.LONG_EXIT['stochastic_threshold']):
                    # Calculate PnL including rebates and fees
                    price_pnl = position_size * (current_price - entry_price)
                    fee = position_size * current_price * config.TAKER_FEE
                    total_pnl = price_pnl - fee

                    balance += total_pnl

                    trades.append({
                        'type': 'Long',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': total_pnl,
                        'rebate': rebate_earned,
                        'fee': fee,
                        'balance': balance
                    })

                    logging.info(f"Long Exit - Price: {current_price:.2f}, PnL: {total_pnl:.2f}, "
                               f"Balance: {balance:.2f}, Fee: {fee:.2f}")
                    position = None

            else:  # Short position
                # Exit conditions for short
                if (current_row['RSI'] < config.SHORT_EXIT['rsi_threshold'] or
                        current_price < lower_band or
                        current_row['%K'] < config.SHORT_EXIT['stochastic_threshold']):
                    # Calculate PnL including rebates and fees
                    price_pnl = position_size * (entry_price - current_price)
                    fee = position_size * current_price * config.TAKER_FEE
                    total_pnl = price_pnl - fee

                    balance += total_pnl

                    trades.append({
                        'type': 'Short',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': total_pnl,
                        'rebate': rebate_earned,
                        'fee': fee,
                        'balance': balance
                    })

                    logging.info(f"Short Exit - Price: {current_price:.2f}, PnL: {total_pnl:.2f}, "
                               f"Balance: {balance:.2f}, Fee: {fee:.2f}")
                    position = None

        # Risk management
        if balance < initial_balance * (1 - config.MAX_DRAWDOWN_PCT):
            logging.warning(f"Strategy stopped - Significant losses. Balance: {balance:.2f}")
            break

    # Calculate strategy metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['pnl'] for t in trades)
        total_rebates = sum(t['rebate'] for t in trades)
        total_fees = sum(t['fee'] for t in trades)
        max_drawdown = min(t['balance'] for t in trades) - initial_balance if trades else 0
    else:
        profitable_trades = win_rate = total_profit = total_rebates = total_fees = max_drawdown = 0

    # Log final results
    logging.info("\nStrategy Final Results:")
    logging.info(f"Initial Balance: Rs.{initial_balance:.2f}")
    logging.info(f"Final Balance: Rs.{balance:.2f}")
    logging.info(f"Total Profit/Loss: Rs.{total_profit:.2f}")
    logging.info(f"Total Rebates Earned: Rs.{total_rebates:.2f}")
    logging.info(f"Total Fees Paid: Rs.{total_fees:.2f}")
    logging.info(f"Net P/L (incl. rebates): Rs.{(total_profit + total_rebates - total_fees):.2f}")
    logging.info(f"Return: {((balance - initial_balance) / initial_balance) * 100:.2f}%")
    logging.info(f"Total Trades: {total_trades}")
    logging.info(f"Profitable Trades: {profitable_trades}")
    logging.info(f"Win Rate: {win_rate:.2f}%")
    logging.info(f"Max Drawdown: Rs.{abs(max_drawdown):.2f}")

    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'total_rebates': total_rebates,
        'total_fees': total_fees,
        'max_drawdown': max_drawdown,
        'return_pct': ((balance - initial_balance) / initial_balance) * 100,
        'trades': trades
    }


if __name__ == "__main__":
    try:
        # Load and run strategy
        data = load_market_data(config.DATA_FILE_PATH)
        results = rebate_trading_strategy(data)

    except FileNotFoundError:
        logging.error(f"File not found: {config.DATA_FILE_PATH}")
    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")