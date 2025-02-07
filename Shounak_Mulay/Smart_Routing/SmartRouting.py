import pandas as pd
import os
from datetime import datetime
from config_SmartRouting import *
import talib

def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Smart_Routing/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_market_data(file_path):
    try:
        data = pd.read_csv(file_path)
        if ENABLE_DEBUG_LOGGING:
            print(f"Data loaded successfully from {file_path}")
        return data
    except FileNotFoundError:
        log_error(f"Error: File not found at {file_path}")
        raise

def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    with open(log_filename, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def calculate_indicators(data):
    # Calculate On-Balance Volume (OBV) for order flow
    data['OBV'] = talib.OBV(data['close'], data['Volume'])
    
    # Calculate Simple Moving Average (SMA) for volume
    data['Volume_MA'] = talib.SMA(data['Volume'], timeperiod=14)
    
    return data

def routing_decision(row, volume_ma):
    volume = row['Volume']
    obv = row['OBV']
    
    # Build reasoning components
    reasoning = []
    
    # Volume analysis
    volume_status = "Above MA" if volume > volume_ma else "Below MA"
    reasoning.append(f"Volume: {volume:,} vs MA: {volume_ma:,} ({volume_status})")
    
    # Order flow (OBV) analysis
    obv_status = "Positive" if obv > 0 else "Negative"
    reasoning.append(f"OBV: {obv:,} ({obv_status})")

    # Combine reasoning
    full_reasoning = " | ".join(reasoning)

    if volume > volume_ma and obv > 0:
        return "Buy", full_reasoning
    return "Hold", full_reasoning

def run_smart_order_routing(data, initial_balance, volume_ma, stop_loss_pct, target_pct):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"smart_routing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss_price = None
    target_price = None
    position_size = 1
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    # Enhanced Trading Initialization Logs
    log_trade(f"===========================================")
    log_trade(f"  Smart Order Routing Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Volume MA Threshold: {volume_ma:,}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Percentage: {target_pct}%")
    log_trade(f"Position Size: {position_size} unit(s)")
    log_trade(f"Debug Logging: {'Enabled' if ENABLE_DEBUG_LOGGING else 'Disabled'}")

    for index, row in data.iterrows():
        current_price = row['close']
        timestamp = pd.Timestamp(row['time']) if 'time' in row else pd.Timestamp.now()
        obv = row['OBV']
        volume_ma_value = row['Volume_MA']
        volume = row['Volume']

        if ENABLE_DEBUG_LOGGING:
            log_trade(f"\nAnalyzing Minute {index + 1}:")
            log_trade(f"Price: {current_price:.2f}")
            log_trade(f"VWAP: {row['VWAP']:.2f}")
            log_trade(f"Volume: {row['Volume']:,}")

        if position is None:
            routing_decision_result, reasoning = routing_decision(row, volume_ma)
            if routing_decision_result == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                trade_entry_reason = reasoning
                stop_loss_price = trade_price * (1 - stop_loss_pct / 100)
                target_price = trade_price * (1 + target_pct / 100)
                
                log_trade(f"\nRouting Buy Order:")
                log_trade(f"Entry Price: {trade_price:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Stop Loss: {stop_loss_price:.2f}")
                log_trade(f"Target: {target_price:.2f}")

        if position == "Buy":
            if current_price <= stop_loss_price or current_price >= target_price:
                profit = (current_price - trade_price) * position_size
                balance += profit
                
                exit_reason = "Stop Loss" if current_price <= stop_loss_price else "Target Profit"
                
                trade_info = {
                    'entry_time': trade_entry_time,
                    'exit_time': timestamp,
                    'type': position,
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'position_size': position_size,
                    'status': exit_reason,
                    'profit': profit,
                    'entry_reasoning': trade_entry_reason
                }
                trades.append(trade_info)

                log_trade(f"\n===========================================")
                log_trade(f"Closed {position} position: {exit_reason}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Entry Time: {trade_entry_time}")
                log_trade(f"Exit Time: {timestamp}")
                log_trade(f"Entry Price: {trade_price:.2f}")
                log_trade(f"Exit Price: {current_price:.2f}")
                log_trade(f"Position Size: {position_size}")
                log_trade(f"Profit/Loss: {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                log_trade(f"===========================================")
                
                position = None
                trade_price = None
                stop_loss_price = None
                target_price = None
                trade_entry_time = None
                trade_entry_reason = None

        if balance <= initial_balance * 0.7:
            log_trade(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    # Enhanced Trading Summary
    log_trade("\n===========================================")
    log_trade(f"  Trading Summary")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {initial_balance:.2f}")
    log_trade(f"Final Balance: {balance:.2f}")
    log_trade(f"Total Profit/Loss: {balance - initial_balance:.2f}")
    log_trade(f"Total Trades: {len(trades)}")

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
            log_trade(f"Type: {trade['type']}")
            log_trade(f"Entry Price: {trade['entry_price']:.2f}")
            log_trade(f"Exit Price: {trade['exit_price']:.2f}")
            log_trade(f"Position Size: {trade['position_size']}")
            log_trade(f"Status: {trade['status']}")
            log_trade(f"Profit/Loss: {trade['profit']:.2f}")
            log_trade(f"Entry Reasoning: {trade['entry_reasoning']}")

        # Performance Metrics
        log_trade(f"\nPerformance Statistics:")
        log_trade(f"Profitable Trades: {len(profit_trades)}")
        log_trade(f"Loss-making Trades: {len(loss_trades)}")
        
        if len(profit_trades) > 0:
            log_trade(f"Average Profit per Winning Trade: {profit_trades['profit'].mean():.2f}")
            log_trade(f"Largest Winning Trade: {profit_trades['profit'].max():.2f}")
        
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per Losing Trade: {loss_trades['profit'].mean():.2f}")
            log_trade(f"Largest Losing Trade: {loss_trades['profit'].min():.2f}")

        # Advanced Metrics
        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")
        
        if len(profit_trades) > 0 and len(loss_trades) > 0:
            profit_factor = abs(profit_trades['profit'].sum() / loss_trades['profit'].sum())
            log_trade(f"Profit Factor: {profit_factor:.2f}")
            
            risk_reward_ratio = (profit_trades['profit'].mean() / abs(loss_trades['profit'].mean())) if len(loss_trades) > 0 else float('inf')
            log_trade(f"Risk-Reward Ratio: {risk_reward_ratio:.2f}")
    
    log_trade("\n===========================================")
    return balance, trades

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), file_path)
    
    try:
        # Load and process data
        data = load_market_data(file_path)
        data = calculate_indicators(data)  # Add this line to calculate indicators
        
        final_balance, trades = run_smart_order_routing(
            data,
            initial_balance=initial_balance,
            volume_ma=volume_ma,
            stop_loss_pct=stop_loss_pct,
            target_pct=target_pct
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")