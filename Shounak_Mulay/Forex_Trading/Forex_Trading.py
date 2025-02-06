import pandas as pd
import time
import os
from datetime import datetime
import config_ForexTrading
import talib
# Function to create log directory if it doesn't exist
def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Forex_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# Load CSV data
def load_market_data(file_path):
    """Load and preprocess the CSV data"""
    try:
        data = pd.read_csv(file_path)
        if config_ForexTrading.ENABLE_DEBUG_LOGGING:
            print(f"Data loaded successfully from {file_path}")
        data['RSI'] = talib.RSI(data['close'])
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        log_error(f"Error: File not found at {file_path}")
        raise

# Log Errors to File
def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    with open(log_filename, 'a') as f:
        f.write(f"{message}\n")

# Enhanced forex trading decision with reasoning
def forex_trading_decision(row, position, entry_made):
    volume = row["Volume"]
    rsi = row["RSI"]
    price = row["close"]
    min_volume = config_ForexTrading.minimum_volume_threshold
    
    # Build reasoning components
    reasoning = []
    
    # Volume analysis
    volume_status = "Sufficient" if volume >= min_volume else "Insufficient"
    reasoning.append(f"Volume: {volume:,} ({volume_status})")
    
    # RSI analysis
    rsi_status = "Oversold" if rsi < config_ForexTrading.rsi else "Normal"
    reasoning.append(f"RSI: {rsi:.2f} ({rsi_status})")
    
    # Price information
    reasoning.append(f"Price: {price:.2f}")
    
    # Position status
    position_status = "No Position" if position is None else position
    entry_status = "No Prior Entry" if not entry_made else "Entry Made"
    reasoning.append(f"Position: {position_status} | {entry_status}")

    # Combine reasoning
    full_reasoning = " | ".join(reasoning)

    if config_ForexTrading.ENABLE_DEBUG_LOGGING:
        print(f"\nAnalyzing conditions:")
        print(full_reasoning)

    if position is None and not entry_made and volume >= min_volume:
        if rsi < config_ForexTrading.rsi:
            return "Buy", full_reasoning

    return "Hold", full_reasoning

