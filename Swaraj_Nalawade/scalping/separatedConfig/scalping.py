import pandas as pd
import talib
from datetime import datetime
import config

# Function to load market data and calculate indicators using TA-Lib
def load_market_data(csv_file):
    df = pd.read_csv(csv_file)

    # Ensure time column is in datetime format
    df['time'] = pd.to_datetime(df['time'])

    # Sort data by time to maintain correct sequence
    df = df.sort_values(by='time').reset_index(drop=True)

    # Calculate indicators using TA-Lib
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['MACD'], df['Signal'], _ = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df['%K'], df['%D'] = talib.STOCH(df['high'], df['low'], df['close'], fastk_period=14, slowk_period=3, slowd_period=3)

    # ✅ Instead of dropping all NaN rows, fill NaNs with previous valid values
    df.fillna(method='bfill', inplace=True)  # Backfill NaNs
    df.fillna(method='ffill', inplace=True)  # Forward-fill remaining NaNs

    # ✅ DEBUG: Print after filling NaNs
    print("After filling NaN:")
    print(df[['time', 'close', 'RSI', 'MACD', 'Signal', '%K', '%D']].head(30))

    return df


# Function to fetch current market data
def get_market_data(df, current_index):
    if current_index >= len(df):
        return None
    
    row = df.iloc[current_index]
    return {
        "bid_price": row['close'],
        "ask_price": row['close'],
        "volume": row['Volume'],
        "rsi": row['RSI'],
        "macd": row['MACD'],
        "signal": row['Signal'],
        "k_percent": row['%K'],
        "d_percent": row['%D'],
        "timestamp": row['time']
    }

# Function to decide scalping action
def scalping_decision(market_data, position=None):
    print(f"DEBUG: Market Data at {market_data['timestamp']}")
    print(f"RSI: {market_data['rsi']}, MACD: {market_data['macd']}, Signal: {market_data['signal']}")
    print(f"K%: {market_data['k_percent']}, D%: {market_data['d_percent']}, Volume: {market_data['volume']}")

    if market_data['volume'] < config.MIN_VOLUME:
        print("Skipped trade due to low volume")
        return "Hold"

    if position == "Buy":
        if market_data['rsi'] > config.RSI_OVERBOUGHT or (market_data['macd'] < market_data['signal'] and market_data['k_percent'] < market_data['d_percent']):
            print("Exiting Buy position")
            return "Exit"
    elif position == "Sell":
        if market_data['rsi'] < config.RSI_OVERSOLD or (market_data['macd'] > market_data['signal'] and market_data['k_percent'] > market_data['d_percent']):
            print("Exiting Sell position")
            return "Exit"
    elif position is None:
        if market_data['rsi'] < config.RSI_BUY_THRESHOLD and market_data['macd'] > market_data['signal'] and market_data['k_percent'] > market_data['d_percent']:
            print("Buying condition met")
            return "Buy"
        elif market_data['rsi'] > config.RSI_SELL_THRESHOLD and market_data['macd'] < market_data['signal'] and market_data['k_percent'] < market_data['d_percent']:
            print("Selling condition met")
            return "Sell"

    return "Hold"

# Main function to run scalping strategy
def run_scalping_strategy():
    balance = config.INITIAL_BALANCE
    df = load_market_data(config.CSV_FILE_PATH)
    
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trades = []
    current_index = config.INITIAL_LOOKBACK
    
    log_filename = f"scalping_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(message + "\n")
        print(message)
    
    log_trade("===========================================")
    log_trade("  Scalping Strategy Started")
    log_trade("===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {config.STOP_LOSS_PERCENT}%")
    log_trade(f"Target Profit Percentage: {config.TARGET_PROFIT_PERCENT}%")
    log_trade(f"Minimum Volume: {config.MIN_VOLUME}")
    log_trade(f"RSI Buy Threshold: {config.RSI_BUY_THRESHOLD}")
    
    while current_index < len(df):
        market_data = get_market_data(df, current_index)
        if market_data is None:
            break
        
        current_price = market_data['bid_price']
        decision = scalping_decision(market_data, position)
        
        if position is not None:
            if (position == "Buy" and current_price <= stop_loss) or \
               (position == "Buy" and current_price >= target_profit) or \
               (position == "Sell" and current_price >= stop_loss) or \
               (position == "Sell" and current_price <= target_profit) or \
               decision == "Exit":
                profit = (current_price - trade_price if position == "Buy" 
                          else trade_price - current_price)
                balance += profit
                status = "Stop Loss" if (position == "Buy" and current_price <= stop_loss) or \
                                        (position == "Sell" and current_price >= stop_loss) else \
                         "Target Profit" if (position == "Buy" and current_price >= target_profit) or \
                                           (position == "Sell" and current_price <= target_profit) else \
                         "Technical Exit"
                
                log_trade(f"Closed {position} position: {status}")
                log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {current_price:.2f}")
                log_trade(f"Profit/Loss: {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                
                trades.append({
                    'entry_time': trade_entry_time,
                    'exit_time': market_data['timestamp'],
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'status': status,
                    'profit': profit
                })
                position = None
                current_index += config.COOLDOWN_PERIODS
                continue
        
        if position is None and decision in ["Buy", "Sell"]:
            position = decision
            trade_price = current_price
            stop_loss = trade_price * (1 - config.STOP_LOSS_PERCENT / 100) if position == "Buy" else \
                        trade_price * (1 + config.STOP_LOSS_PERCENT / 100)
            target_profit = trade_price * (1 + config.TARGET_PROFIT_PERCENT / 100) if position == "Buy" else \
                            trade_price * (1 - config.TARGET_PROFIT_PERCENT / 100)
            trade_entry_time = market_data['timestamp']
            
            log_trade(f"Opened {position} position at {trade_price:.2f}")
            log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
        
        current_index += 1
    
    log_trade("===========================================")
    log_trade("  Trading Summary")
    log_trade("===========================================")
    log_trade(f"Initial Balance: {config.INITIAL_BALANCE:.2f}")
    log_trade(f"Final Balance: {balance:.2f}")
    log_trade(f"Total Profit/Loss: {balance - config.INITIAL_BALANCE:.2f}")
    log_trade(f"Total Trades Executed: {len(trades)}")
    
    return balance, trades

if __name__ == "__main__":
    final_balance, trades = run_scalping_strategy()
