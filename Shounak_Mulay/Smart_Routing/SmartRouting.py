import pandas as pd
import os
from datetime import datetime
from config_SmartRouting import *  # Import configuration from config.py

# Function to create log directory if it doesn't exist
def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Smart_Routing/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# Load CSV data
def load_market_data(file_path):
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        log_error(f"Error: File not found at {file_path}")
        raise

# Log Errors to File
def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    with open(log_filename, 'a') as f:
        f.write(f"{message}\n")

# Smart order routing decision logic based on volume and VWAP
def routing_decision(row, volume_ma):
    volume = row['Volume']
    vwap = row['VWAP']

    # Routing decision based on volume and price (VWAP)
    if volume > volume_ma and row['close'] < vwap:  # Bullish signal based on volume and price below VWAP
        return "Buy_Route"  # Route to high-liquidity exchange for buying
    return "Hold"  # No strong routing preference based on current conditions

def run_smart_order_routing(data, initial_balance, volume_ma, stop_loss_pct, target_pct):
    # Create log directory and file
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"smart_routing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss_price = None
    target_price = None
    position_size = 1

    # Summary variables (preserving existing tracking)
    trades = []
    total_profit = 0
    total_loss = 0
    successful_trades = 0
    failed_trades = 0

    # Trading Initialization Logs
    log_trade(f"===========================================")
    log_trade(f"  Smart Order Routing Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Volume MA Threshold: {volume_ma}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Percentage: {target_pct}%")
    log_trade(f"Position Size: {position_size} unit(s)")

    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        vwap = row['VWAP']

        # Log market conditions
        print(f"\nMinute {index + 1}:")
        print(f"Price: {current_price:.2f}, VWAP: {vwap:.2f}, Volume: {volume}")

        if position is None:
            routing_decision_result = routing_decision(row, volume_ma)
            if routing_decision_result == "Buy_Route":
                position = "Buy"
                trade_price = current_price
                stop_loss_price = trade_price * (1 - stop_loss_pct / 100)
                target_price = trade_price * (1 + target_pct / 100)
                
                log_trade(f"\nRouting Buy Order:")
                log_trade(f"Entry Price: {trade_price:.2f}")
                log_trade(f"VWAP Benchmark: {vwap:.2f}")
                log_trade(f"Stop Loss: {stop_loss_price:.2f}")
                log_trade(f"Target: {target_price:.2f}")

        if position == "Buy":
            if current_price <= stop_loss_price:
                loss = trade_price - current_price
                balance -= position_size * loss
                total_loss += loss
                failed_trades += 1
                
                log_trade(f"\n===========================================")
                log_trade(f"Stop Loss Hit:")
                log_trade(f"Entry Price: {trade_price:.2f}")
                log_trade(f"Exit Price: {current_price:.2f}")
                log_trade(f"Loss: {loss:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                
                trades.append({
                    "Entry Price": trade_price,
                    "Exit Price": current_price,
                    "PnL": -loss,
                    "Reason": "Stop Loss"
                })
                position = None
                
            elif current_price >= target_price:
                profit = current_price - trade_price
                balance += position_size * profit
                total_profit += profit
                successful_trades += 1
                
                log_trade(f"\n===========================================")
                log_trade(f"Target Profit Hit:")
                log_trade(f"Entry Price: {trade_price:.2f}")
                log_trade(f"Exit Price: {current_price:.2f}")
                log_trade(f"Profit: {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                
                trades.append({
                    "Entry Price": trade_price,
                    "Exit Price": current_price,
                    "PnL": profit,
                    "Reason": "Target Profit"
                })
                position = None

        if balance <= initial_balance * 0.7:
            log_trade(f"\nBalance dropped below 70% of initial value. Stopping strategy.")
            break

    # Generate comprehensive trading summary
    log_trade("\n===========================================")
    log_trade(f"  Trading Summary")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {initial_balance:.2f}")
    log_trade(f"Final Balance: {balance:.2f}")
    log_trade(f"Total Trades: {len(trades)}")
    log_trade(f"Successful Trades: {successful_trades}")
    log_trade(f"Failed Trades: {failed_trades}")
    log_trade(f"Total Profit: {total_profit:.2f}")
    log_trade(f"Total Loss: {total_loss:.2f}")
    log_trade(f"Net Profit/Loss: {total_profit - total_loss:.2f}")
    
    if len(trades) > 0:
        win_rate = (successful_trades / len(trades)) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")
        
        if total_loss != 0:
            profit_factor = total_profit / abs(total_loss)
            log_trade(f"Profit Factor: {profit_factor:.2f}")
        
        avg_profit = total_profit / successful_trades if successful_trades > 0 else 0
        avg_loss = total_loss / failed_trades if failed_trades > 0 else 0
        log_trade(f"Average Profit per Winning Trade: {avg_profit:.2f}")
        log_trade(f"Average Loss per Losing Trade: {avg_loss:.2f}")

    # Detailed trade breakdown
    log_trade("\n--- Trade Details ---")
    for i, trade in enumerate(trades, 1):
        log_trade(f"Trade {i}: Entry={trade['Entry Price']:.2f}, Exit={trade['Exit Price']:.2f}, "
                 f"PnL={trade['PnL']:.2f}, Reason={trade['Reason']}")

    log_trade("\n===========================================")
    return balance, trades

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), file_path)
    
    try:
        data = load_market_data(file_path)
        final_balance, trades = run_smart_order_routing(
            data,
            initial_balance=initial_balance,
            volume_ma=volume_ma,
            stop_loss_pct=stop_loss_pct,
            target_pct=target_pct
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")