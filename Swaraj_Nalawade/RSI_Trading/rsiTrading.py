import pandas as pd
import numpy as np
import logging
from datetime import datetime
from config import *  # Import all the config parameters

def setup_logging():
    """Configure logging with custom format showing trade timestamps."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename=LOG_FILE_PATH
    )

def identify_rsi_signals(df):
    """Enhanced signal identification with stricter conditions."""
    # RSI Conditions
    rsi_oversold = df['RSI'] <= RSI_OVERSOLD
    rsi_overbought = df['RSI'] >= RSI_OVERBOUGHT

    # Additional Confirmation (MACD)
    macd_bullish = df['MACD'] > df['Signal']
    macd_bearish = df['MACD'] < df['Signal']

    bullish_signal = rsi_oversold & macd_bullish
    bearish_signal = rsi_overbought & macd_bearish

    return bullish_signal, bearish_signal

def log_trade(trade_type, action, price, time, reason=None, profit=None, balance=None, position_size=None):
    """Enhanced trade logging with detailed information."""
    if action == "ENTRY":
        log_msg = (
            f"[{time}] {trade_type} ENTRY\n"
            f"Price: {price:.2f}, Position Size: {position_size:.2f}\n"
            f"Current Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    else:  # EXIT
        log_msg = (
            f"[{time}] {trade_type} EXIT\n"
            f"Price: {price:.2f}, Profit/Loss: {profit:.2f}\n"
            f"Reason: {reason}\n"
            f"New Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    logging.info(log_msg)

def save_trade_log(trade_history, output_path="trade_log.csv"):
    """Save trade history to a CSV file."""
    trades_df = pd.DataFrame(trade_history)
    trades_df.to_csv(output_path, index=False)
    print(f"Trade log saved to {output_path}")

def run_rsi_strategy(data_path=CSV_FILE_PATH, initial_balance=INITIAL_BALANCE, stop_loss_pct=STOP_LOSS_PERCENT, 
                     target_profit_pct=TARGET_PROFIT_PERCENT, risk_per_trade=RISK_PER_TRADE, 
                     transaction_cost_pct=TRANSACTION_COST_PERCENT):
    # Load and prepare data
    df = pd.read_csv(data_path, parse_dates=['time'])
    df = df.sort_values('time')

    # Setup logging
    setup_logging()

    # Trading variables
    balance = initial_balance
    position = None
    entry_price = None
    trade_history = []
    cooling_period = COOLDOWN_PERIODS  # Minimum periods between trades
    last_trade_index = -cooling_period

    # Get signals
    bullish_signals, bearish_signals = identify_rsi_signals(df)

    # Main trading loop
    for i in range(50, len(df)):
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]

        # Skip if within cooling period
        if i - last_trade_index < cooling_period:
            continue

        # Position entry logic
        if position is None:
            if bullish_signals.iloc[i]:
                position = "LONG"
                entry_price = current_price
                position_size = balance * risk_per_trade / current_price
                log_trade("LONG", "ENTRY", current_price, current_time, balance=balance, position_size=position_size)
                last_trade_index = i

            elif bearish_signals.iloc[i]:
                position = "SHORT"
                entry_price = current_price
                position_size = balance * risk_per_trade / current_price
                log_trade("SHORT", "ENTRY", current_price, current_time, balance=balance, position_size=position_size)
                last_trade_index = i

        # Position exit logic
        elif position == "LONG":
            profit = (current_price - entry_price) * position_size
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            target = entry_price * (1 + target_profit_pct / 100)

            if current_price <= stop_loss or current_price >= target or bearish_signals.iloc[i]:
                profit -= profit * transaction_cost_pct / 100  # Subtract transaction cost
                balance += profit
                trade_history.append({
                    "type": "LONG",
                    "action": "EXIT",
                    "price": current_price,
                    "time": current_time,
                    "profit": profit,
                    "reason": "Stop Loss" if current_price <= stop_loss else 
                              "Target Reached" if current_price >= target else 
                              "Signal Reversal",
                    "balance": balance
                })
                log_trade("LONG", "EXIT", current_price, current_time, reason=trade_history[-1]['reason'], profit=profit, balance=balance)
                position = None

        elif position == "SHORT":
            profit = (entry_price - current_price) * position_size
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            target = entry_price * (1 - target_profit_pct / 100)

            if current_price >= stop_loss or current_price <= target or bullish_signals.iloc[i]:
                profit -= profit * transaction_cost_pct / 100  # Subtract transaction cost
                balance += profit
                trade_history.append({
                    "type": "SHORT",
                    "action": "EXIT",
                    "price": current_price,
                    "time": current_time,
                    "profit": profit,
                    "reason": "Stop Loss" if current_price >= stop_loss else 
                              "Target Reached" if current_price <= target else 
                              "Signal Reversal",
                    "balance": balance
                })
                log_trade("SHORT", "EXIT", current_price, current_time, reason=trade_history[-1]['reason'], profit=profit, balance=balance)
                position = None

    # Save trade history
    if SAVE_TRADE_HISTORY:
        save_trade_log(trade_history)

    # Print trading summary
    print(f"\nInitial Balance: {initial_balance:.2f}")
    print(f"Total Trades: {len(trade_history)}")
    print(f"Final Balance: {balance:.2f}")

    return balance, trade_history

if __name__ == "__main__":
    final_balance, trades = run_rsi_strategy()
