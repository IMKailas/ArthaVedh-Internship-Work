import pandas as pd
import numpy as np
import logging
from datetime import datetime
import config
import os  # Add this import to handle directory creation
import talib as ta  # Import TA-Lib for technical indicator calculations

def setup_logging():
    """Configure logging with custom format"""
    log_dir = "logs"  # Directory for logs
    os.makedirs(log_dir, exist_ok=True)  # Create the directory if it doesn't exist

    log_file_name = f"momentum_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.FileHandler(f"{log_dir}/{log_file_name}"),  # Save logs in the 'logs' directory
            logging.StreamHandler()  # Output logs to the console
        ]
    )

def calculate_technical_indicators(df):
    """Calculate technical indicators for momentum investing using TA-Lib"""
    # EMA calculations using TA-Lib
    df['EMA9'] = ta.EMA(df['close'], timeperiod=config.EMA_PERIODS['fast'])
    df['EMA21'] = ta.EMA(df['close'], timeperiod=config.EMA_PERIODS['medium'])
    df['EMA50'] = ta.EMA(df['close'], timeperiod=config.EMA_PERIODS['slow'])

    # RSI calculation using TA-Lib
    df['RSI'] = ta.RSI(df['close'], timeperiod=config.RSI_PERIOD)

    # Bollinger Bands calculation using TA-Lib
    df['BB_middle'], df['Upper BB'], df['Lower BB'] = ta.BBANDS(df['close'], timeperiod=config.BOLLINGER_PERIOD, nbdevup=config.BOLLINGER_STD, nbdevdn=config.BOLLINGER_STD, matype=0)

    return df

def identify_investing_signals(df):
    """Identify momentum investing signals based on configured conditions"""
    signals = pd.DataFrame(index=df.index)

    signals['ema_alignment'] = (df['EMA9'] > df['EMA21']) & (df['EMA21'] > df['EMA50'])
    signals['rsi_bullish'] = (df['RSI'] > config.RSI_OVERSOLD) & (df['RSI'] < config.RSI_OVERBOUGHT)
    signals['price_above_bb_middle'] = df['close'] > df['BB_middle']

    buy_signal = (
        signals['ema_alignment'] &
        signals['rsi_bullish'] &
        signals['price_above_bb_middle']
    )

    return buy_signal

def log_trade(action, price, time, reason=None, profit=None, balance=None):
    """Log trade details"""
    if action == "BUY":
        log_msg = (
            f"[{time}] BUY ORDER EXECUTED\n"
            f"Price: {price:.2f}\n"
            f"Current Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    else:  # SELL
        log_msg = (
            f"[{time}] SELL ORDER EXECUTED\n"
            f"Price: {price:.2f}\n"
            f"Reason: {reason}\n"
            f"Profit/Loss: {profit:.2f}\n"
            f"New Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    logging.info(log_msg)

def print_investing_summary(trades_df, initial_balance, final_balance):
    """Print detailed investing summary"""
    if len(trades_df) == 0:
        print("\nNo trades were executed during this period.")
        return

    # Calculate statistics
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    loss_trades = len(trades_df[trades_df['profit'] <= 0])
    win_rate = (profitable_trades / total_trades) * 100
    total_profit = trades_df['profit'].sum()
    avg_profit = trades_df['profit'].mean()
    max_profit = trades_df['profit'].max()
    max_loss = trades_df['profit'].min()

    # Print formatted summary
    print("\n" + "="*60)
    print(f"{'INVESTING SUMMARY':^60}")
    print("="*60)

    print("\nPERFORMANCE METRICS")
    print("-"*60)
    print(f"Initial Balance:      ${initial_balance:,.2f}")
    print(f"Final Balance:        ${final_balance:,.2f}")
    print(f"Total Profit/Loss:    ${total_profit:,.2f}")
    print(f"Return on Investment: {((final_balance - initial_balance) / initial_balance * 100):,.2f}%")

    print("\nTRADE STATISTICS")
    print("-"*60)
    print(f"Total Trades:         {total_trades}")
    print(f"Profitable Trades:    {profitable_trades}")
    print(f"Loss-Making Trades:   {loss_trades}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Average Profit:      ${avg_profit:.2f}")
    print(f"Maximum Profit:      ${max_profit:.2f}")
    print(f"Maximum Loss:        ${max_loss:.2f}")

def run_momentum_investing():
    """Execute the momentum investing strategy"""
    setup_logging()

    # Load and prepare data
    df = pd.read_csv(config.DATA_PATH)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    df = df.sort_values('time')

    # Calculate indicators
    df = calculate_technical_indicators(df)

    # Initialize investing variables
    balance = config.INITIAL_BALANCE
    position = None
    entry_price = None
    trade_history = []

    # Get investing signals
    buy_signals = identify_investing_signals(df)

    # Main investing loop
    for i in range(config.MIN_LOOKBACK, len(df)):
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]

        if position is None:
            if buy_signals.iloc[i]:
                position = "INVESTED"
                entry_price = current_price
                log_trade("BUY", current_price, current_time, balance=balance)

        elif position == "INVESTED":
            profit = current_price - entry_price
            stop_loss = entry_price * (1 - config.STOP_LOSS_PERCENT/100)
            target = entry_price * (1 + config.TARGET_PROFIT_PERCENT/100)

            if current_price <= stop_loss:
                log_trade("SELL", current_price, current_time, "Stop Loss", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "SELL", "profit": profit, "reason": "Stop Loss"})

            elif current_price >= target:
                log_trade("SELL", current_price, current_time, "Target Reached", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "SELL", "profit": profit, "reason": "Target"})

    # Convert trade history to DataFrame for summary
    trades_df = pd.DataFrame(trade_history)

    # Print investing summary
    print_investing_summary(trades_df, config.INITIAL_BALANCE, balance)

    # Save trade history to a CSV for further analysis
    trades_df.to_csv(f"investing_history_{datetime.now().strftime('%Y%m%d')}.csv", index=False)

if __name__ == "__main__":
    run_momentum_investing()
