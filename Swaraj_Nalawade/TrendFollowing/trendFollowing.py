# trend_strategy.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import config

def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        filename=f"trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

def calculate_moving_average(prices, period):
    """Calculate moving average for given prices and period"""
    return prices.rolling(window=period).mean()

def enter_position(position_type, price):
    """Handle position entry logic"""
    if position_type == "Long":
        stop_loss = price * (1 - config.STOP_LOSS_PERCENT / 100)
        target_profit = price * (1 + config.TARGET_PROFIT_PERCENT / 100)
    else:  # Short
        stop_loss = price * (1 + config.STOP_LOSS_PERCENT / 100)
        target_profit = price * (1 - config.TARGET_PROFIT_PERCENT / 100)
    
    logging.info(f"Entering {position_type} position at {price:.2f}, Stop Loss: {stop_loss:.2f}, Target: {target_profit:.2f}")
    return position_type, price, stop_loss, target_profit

def exit_position(current_price, trade_price, position_type, reason, balance):
    """Handle position exit logic"""
    profit = (current_price - trade_price if position_type == "Long"
             else trade_price - current_price)
    new_balance = balance + profit
    logging.info(f"Exiting {position_type} at {current_price:.2f}, Reason: {reason}, Profit: {profit:.2f}, New Balance: {new_balance:.2f}")
    return new_balance

def check_entry_conditions(row, position):
    """Check if entry conditions are met"""
    if position is not None:
        return False
        
    short_ma = row['short_ma']
    long_ma = row['long_ma']
    current_price = row['close']
    vwap = row['VWAP']
    rsi = row['RSI']
    
    long_conditions = [
        short_ma > long_ma,
        not config.USE_VWAP or current_price > vwap,
        not config.USE_RSI or rsi > config.RSI_BUY_THRESHOLD
    ]
    
    short_conditions = [
        short_ma < long_ma,
        not config.USE_VWAP or current_price < vwap,
        not config.USE_RSI or rsi < config.RSI_SELL_THRESHOLD
    ]
    
    if all(long_conditions):
        return "Long"
    elif all(short_conditions):
        return "Short"
    
    return None

def check_exit_conditions(row, position, stop_loss, target_profit):
    """Check if exit conditions are met"""
    if not position:
        return None
        
    current_price = row['close']
    short_ma = row['short_ma']
    long_ma = row['long_ma']
    
    if position == "Long":
        if current_price <= stop_loss:
            return "Stop Loss"
        elif current_price >= target_profit:
            return "Target Profit"
        elif short_ma < long_ma:
            return "Trend Reversal"
            
    elif position == "Short":
        if current_price >= stop_loss:
            return "Stop Loss"
        elif current_price <= target_profit:
            return "Target Profit"
        elif short_ma > long_ma:
            return "Trend Reversal"
    
    return None

def run_trend_following_strategy():
    """Main strategy execution function"""
    setup_logging()
    
    # Load and prepare data
    df = pd.read_csv(config.DATA_PATH)
    
    # Validate required columns
    if not all(col in df.columns for col in config.REQUIRED_COLUMNS):
        raise ValueError(f"CSV must contain the following columns: {', '.join(config.REQUIRED_COLUMNS)}")
    
    # Calculate moving averages
    df['short_ma'] = calculate_moving_average(df['close'], config.SHORT_MA_PERIOD)
    df['long_ma'] = calculate_moving_average(df['close'], config.LONG_MA_PERIOD)
    
    # Initialize trading variables
    balance = config.INITIAL_BALANCE
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_history = []
    
    # Skip initial rows where moving averages are not available
    start_index = max(df['short_ma'].isna().sum(), df['long_ma'].isna().sum())
    
    # Main trading loop
    for i in range(start_index, len(df)):
        current_row = df.iloc[i]
        
        # Check for position entry
        if position is None:
            entry_signal = check_entry_conditions(current_row, position)
            if entry_signal:
                position, trade_price, stop_loss, target_profit = enter_position(
                    entry_signal, current_row['close']
                )
        
        # Check for position exit
        else:
            exit_reason = check_exit_conditions(current_row, position, stop_loss, target_profit)
            if exit_reason:
                # Record trade
                trade_history.append({
                    "entry_price": trade_price,
                    "exit_price": current_row['close'],
                    "position_type": position,
                    "exit_reason": exit_reason,
                    "profit": current_row['close'] - trade_price if position == "Long" else trade_price - current_row['close'],
                    "balance": balance
                })
                
                # Update balance and reset position
                balance = exit_position(current_row['close'], trade_price, position, exit_reason, balance)
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
        
        # Check stop condition
        if balance <= config.INITIAL_BALANCE * (1 - config.MAX_LOSS_PERCENT / 100):
            logging.warning(f"Balance dropped below {100 - config.MAX_LOSS_PERCENT}% of initial value. Stopping strategy.")
            break
    
    # Create and save trade history
    trades_df = pd.DataFrame(trade_history)
    if len(trades_df) > 0 and config.SAVE_TRADE_HISTORY:
        log_trading_summary(trades_df, balance)
        trades_df.to_csv(f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    else:
        logging.info("No trades were executed during the backtest period.")
    
    return balance, trades_df

def log_trading_summary(trades_df, final_balance):
    """Log summary statistics of trading session"""
    summary_stats = {
        "Total Trades": len(trades_df),
        "Profitable Trades": len(trades_df[trades_df['profit'] > 0]),
        "Loss-Making Trades": len(trades_df[trades_df['profit'] < 0]),
        "Total Profit/Loss": trades_df['profit'].sum(),
        "Win Rate": len(trades_df[trades_df['profit'] > 0]) / len(trades_df) * 100,
        "Final Balance": final_balance,
        "Return": (final_balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE * 100
    }
    
    logging.info("\nStrategy Summary:")
    for key, value in summary_stats.items():
        logging.info(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")

if __name__ == "__main__":
    final_balance, trades = run_trend_following_strategy()
