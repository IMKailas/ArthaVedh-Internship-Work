import pandas as pd
import os
import random
from datetime import datetime
import config_VolatilityTrading as config

def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Volatility_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_market_data(file_path):
    try:
        data = pd.read_csv(file_path)
        if config.ENABLE_DEBUG_LOGGING:
            print(f"Data loaded successfully from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        log_error(f"Error: File not found at {file_path}")
        raise

def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    with open(log_filename, 'a') as f:
        f.write(f"{message}\n")

def simulate_vix():
    return round(random.uniform(20, 40), 2)

def volume_price_decision(row, previous_row, vix):
    volume = row['Volume']
    price = row['close']
    previous_price = previous_row['close'] if previous_row is not None else price

    volume_threshold = config.VOLUME_THRESHOLD
    price_increase_threshold = config.PRICE_INCREASE_THRESHOLD
    high_vix_threshold = config.HIGH_VIX_THRESHOLD

    price_change_percentage = ((price - previous_price) / previous_price) * 100 if previous_price != 0 else 0

    if config.ENABLE_DEBUG_LOGGING:
        print(f"\nAnalyzing conditions:")
        print(f"Volume: {volume}")
        print(f"Price Change %: {price_change_percentage:.2f}")
        print(f"VIX: {vix}")

    if vix > high_vix_threshold and volume > volume_threshold and price_change_percentage > price_increase_threshold:
        return "Buy"
    return "Hold"

def simulate_price_change(entry_price, current_price):
    price_fluctuation = current_price - entry_price
    return round(current_price + price_fluctuation, 2)

def run_volatility_strategy(data, initial_balance, stop_loss_pct, target_profit_pct):
    # Create log directory and file
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"volatility_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        if config.ENABLE_DEBUG_LOGGING:
            print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_entry_time = None
    trades = []

    # Initialize logging
    log_trade(f"===========================================")
    log_trade(f"  Volatility Trading Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")

    previous_row = None
    for index, row in data.iterrows():
        current_price = row['close']
        volume = row['Volume']
        vix = simulate_vix()
        timestamp = pd.Timestamp(row['time']) if 'time' in row else pd.Timestamp.now()

        if position is None:
            decision = volume_price_decision(row, previous_row, vix)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")
                log_trade(f"Current VIX: {vix}")

        if position == "Buy":
            current_price = simulate_price_change(trade_price, current_price)

            if current_price <= stop_loss or current_price >= target_profit:
                profit = current_price - trade_price
                balance += profit
                
                exit_reason = "Stop Loss" if current_price <= stop_loss else "Target Profit"
                
                trade_info = {
                    'entry_time': trade_entry_time,
                    'exit_time': timestamp,
                    'type': position,
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'status': exit_reason,
                    'profit': profit,
                    'vix_at_entry': vix
                }
                trades.append(trade_info)

                log_trade(f"\n===========================================")
                log_trade(f"Closed {position} position: {exit_reason}")
                log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {current_price:.2f}")
                log_trade(f"Profit/Loss: {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                log_trade(f"Exit Time: {timestamp}")
                log_trade(f"===========================================")
                
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
                trade_entry_time = None

        if balance <= initial_balance * 0.7:
            log_trade(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

        previous_row = row

    # Close any remaining position
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
            'vix_at_entry': vix
        })

        log_trade(f"\n===========================================")
        log_trade(f"Closed remaining position at market close.")
        log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {final_price:.2f}")
        log_trade(f"Profit/Loss: {profit:.2f}")
        log_trade(f"New Balance: {balance:.2f}")
        log_trade(f"===========================================")

    # Trading Summary
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

        log_trade(f"Profitable Trades: {len(profit_trades)}")
        log_trade(f"Loss-making Trades: {len(loss_trades)}")
        if len(profit_trades) > 0:
            log_trade(f"Average Profit per Winning Trade: {profit_trades['profit'].mean():.2f}")
            log_trade(f"Highest Profit Trade: {profit_trades['profit'].max():.2f}")
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per Losing Trade: {loss_trades['profit'].mean():.2f}")
            log_trade(f"Largest Loss Trade: {loss_trades['profit'].min():.2f}")

        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")
        
        # Additional VIX analysis
        log_trade(f"\nVIX Analysis:")
        log_trade(f"Average VIX at Entry: {trades_df['vix_at_entry'].mean():.2f}")
        profit_trades_vix = trades_df[trades_df['profit'] > 0]['vix_at_entry'].mean()
        loss_trades_vix = trades_df[trades_df['profit'] < 0]['vix_at_entry'].mean()
        log_trade(f"Average VIX on Profitable Trades: {profit_trades_vix:.2f}")
        log_trade(f"Average VIX on Loss Trades: {loss_trades_vix:.2f}")
    
    log_trade("\n===========================================")

    return balance, trades

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), './Volatility_Trading/NSE_NIFTY, 1D.csv')
    try:
        data = load_market_data(file_path)
        final_balance, trades = run_volatility_strategy(
            data, 
            config.INITIAL_BALANCE, 
            config.STOP_LOSS_PCT, 
            config.TARGET_PROFIT_PCT
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        log_error(f"File not found: {file_path}")