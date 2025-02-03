import pandas as pd
import numpy as np
import logging
import talib
from datetime import datetime
import config

# Set up logging
logging.basicConfig(
    filename=config.LOG_FILE,
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)

def calculate_indicators(df):
    """Calculate technical indicators using TA-Lib"""
    logging.info("Calculating technical indicators...")

    # Convert timestamp column if it exists
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

    # VWAP Calculation (manual as TA-Lib doesn't have VWAP)
    df['Cum_Vol'] = df['Volume'].cumsum()
    df['Cum_Vol_Price'] = (df['Plot'] * df['Volume']).cumsum()
    df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']

    # TA-Lib Indicators
    # RSI
    df['RSI'] = talib.RSI(df['Plot'], timeperiod=config.RSI_PERIOD)

    # Volume Moving Average
    df['Volume_MA'] = talib.SMA(df['Volume'], timeperiod=config.VOLUME_MA_PERIOD)
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

    # Price Moving Average
    df['Price_MA'] = talib.SMA(df['Plot'], timeperiod=config.PRICE_MA_PERIOD)

    # Price Momentum (percentage change)
    df['Price_Momentum'] = df['Plot'].pct_change(periods=config.MOMENTUM_LOOKBACK) * 100

    # ATR for volatility-based exits
    df['ATR'] = talib.ATR(df['Plot'], df['Plot'], df['Plot'], timeperiod=config.ATR_PERIOD)

    logging.info("Technical indicators calculated successfully.")
    return df

def check_entry_signal(df, i):
    """Identify entry signals based on momentum and volume"""
    current = df.iloc[i]

    # Basic trend and momentum checks
    price_above_ma = current['Plot'] > current['Price_MA']
    volume_active = current['Volume_Ratio'] > config.MIN_VOLUME_RATIO
    momentum_positive = current['Price_Momentum'] > 0

    # VWAP relationship
    price_above_vwap = current['Plot'] > current['VWAP']

    # RSI conditions
    rsi_healthy = config.RSI_OVERSOLD < current['RSI'] < config.RSI_OVERBOUGHT

    # Entry signals
    long_signal = (price_above_ma and price_above_vwap and
                   volume_active and momentum_positive and rsi_healthy)

    short_signal = (not price_above_ma and not price_above_vwap and
                    volume_active and not momentum_positive and rsi_healthy)

    return "LONG" if long_signal else "SHORT" if short_signal else None

def calculate_exit_points(entry_price, position_type, atr):
    """Calculate stop loss and take profit levels"""
    atr_multiple = atr * config.ATR_MULTIPLIER

    if position_type == "LONG":
        stop_loss = entry_price - atr_multiple
        take_profit = entry_price + (atr_multiple * config.TAKE_PROFIT_RATIO)
    else:  # SHORT
        stop_loss = entry_price + atr_multiple
        take_profit = entry_price - (atr_multiple * config.TAKE_PROFIT_RATIO)

    return stop_loss, take_profit

def check_exit_signals(df, i, position_type, entry_price, stop_loss, take_profit, entry_time):
    """Check exit conditions for positions"""
    current = df.iloc[i]
    current_price = current['Plot']
    current_time = df.index[i]

    # Initialize exit reason
    exit_reason = None

    # Price-based exits
    if position_type == "LONG":
        if current_price <= stop_loss:
            exit_reason = "Stop Loss"
        elif current_price >= take_profit:
            exit_reason = "Take Profit"
        elif current_price < current['VWAP']:
            exit_reason = "VWAP Breakdown"
    else:  # SHORT
        if current_price >= stop_loss:
            exit_reason = "Stop Loss"
        elif current_price <= take_profit:
            exit_reason = "Take Profit"
        elif current_price > current['VWAP']:
            exit_reason = "VWAP Breakout"

    # Time-based exit
    if isinstance(current_time, pd.Timestamp) and isinstance(entry_time, pd.Timestamp):
        time_diff = (current_time - entry_time).total_seconds()
        if time_diff > config.MAX_POSITION_DURATION:
            exit_reason = "Time Exit"

    return bool(exit_reason), exit_reason

def run_momentum_strategy(data_path, initial_balance=None):
    """Execute momentum scalping strategy"""
    if initial_balance is None:
        initial_balance = config.INITIAL_BALANCE

    logging.info(f"Starting Momentum Strategy with initial balance: Rs.{initial_balance:,.2f}")

    # Load and prepare data
    df = pd.read_csv(data_path)

    # Ensure we have a timestamp column for time-based calculations
    if 'timestamp' not in df.columns:
        df['timestamp'] = pd.date_range(start=datetime.now().date(), periods=len(df), freq='1min')

    df = calculate_indicators(df)

    # Initialize trading variables
    balance = initial_balance
    position = None
    entry_price = None
    entry_time = None
    trades = []
    daily_trades = 0

    # Trading loop
    for i in range(config.PRICE_MA_PERIOD, len(df)):
        current_price = df.iloc[i]['Plot']

        if position is None:  # Looking for entry
            if daily_trades >= config.MAX_TRADES_PER_DAY:
                continue

            position_signal = check_entry_signal(df, i)

            if position_signal:
                position = position_signal
                entry_price = current_price
                entry_time = df.index[i]
                stop_loss, take_profit = calculate_exit_points(
                    entry_price, position, df.iloc[i]['ATR']
                )
                daily_trades += 1

                logging.info(f"""
                Entry:
                Time: {entry_time}
                Position: {position}
                Price: {entry_price:.2f}
                Stop Loss: {stop_loss:.2f}
                Take Profit: {take_profit:.2f}
                """)

        else:  # Managing existing position
            should_exit, exit_reason = check_exit_signals(
                df, i, position, entry_price, stop_loss, take_profit, entry_time
            )

            if should_exit:
                profit = (current_price - entry_price) if position == "LONG" else (entry_price - current_price)
                balance += profit

                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.index[i],
                    'position': position,
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'profit': profit,
                    'exit_reason': exit_reason
                })

                logging.info(f"""
                Exit:
                Time: {df.index[i]}
                Position: {position}
                Exit Price: {current_price:.2f}
                Profit/Loss: Rs.{profit:.2f}
                Reason: {exit_reason}
                New Balance: Rs.{balance:.2f}
                """)

                position = None

                # Check drawdown limit
                if balance < initial_balance * (1 - config.MAX_DRAWDOWN_PCT):
                    logging.warning(f"Strategy stopped - Maximum drawdown reached. Balance: Rs.{balance:.2f}")
                    break

    # Calculate performance metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['profit'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['profit'] for t in trades)
        max_drawdown = min(t['profit'] for t in trades)
    else:
        profitable_trades = win_rate = total_profit = max_drawdown = 0

    # Log final results
    logging.info(f"""
    Final Results:
    Initial Balance: Rs.{initial_balance:,.2f}
    Final Balance: Rs.{balance:,.2f}
    Total Profit/Loss: Rs.{total_profit:,.2f}
    Return: {((balance - initial_balance) / initial_balance) * 100:.2f}%
    Total Trades: {total_trades}
    Win Rate: {win_rate:.2f}%
    Max Drawdown: Rs.{abs(max_drawdown):,.2f}
    """)

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

if __name__ == "__main__":
    try:
        results = run_momentum_strategy(config.DATA_FILE)
    except Exception as e:
        logging.error(f"Error in strategy execution: {str(e)}")