import pandas as pd
import os
from datetime import datetime
import config_OrderFlow
import talib

# Function to create log directory if it doesn't exist
def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Order_Flow_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# Load CSV data
def load_market_data(file_path):
    try:
        data = pd.read_csv(file_path)
        if config_OrderFlow.ENABLE_DEBUG_LOGGING:
            print(f"Data loaded successfully from {file_path}")
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

# Calculate TA-Lib indicators
def calculate_indicators(data):
    # Calculate On-Balance Volume (OBV) for order flow
    data['OBV'] = talib.OBV(data['close'], data['Volume'])
    
    # Calculate Simple Moving Average (SMA) for volume
    data['Volume_MA'] = talib.SMA(data['Volume'], timeperiod=14)
    
    return data

# Enhanced order flow decision logic with reasoning
def order_flow_decision(row, volume_ma):
    volume = row['Volume']
    price = row['close']
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

def run_order_flow_strategy(data, initial_balance, stop_loss_pct, target_profit_pct):
    # Create log directory and file
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"orderflow_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    # Trading Initialization Logs
    log_trade(f"===========================================")
    log_trade(f"  Order Flow Trading Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    data = calculate_indicators(data)

    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        obv = row['OBV']
        volume_ma_value = row['Volume_MA']
        timestamp = pd.Timestamp(row['time'])

        if position is None:
            decision, reasoning = order_flow_decision(row, volume_ma_value)

            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                trade_entry_reason = reasoning
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")
                log_trade(f"OBV: {obv:,}, Volume: {volume:,}")

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
                    'entry_obv': obv,
                    'entry_volume': volume,
                    'entry_reasoning': trade_entry_reason
                }
                trades.append(trade_info)

                log_trade(f"\n===========================================")
                log_trade(f"Closed {position} position: {exit_reason}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {current_price:.2f}")
                log_trade(f"OBV at Entry: {obv:,}")
                log_trade(f"Volume at Entry: {volume:,}")
                log_trade(f"Profit/Loss: {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                log_trade(f"Exit Time: {timestamp}")
                log_trade(f"===========================================")
                
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
                trade_entry_time = None
                trade_entry_reason = None

        # Risk management
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
            'entry_obv': obv,
            'entry_volume': volume,
            'entry_reasoning': trade_entry_reason
        })

        log_trade(f"\n===========================================")
        log_trade(f"Closed remaining position at market close")
        log_trade(f"Entry Reasoning: {trade_entry_reason}")
        log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {final_price:.2f}")
        log_trade(f"OBV at Entry: {obv:,}")
        log_trade(f"Volume at Entry: {volume:,}")
        log_trade(f"Profit/Loss: {profit:.2f}")
        log_trade(f"Final Balance: {balance:.2f}")
        log_trade(f"===========================================")

    # Enhanced Trading Summary Logs
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
            log_trade(f"OBV at Entry: {trade['entry_obv']:,}")
            log_trade(f"Volume at Entry: {trade['entry_volume']:,}")
            log_trade(f"Status: {trade['status']}")
            log_trade(f"Profit/Loss: {trade['profit']:.2f}")
            log_trade(f"Entry Reasoning: {trade['entry_reasoning']}")

        log_trade(f"\nProfit/Loss Statistics:")
        log_trade(f"Profitable Trades: {len(profit_trades)}")
        log_trade(f"Loss-making Trades: {len(loss_trades)}")
        if len(profit_trades) > 0:
            log_trade(f"Average Profit per Winning Trade: {profit_trades['profit'].mean():.2f}")
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per Losing Trade: {loss_trades['profit'].mean():.2f}")

        # Calculate win rate
        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")

        # Order Flow-specific metrics
        log_trade(f"\nOrder Flow-specific Metrics:")
        log_trade(f"Average OBV at Entry: {trades_df['entry_obv'].mean():.2f}")
        log_trade(f"Average Volume at Entry: {trades_df['entry_volume'].mean():.2f}")
        log_trade(f"Maximum Single Trade Profit: {trades_df['profit'].max():.2f}")
        log_trade(f"Maximum Single Trade Loss: {trades_df['profit'].min():.2f}")
    
    log_trade("\n===========================================")
    return balance, trades

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), './Order_Flow_Trading/NSE_NIFTY, 1 Intraday.csv')
    
    try:
        data = load_market_data(file_path)
        params = {
            'initial_balance': config_OrderFlow.initial_balance,
            'stop_loss_pct': config_OrderFlow.stop_loss_pct,
            'target_profit_pct': config_OrderFlow.target_profit_pct,
        }
        
        final_balance, trades = run_order_flow_strategy(
            data,
            initial_balance=params['initial_balance'],
            stop_loss_pct=params['stop_loss_pct'],
            target_profit_pct=params['target_profit_pct'],
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")