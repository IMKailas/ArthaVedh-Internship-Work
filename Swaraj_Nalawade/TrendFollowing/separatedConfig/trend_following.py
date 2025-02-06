import pandas as pd
import logging
import talib as ta
from datetime import datetime
import config

def setup_logging():
    """Configure logging settings"""
    log_filename = f"trend_following_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        filename=log_filename
    )
    return log_filename

def enter_position(position_type, price):
    """Handle position entry logic"""
    if position_type == "Long":
        stop_loss = price * (1 - config.STOP_LOSS_PERCENT / 100)
        target_profit = price * (1 + config.TARGET_PROFIT_PERCENT / 100)
    else:  # Short
        stop_loss = price * (1 + config.STOP_LOSS_PERCENT / 100)
        target_profit = price * (1 - config.TARGET_PROFIT_PERCENT / 100)
    
    return position_type, price, stop_loss, target_profit

def exit_position(current_price, trade_price, position_type, reason, balance):
    """Handle position exit logic"""
    profit = (current_price - trade_price if position_type == "Long"
             else trade_price - current_price)
    new_balance = balance + profit
    return new_balance, profit

def check_entry_conditions(row, position):
    """Check if entry conditions are met"""
    if position is not None:
        return False
        
    short_ma = row['short_ma']
    long_ma = row['long_ma']
    
    long_conditions = [
        short_ma > long_ma
    ]
    
    short_conditions = [
        short_ma < long_ma
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

def log_trade_details(message, log_filename):
    """Log trade details to the file and console"""
    with open(log_filename, 'a') as f:
        f.write(message + "\n")
    print(message)

def run_trend_following_strategy():
    """Main strategy execution function"""
    log_filename = setup_logging()
    
    # Load and prepare data
    df = pd.read_csv(config.DATA_PATH)
    
    # Validate required columns
    if not all(col in df.columns for col in config.REQUIRED_COLUMNS):
        raise ValueError(f"CSV must contain the following columns: {', '.join(config.REQUIRED_COLUMNS)}")
    
    # Calculate moving averages using TA-Lib
    df['short_ma'] = ta.SMA(df['close'], config.SHORT_MA_PERIOD)
    df['long_ma'] = ta.SMA(df['close'], config.LONG_MA_PERIOD)
    
    # Initialize trading variables
    balance = config.INITIAL_BALANCE
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_history = []
    
    # Log strategy initialization
    log_trade_details("===========================================", log_filename)
    log_trade_details("  Trend Following Strategy Started", log_filename)
    log_trade_details("===========================================", log_filename)
    log_trade_details(f"Initial Balance: {balance:.2f}", log_filename)
    log_trade_details(f"Stop Loss Percentage: {config.STOP_LOSS_PERCENT}%", log_filename)
    log_trade_details(f"Target Profit Percentage: {config.TARGET_PROFIT_PERCENT}%", log_filename)
    
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
                log_trade_details(f"Opened {position} position at {trade_price:.2f}\nStop Loss: {stop_loss:.2f}, Target: {target_profit:.2f}", log_filename)
        
        # Check for position exit
        else:
            exit_reason = check_exit_conditions(current_row, position, stop_loss, target_profit)
            if exit_reason:
                balance, profit = exit_position(current_row['close'], trade_price, position, exit_reason, balance)
                log_trade_details(f"Closed {position} position: {exit_reason}\nEntry Price: {trade_price:.2f}, Exit Price: {current_row['close']:.2f}\nProfit/Loss: {profit:.2f}\nNew Balance: {balance:.2f}", log_filename)
                
                trade_history.append({
                    "entry_price": trade_price,
                    "exit_price": current_row['close'],
                    "position_type": position,
                    "exit_reason": exit_reason,
                    "profit": profit,
                    "balance": balance
                })
                
                # Reset position
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
        
        # Check stop condition
        if balance <= config.INITIAL_BALANCE * (1 - config.MAX_LOSS_PERCENT / 100):
            log_trade_details(f"Balance dropped below {100 - config.MAX_LOSS_PERCENT}% of initial value. Stopping strategy.", log_filename)
            break
    
    # Create and save trade history
    trades_df = pd.DataFrame(trade_history)
    if len(trades_df) > 0 and config.SAVE_TRADE_HISTORY:
        trades_df.to_csv(f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    # Log summary
    log_trade_details("===========================================", log_filename)
    log_trade_details("  Trading Summary", log_filename)
    log_trade_details("===========================================", log_filename)
    log_trade_details(f"Final Balance: {balance:.2f}", log_filename)
    log_trade_details(f"Total Trades Executed: {len(trade_history)}", log_filename)
    
    for idx, trade in enumerate(trade_history):
        log_trade_details(f"Trade #{idx + 1}:\nEntry Price: {trade['entry_price']:.2f}, Exit Price: {trade['exit_price']:.2f}\nProfit/Loss: {trade['profit']:.2f}\n", log_filename)
    
    return balance, trades_df

if __name__ == "__main__":
    final_balance, trades = run_trend_following_strategy()

















############################## Improved by Deepseek #########################
# # trend_following_strategy.py
# import pandas as pd
# import logging
# import talib as ta
# from datetime import datetime
# import config

# def setup_logging():
#     """Configure logging settings"""
#     log_filename = f"trend_following_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
#     logging.basicConfig(
#         level=getattr(logging, config.LOG_LEVEL),
#         format=config.LOG_FORMAT,
#         filename=log_filename
#     )
#     return log_filename

# def enter_position(position_type, price):
#     """Handle position entry logic"""
#     if position_type == "Long":
#         stop_loss = price * (1 - config.STOP_LOSS_PERCENT / 100)
#         target_profit = price * (1 + config.TARGET_PROFIT_PERCENT / 100)
#     else:  # Short
#         stop_loss = price * (1 + config.STOP_LOSS_PERCENT / 100)
#         target_profit = price * (1 - config.TARGET_PROFIT_PERCENT / 100)
    
#     return position_type, price, stop_loss, target_profit

# def exit_position(current_price, trade_price, position_type, reason, balance):
#     """Handle position exit logic"""
#     profit = (current_price - trade_price if position_type == "Long"
#              else trade_price - current_price)
#     new_balance = balance + profit
#     return new_balance, profit

# def check_entry_conditions(current_row, previous_row, position):
#     """Check if entry conditions are met"""
#     if position is not None or previous_row is None:
#         return None

#     # Check moving average crossover
#     ma_cross_up = (current_row['short_ma'] > current_row['long_ma'] and 
#                   previous_row['short_ma'] <= previous_row['long_ma'])
#     ma_cross_down = (current_row['short_ma'] < current_row['long_ma'] and 
#                     previous_row['short_ma'] >= previous_row['long_ma'])

#     # Initialize conditions
#     long_conditions = [ma_cross_up]
#     short_conditions = [ma_cross_down]

#     # Add VWAP condition if enabled
#     if config.USE_VWAP:
#         long_conditions.append(current_row['close'] > current_row['VWAP'])
#         short_conditions.append(current_row['close'] < current_row['VWAP'])

#     # Add RSI condition if enabled
#     if config.USE_RSI:
#         long_conditions.append(current_row['RSI'] >= config.RSI_BUY_THRESHOLD)
#         short_conditions.append(current_row['RSI'] <= config.RSI_SELL_THRESHOLD)

#     if all(long_conditions):
#         return "Long"
#     elif all(short_conditions):
#         return "Short"
    
#     return None

# def check_exit_conditions(current_row, previous_row, position, stop_loss, target_profit):
#     """Check if exit conditions are met"""
#     if not position:
#         return None
        
#     current_price = current_row['close']
#     exit_reason = None

#     # Check stop loss/target profit
#     if position == "Long":
#         if current_price <= stop_loss:
#             exit_reason = "Stop Loss"
#         elif current_price >= target_profit:
#             exit_reason = "Target Profit"
#     else:  # Short
#         if current_price >= stop_loss:
#             exit_reason = "Stop Loss"
#         elif current_price <= target_profit:
#             exit_reason = "Target Profit"

#     # Check trend reversal using MA crossover
#     if previous_row is not None:
#         ma_reverse_down = (current_row['short_ma'] < current_row['long_ma'] and 
#                           previous_row['short_ma'] >= previous_row['long_ma'])
#         ma_reverse_up = (current_row['short_ma'] > current_row['long_ma'] and 
#                         previous_row['short_ma'] <= previous_row['long_ma'])

#         if position == "Long" and ma_reverse_down:
#             exit_reason = "Trend Reversal"
#         elif position == "Short" and ma_reverse_up:
#             exit_reason = "Trend Reversal"

#     return exit_reason

# def log_trade_details(message, log_filename):
#     """Log trade details to the file and console"""
#     with open(log_filename, 'a') as f:
#         f.write(message + "\n")
#     print(message)

# def run_trend_following_strategy():
#     """Main strategy execution function"""
#     log_filename = setup_logging()
    
#     # Load and prepare data
#     df = pd.read_csv(config.DATA_PATH)
    
#     # Validate required columns
#     if not all(col in df.columns for col in config.REQUIRED_COLUMNS):
#         raise ValueError(f"Missing required columns: {config.REQUIRED_COLUMNS}")

#     # Calculate moving averages using TA-Lib
#     df['short_ma'] = ta.SMA(df['close'], config.SHORT_MA_PERIOD)
#     df['long_ma'] = ta.SMA(df['close'], config.LONG_MA_PERIOD)
    
#     # Initialize trading variables
#     balance = config.INITIAL_BALANCE
#     position = None
#     trade_price = None
#     stop_loss = None
#     target_profit = None
#     trade_history = []
    
#     # Log strategy initialization
#     log_trade_details("\n===========================================", log_filename)
#     log_trade_details("  Trend Following Strategy Started", log_filename)
#     log_trade_details("===========================================", log_filename)
#     log_trade_details(f"Initial Balance: {balance:.2f}", log_filename)
#     log_trade_details(f"Stop Loss Percentage: {config.STOP_LOSS_PERCENT}%", log_filename)
#     log_trade_details(f"Target Profit Percentage: {config.TARGET_PROFIT_PERCENT}%", log_filename)
    
#     # Skip initial rows where moving averages are not available
#     start_index = max(df['short_ma'].isna().sum(), df['long_ma'].isna().sum())
    
#     # Main trading loop
#     for i in range(start_index, len(df)):
#         current_row = df.iloc[i]
#         previous_row = df.iloc[i-1] if i > start_index else None
        
#         # Check for position entry
#         if position is None:
#             entry_signal = check_entry_conditions(current_row, previous_row, position)
#             if entry_signal:
#                 position, trade_price, stop_loss, target_profit = enter_position(
#                     entry_signal, current_row['close']
#                 )
#                 log_trade_details(
#                     f"\n{current_row.name} - Opened {position} position at {trade_price:.2f} "
#                     f"(SL: {stop_loss:.2f}, TP: {target_profit:.2f})", 
#                     log_filename
#                 )
        
#         # Check for position exit
#         else:
#             exit_reason = check_exit_conditions(current_row, previous_row, position, stop_loss, target_profit)
#             if exit_reason:
#                 balance, profit = exit_position(
#                     current_row['close'], 
#                     trade_price, 
#                     position, 
#                     exit_reason, 
#                     balance
#                 )
#                 log_trade_details(
#                     f"\n{current_row.name} - Closed {position} position: {exit_reason} "
#                     f"(Entry: {trade_price:.2f}, Exit: {current_row['close']:.2f}) "
#                     f"Profit/Loss: {profit:.2f} | New Balance: {balance:.2f}", 
#                     log_filename
#                 )
                
#                 trade_history.append({
#                     "timestamp": current_row.name,
#                     "entry_price": trade_price,
#                     "exit_price": current_row['close'],
#                     "position_type": position,
#                     "exit_reason": exit_reason,
#                     "profit": profit,
#                     "balance": balance
#                 })
                
#                 # Reset position
#                 position = None
#                 trade_price = None
#                 stop_loss = None
#                 target_profit = None
        
#         # Check maximum loss condition
#         if balance <= config.INITIAL_BALANCE * (1 - config.MAX_LOSS_PERCENT / 100):
#             log_trade_details(
#                 f"\nMaximum loss threshold reached! Stopping strategy. "
#                 f"Final balance: {balance:.2f}", 
#                 log_filename
#             )
#             break
    
#     # Save trade history
#     if config.SAVE_TRADE_HISTORY and trade_history:
#         trades_df = pd.DataFrame(trade_history)
#         history_filename = f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
#         trades_df.to_csv(history_filename, index=False)
#         log_trade_details(f"\nTrade history saved to {history_filename}", log_filename)
    
#     # Final summary
#     log_trade_details("\n===========================================", log_filename)
#     log_trade_details("  Trading Summary", log_filename)
#     log_trade_details("===========================================", log_filename)
#     log_trade_details(f"Final Balance: {balance:.2f}", log_filename)
#     log_trade_details(f"Total Trades: {len(trade_history)}", log_filename)
#     log_trade_details(f"Total Profit/Loss: {balance - config.INITIAL_BALANCE:.2f}", log_filename)
    
#     return balance, trade_history

# if __name__ == "__main__":
#     final_balance, trades = run_trend_following_strategy()