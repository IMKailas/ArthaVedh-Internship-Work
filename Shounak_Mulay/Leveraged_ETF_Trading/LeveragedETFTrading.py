import pandas as pd
import os
import random
import config_LeveragedETF
from datetime import datetime

def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Leveraged_ETF_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_etf_data(file_path):
    """Load and preprocess the ETF data"""
    try:
        data = pd.read_csv(file_path)
        return data
    except FileNotFoundError:
        error_msg = f"Error: File not found at {file_path}"
        log_error(error_msg)
        raise

def log_error(message):
    """Log errors to a dedicated error log file"""
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_filename, 'a') as f:
        f.write(f"{message}\n")

def calculate_volatility(row):
    return row["high"] - row["low"]

def calculate_market_trend(row):
    return "up" if row["close"] > row["VWAP"] else "down"

def leveraged_etf_decision(row, position, entry_made):
    volatility = calculate_volatility(row)
    market_trend = calculate_market_trend(row)
    high_volatility_threshold = 1.0
    
    # Build detailed reasoning components
    reasoning = []
    reasoning.append(f"Volatility: {volatility:.2f} ({['Low', 'High'][volatility >= high_volatility_threshold]})")
    reasoning.append(f"Market Trend: {market_trend.capitalize()}")
    reasoning.append(f"Close Price: {row['close']:.2f}")
    reasoning.append(f"VWAP: {row['VWAP']:.2f}")
    
    # Add position status to reasoning
    position_status = "No Position" if position is None else position
    entry_status = "No Prior Entry" if not entry_made else "Entry Made"
    reasoning.append(f"Position: {position_status} | {entry_status}")

    # Combine reasoning
    full_reasoning = " | ".join(reasoning)
    
    if position is None and not entry_made and volatility >= high_volatility_threshold and market_trend == "up":
        return "Buy", full_reasoning
    return "Hold", full_reasoning

def simulate_etf_price_change(entry_price, volatility, trend):
    price_change = round(random.uniform(0.1, 2) * volatility, 2)
    price_change *= 1.1 if trend == "up" else -1.1
    return round(entry_price + price_change, 2)

def run_leveraged_etf_strategy(etf_data, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    # Create log file with timestamp
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"leveraged_etf_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    def log_trade(message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        print(f"{message}")

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    entry_made = False
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    # Initial strategy parameters logging
    log_trade(f"===========================================")
    log_trade(f"  Leveraged ETF Trading Strategy  ")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Leverage: {leverage}x")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    log_trade(f"High Volatility Threshold: 1.0")

    for index, row in etf_data.iterrows():
        timestamp = pd.Timestamp(row.name if isinstance(row.name, pd.Timestamp) else row.get('time', datetime.now()))
        price = row["close"]
        volatility = calculate_volatility(row)
        trend = calculate_market_trend(row)

        # Check for new entry
        if position is None:
            decision, reasoning = leveraged_etf_decision(row, position, entry_made)
            
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

        # Manage active position
        if position == "Buy":
            current_price = simulate_etf_price_change(trade_price, volatility, trend)
            leveraged_gain_loss = (current_price - trade_price) * leverage

            if current_price <= stop_loss or current_price >= target_profit:
                # Calculate final profit/loss
                profit = leveraged_gain_loss
                balance += profit
                
                # Determine exit reason
                exit_reason = "Stop Loss" if current_price <= stop_loss else "Target Profit"
                
                # Record trade details
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
                
                # Log trade closure details
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
        final_price = etf_data.iloc[-1]['close']
        leveraged_gain_loss = (final_price - trade_price) * leverage
        profit = leveraged_gain_loss
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
        log_trade(f"Closed remaining position at market close")
        log_trade(f"Entry Reasoning: {trade_entry_reason}")
        log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {final_price:.2f}")
        log_trade(f"Profit/Loss: {profit:.2f}")
        log_trade(f"Final Balance: {balance:.2f}")
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
    file_path = os.path.join(os.getcwd(), './Leveraged_ETF_Trading/NSE_NIFTY, 1 Intraday.csv')
    
    initial_balance = config_LeveragedETF.initial_balance
    leverage = config_LeveragedETF.leverage
    stop_loss_pct = config_LeveragedETF.stop_loss_pct
    target_profit_pct = config_LeveragedETF.target_profit_pct

    try:
        etf_data = load_etf_data(file_path)
        final_balance, trades = run_leveraged_etf_strategy(
            etf_data, 
            initial_balance, 
            leverage, 
            stop_loss_pct, 
            target_profit_pct
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")