def run_forex_trading_strategy(csv_file, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    # Create log file
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"forex_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    entry_made = False
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    log_trade(f"===========================================")
    log_trade(f"  Forex Trading Strategy  ")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    log_trade(f"Minimum Volume Threshold: {config_ForexTrading.minimum_volume_threshold:,}")
    log_trade(f"RSI Threshold: {config_ForexTrading.rsi}")

    for index, row in data.iterrows():
        price = row["close"]
        timestamp = row.name if isinstance(row.name, pd.Timestamp) else pd.Timestamp(row['time'])
        current_price = price

        # Check for new entry
        if position is None:
            decision, reasoning = forex_trading_decision(row, position, entry_made)

            if decision == "Buy":
                position = "Buy"
                trade_price = price
                trade_entry_time = timestamp
                trade_entry_reason = reasoning
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")
                entry_made = True

        # Check exit conditions if in position
        if position:
            current_price = price

            if position == "Buy":
                if current_price <= stop_loss or current_price >= target_profit:
                    # Calculate profit/loss
                    profit = current_price - trade_price
                    balance += profit
                    
                    # Determine exit reason
                    exit_reason = "Stop Loss" if current_price <= stop_loss else "Target Profit"
                    
                    # Log trade details
                    trade_info = {
                        'entry_time': trade_entry_time,
                        'exit_time': timestamp,
                        'type': position,
                        'entry_price': trade_price,
                        'exit_price': current_price,
                        'status': exit_reason,
                        'profit': profit,
                        'entry_reasoning': trade_entry_reason
                    }
                    trades.append(trade_info)
                    
                    log_trade(f"\n===========================================")
                    log_trade(f"Closed {position} position: {exit_reason}")
                    log_trade(f"Entry Reasoning: {trade_entry_reason}")
                    log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {current_price:.2f}")
                    log_trade(f"Profit/Loss: {profit:.2f}")
                    log_trade(f"New Balance: {balance:.2f}")
                    log_trade(f"Exit Time: {timestamp}")
                    log_trade(f"===========================================")
                    
                    # Reset position
                    position = None
                    trade_price = None
                    entry_made = False
                    trade_entry_time = None
                    trade_entry_reason = None

            if balance <= initial_balance * 0.7:
                log_trade(f"Balance dropped below 70% of initial value. Stopping strategy.")
                break

    # Close any remaining position at the end
    if position is not None:
        final_price = data.iloc[-1]['close']
        profit = final_price - trade_price
        balance += profit
        trades.append({
            'entry_time': trade_entry_time,
            'exit_time': timestamp,
            'type': position,
            'entry_price': trade_price,
            'exit_price': final_price,
            'status': 'Market Close',
            'profit': profit,
            'entry_reasoning': trade_entry_reason
        })
        log_trade(f"\n===========================================")
        log_trade(f"Closed remaining position at market close.")
        log_trade(f"Entry Reasoning: {trade_entry_reason}")
        log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {final_price:.2f}")
        log_trade(f"Profit/Loss: {profit:.2f}")
        log_trade(f"New Balance: {balance:.2f}")
        log_trade(f"===========================================")

    # Enhanced Trading Summary
    log_trade("\n===========================================")
    log_trade(f"  Trading Summary")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {initial_balance:.2f}")
    log_trade(f"Final Balance: {balance:.2f}")
    log_trade(f"Total Profit/Loss: {balance - initial_balance:.2f}")
    log_trade(f"Total Trades Executed: {len(trades)}")

    if len(trades) > 0:
        trades_df = pd.DataFrame(trades)
        trades_df['profit'] = trades_df['profit'].astype(float)
        profit_trades = trades_df[trades_df['profit'] > 0]
        loss_trades = trades_df[trades_df['profit'] < 0]

        # Detailed Trade Analysis
        log_trade(f"\nDetailed Trade Analysis:")
        for i, trade in enumerate(trades, 1):
            log_trade(f"\nTrade #{i}:")
            log_trade(f"Entry Time: {trade['entry_time']}")
            log_trade(f"Exit Time: {trade['exit_time']}")
            log_trade(f"Entry Price: {trade['entry_price']:.2f}")
            log_trade(f"Exit Price: {trade['exit_price']:.2f}")
            log_trade(f"Status: {trade['status']}")
            log_trade(f"Profit/Loss: {trade['profit']:.2f}")
            log_trade(f"Entry Reasoning: {trade['entry_reasoning']}")

        log_trade(f"\nProfit/Loss Statistics:")
        log_trade(f"Profitable Trades: {len(profit_trades)}")
        log_trade(f"Loss-making Trades: {len(loss_trades)}")
        if len(profit_trades) > 0:
            log_trade(f"Average Profit per winning trade: {profit_trades['profit'].mean():.2f}")
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per losing trade: {loss_trades['profit'].mean():.2f}")

        # Calculate win rate
        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")

    return balance, trades

# Main execution
if __name__ == "__main__":
    csv_file = os.path.join(os.getcwd(), './Forex_Trading/NSE_NIFTY, 1 Intraday.csv')
    data = load_market_data(csv_file)
    # data['RSI'] = talib.RSI(data['close'])
    initial_balance = config_ForexTrading.initial_balance
    leverage = config_ForexTrading.leverage
    stop_loss_pct = config_ForexTrading.stop_loss_pct
    target_profit_pct = config_ForexTrading.target_profit_pct

    try:
        final_balance, trades = run_forex_trading_strategy(csv_file, initial_balance, leverage, stop_loss_pct, target_profit_pct)
    except FileNotFoundError:
        print(f"File not found: {csv_file}")