import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    filename=f"trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

def calculate_moving_average(prices, period):
    return prices.rolling(window=period).mean()

def enter_position(position_type, price, stop_loss_pct, target_profit_pct):
    if position_type == "Long":
        stop_loss = price * (1 - stop_loss_pct / 100)
        target_profit = price * (1 + target_profit_pct / 100)
    else:  # Short
        stop_loss = price * (1 + stop_loss_pct / 100)
        target_profit = price * (1 - target_profit_pct / 100)
    
    logging.info(f"Entering {position_type} position at {price:.2f}, Stop Loss: {stop_loss:.2f}, Target: {target_profit:.2f}")
    return position_type, price, stop_loss, target_profit

def exit_position(current_price, trade_price, position_type, reason, balance):
    profit = (current_price - trade_price if position_type == "Long"
             else trade_price - current_price)
    new_balance = balance + profit
    logging.info(f"Exiting {position_type} at {current_price:.2f}, Reason: {reason}, Profit: {profit:.2f}, New Balance: {new_balance:.2f}")
    return new_balance

def run_trend_following_strategy(data_path, initial_balance, stop_loss_pct, target_profit_pct):
    # Load and prepare data
    df = pd.read_csv(data_path)
    
    # Ensure necessary columns are present
    required_columns = ['close', 'VWAP', 'RSI', 'Upper Bollinger Band', 'Lower Bollinger Band']
    if not all(col in df.columns for col in required_columns):
        raise ValueError(f"CSV must contain the following columns: {', '.join(required_columns)}")
    
    # Calculate moving averages
    df['short_ma'] = calculate_moving_average(df['close'], 5)
    df['long_ma'] = calculate_moving_average(df['close'], 15)
    
    # Initialize trading variables
    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_history = []
    
    # Skip initial rows where moving averages are not available
    start_index = max(df['short_ma'].isna().sum(), df['long_ma'].isna().sum())
    
    # Main trading loop
    for i in range(start_index, len(df)):
        current_price = df['close'].iloc[i]
        short_ma = df['short_ma'].iloc[i]
        long_ma = df['long_ma'].iloc[i]
        vwap = df['VWAP'].iloc[i]
        rsi = df['RSI'].iloc[i]
        
        # Check for position entry
        if position is None:
            if short_ma > long_ma and current_price > vwap and rsi > 50:
                position, trade_price, stop_loss, target_profit = enter_position(
                    "Long", current_price, stop_loss_pct, target_profit_pct
                )
            elif short_ma < long_ma and current_price < vwap and rsi < 50:
                position, trade_price, stop_loss, target_profit = enter_position(
                    "Short", current_price, stop_loss_pct, target_profit_pct
                )
        
        # Check for position exit
        elif position:
            exit_reason = None
            
            if (position == "Long" and current_price <= stop_loss) or \
               (position == "Short" and current_price >= stop_loss):
                exit_reason = "Stop Loss"
            elif (position == "Long" and current_price >= target_profit) or \
                 (position == "Short" and current_price <= target_profit):
                exit_reason = "Target Profit"
            elif (position == "Long" and short_ma < long_ma) or \
                 (position == "Short" and short_ma > long_ma):
                exit_reason = "Trend Reversal"
                
            if exit_reason:
                # Record trade before updating balance
                trade_history.append({
                    "entry_price": trade_price,
                    "exit_price": current_price,
                    "position_type": position,
                    "exit_reason": exit_reason,
                    "profit": current_price - trade_price if position == "Long" else trade_price - current_price,
                    "balance": balance
                })
                
                # Update balance and reset position
                balance = exit_position(current_price, trade_price, position, exit_reason, balance)
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
        
        # Check stop condition
        if balance <= initial_balance * 0.7:
            logging.warning(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break
    
    # Create summary DataFrame
    trades_df = pd.DataFrame(trade_history)
    
    # Calculate and log summary statistics
    if len(trades_df) > 0:
        summary_stats = {
            "Total Trades": len(trades_df),
            "Profitable Trades": len(trades_df[trades_df['profit'] > 0]),
            "Loss-Making Trades": len(trades_df[trades_df['profit'] < 0]),
            "Total Profit/Loss": trades_df['profit'].sum(),
            "Win Rate": len(trades_df[trades_df['profit'] > 0]) / len(trades_df) * 100,
            "Final Balance": balance,
            "Return": (balance - initial_balance) / initial_balance * 100
        }
        
        logging.info("\nStrategy Summary:")
        for key, value in summary_stats.items():
            logging.info(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        
        # Save trade history to CSV
        trades_df.to_csv(f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    else:
        logging.info("No trades were executed during the backtest period.")
    
    return balance, trades_df

if __name__ == "__main__":
    # Strategy parameters
    DATA_PATH = r"C:\assignement\sem5\Internship\scalping\loadData.csv"  # Replace with your CSV file path
    INITIAL_BALANCE = 10000
    STOP_LOSS_PCT = 1.0
    TARGET_PROFIT_PCT = 2.0
    
    # Run the strategy
    final_balance, trades = run_trend_following_strategy(
        DATA_PATH,
        INITIAL_BALANCE,
        STOP_LOSS_PCT,
        TARGET_PROFIT_PCT
    )
