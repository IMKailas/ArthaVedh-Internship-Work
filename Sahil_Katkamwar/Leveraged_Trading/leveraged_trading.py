import pandas as pd
import logging
import talib
import config

# Set up logging
logging.basicConfig(
    filename=config.LOG_FILE,
    level=config.LOG_LEVEL,
    format=config.LOG_FORMAT
)


def load_market_data(file_path):
    """Load and prepare market data from CSV"""
    data = pd.read_csv(file_path)
    logging.info(f"Market data loaded from {file_path}")
    return data


def calculate_technical_indicators(data):
    """Calculate technical indicators using TA-Lib"""
    # RSI
    data['RSI'] = talib.RSI(data['close'], timeperiod=config.RSI_PERIOD)

    # MACD
    data['MACD'], data['Signal'], data['MACD_Hist'] = talib.MACD(
        data['close'],
        fastperiod=12,
        slowperiod=26,
        signalperiod=9
    )

    # Volume Moving Average
    data['Volume MA'] = talib.SMA(data['Volume'], timeperiod=config.VOLUME_MA_PERIOD)

    # VWAP (Volume Weighted Average Price)
    data['VWAP'] = (data['Volume'] * data['close']).cumsum() / data['Volume'].cumsum()

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
    # Preprocess data with technical indicators
    data = calculate_technical_indicators(data)

    balance = params.get('initial_balance', config.INITIAL_BALANCE)
    initial_balance = balance
    leverage = params.get('leverage', config.LEVERAGE)
    margin_requirement = params.get('margin_requirement', config.MARGIN_REQUIREMENT)
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
        rsi_oversold = current_row['RSI'] < config.RSI_OVERSOLD
        rsi_overbought = current_row['RSI'] > config.RSI_OVERBOUGHT
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
                    balance, leverage, current_price, params.get('risk_per_trade_pct', config.RISK_PER_TRADE_PCT)
                )
                position = "Long"
                entry_price = current_price
                liquidation_price = calculate_liquidation_price(
                    entry_price, position, leverage, margin_requirement
                )
                logging.info(
                    f"Long Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, Balance: {balance:.2f}, Reason: RSI oversold or MACD crossover")

            # Short Entry
            elif (rsi_overbought or macd_crossunder) and price_below_vwap and volume_spike:
                position_size = calculate_position_size(
                    balance, leverage, current_price, params.get('risk_per_trade_pct', config.RISK_PER_TRADE_PCT)
                )
                position = "Short"
                entry_price = current_price
                liquidation_price = calculate_liquidation_price(
                    entry_price, position, leverage, margin_requirement
                )
                logging.info(
                    f"Short Entry - Price: {entry_price:.2f}, Size: {position_size:.2f}, Balance: {balance:.2f}, Reason: RSI overbought or MACD crossunder")

        else:  # Managing existing position
            # Calculate current profit/loss
            if position == "Long":
                unrealized_pnl = position_size * (current_price - entry_price) * leverage

                # Exit conditions for long
                if (current_price <= liquidation_price or  # Liquidation
                        rsi_overbought or  # RSI exit
                        macd_crossunder or  # MACD exit
                        unrealized_pnl <= -balance * params.get('max_loss_per_trade',
                                                                config.MAX_LOSS_PER_TRADE)):  # Stop loss

                    pnl = position_size * (current_price - entry_price) * leverage
                    balance += pnl

                    trades.append({
                        'type': 'Long',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })

                    logging.info(
                        f"Long Exit - Price: {current_price:.2f}, PnL: {pnl:.2f}, Balance: {balance:.2f}, Reason: Liquidation or Stop loss")
                    position = None

            else:  # Short position
                unrealized_pnl = position_size * (entry_price - current_price) * leverage

                # Exit conditions for short
                if (current_price >= liquidation_price or  # Liquidation
                        rsi_oversold or  # RSI exit
                        macd_crossover or  # MACD exit
                        unrealized_pnl <= -balance * params.get('max_loss_per_trade',
                                                                config.MAX_LOSS_PER_TRADE)):  # Stop loss

                    pnl = position_size * (entry_price - current_price) * leverage
                    balance += pnl

                    trades.append({
                        'type': 'Short',
                        'entry': entry_price,
                        'exit': current_price,
                        'pnl': pnl,
                        'balance': balance
                    })

                    logging.info(
                        f"Short Exit - Price: {current_price:.2f}, PnL: {pnl:.2f}, Balance: {balance:.2f}, Reason: Liquidation or Stop loss")
                    position = None

        # Risk management - stop trading if significant losses
        if balance < initial_balance * config.MAX_DRAWDOWN_PCT:
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
        profitable_trades = win_rate = total_profit = max_drawdown = 0

    logging.info("Strategy results:")
    logging.info(f"Initial Balance: Rs.{initial_balance:.2f}")
    logging.info(f"Final Balance: Rs.{balance:.2f}")
    logging.info(f"Total Profit/Loss: Rs.{total_profit:.2f}")
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
        'max_drawdown': max_drawdown,
        'return_pct': ((balance - initial_balance) / initial_balance) * 100,
        'trades': trades
    }


# Strategy parameters with config values
params = {
    'initial_balance': config.INITIAL_BALANCE,
    'leverage': config.LEVERAGE,
    'margin_requirement': config.MARGIN_REQUIREMENT,
    'risk_per_trade_pct': config.RISK_PER_TRADE_PCT,
    'max_loss_per_trade': config.MAX_LOSS_PER_TRADE
}

try:
    # Load and run strategy
    data = load_market_data(config.DATA_FILE)
    results = leveraged_trading_strategy(data, params)

except FileNotFoundError:
    logging.error(f"File not found: {config.DATA_FILE}")
except Exception as e:
    logging.error(f"Error occurred: {str(e)}")