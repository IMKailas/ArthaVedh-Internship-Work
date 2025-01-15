import pandas as pd
import time
from datetime import datetime
import config

def load_market_data(csv_file):
    """Load and preprocess the CSV data"""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'])
    
    if config.ENABLE_DEBUG_LOGGING:
        print("\nData Overview:")
        print(f"Total rows: {len(df)}")
        print("\nSample of loaded data:")
        print(df.head(1).to_string())
        print("\nColumns available:", df.columns.tolist())
    
    return df

def get_market_data(df, current_index):
    """Get market data for the current index from DataFrame"""
    if current_index >= len(df):
        return None
    
    current_row = df.iloc[current_index]
    
    market_data = {
        "bid_price": current_row['close'],
        "ask_price": current_row['close'],
        "volume": current_row['Volume'],
        "buy_orders": current_row['Volume'],
        "sell_orders": current_row['Volume'],
        "rsi": current_row['RSI'],
        "macd": current_row['MACD'],
        "signal": current_row['Signal'],
        "upper_band": current_row['Upper Band #1'],
        "lower_band": current_row['Lower Band #1'],
        "vwap": current_row['VWAP'],
        "k_percent": current_row['%K'],
        "d_percent": current_row['%D'],
        "timestamp": current_row['time']
    }
    return market_data

def scalping_decision(market_data, position=None):
    """Enhanced decision making with position awareness"""
    if pd.isna(market_data["rsi"]) or pd.isna(market_data["macd"]) or \
       pd.isna(market_data["signal"]) or pd.isna(market_data["k_percent"]) or \
       pd.isna(market_data["d_percent"]):
        return "Hold"

    rsi = market_data["rsi"]
    macd = market_data["macd"]
    signal = market_data["signal"]
    volume = market_data["volume"]
    k_percent = market_data["k_percent"]
    d_percent = market_data["d_percent"]
    
    if config.ENABLE_DEBUG_LOGGING:
        print(f"\nAnalyzing conditions for {market_data['timestamp']}:")
        print(f"Current position: {position}")
        print(f"RSI: {rsi:.2f}")
        print(f"MACD: {macd:.2f}, Signal: {signal:.2f}")
        print(f"Stochastic K%: {k_percent:.2f}, D%: {d_percent:.2f}")
    
    if volume < config.MIN_VOLUME:
        return "Hold"
        
    # Exit conditions if in position
    if position == "Buy":
        if (rsi > config.RSI_OVERBOUGHT) or \
           (config.MACD_CROSSOVER_SELL and macd < signal and 
            config.STOCH_CROSSOVER_SELL and k_percent < d_percent):
            return "Exit"
    elif position == "Sell":
        if (rsi < config.RSI_OVERSOLD) or \
           (config.MACD_CROSSOVER_BUY and macd > signal and 
            config.STOCH_CROSSOVER_BUY and k_percent > d_percent):
            return "Exit"
            
    # Entry conditions if not in position
    if position is None:
        if (rsi < config.RSI_BUY_THRESHOLD and 
            (not config.MACD_CROSSOVER_BUY or macd > signal) and 
            (not config.STOCH_CROSSOVER_BUY or k_percent > d_percent)):
            return "Buy"
        elif (rsi > config.RSI_SELL_THRESHOLD and 
              (not config.MACD_CROSSOVER_SELL or macd < signal) and 
              (not config.STOCH_CROSSOVER_SELL or k_percent < d_percent)):
            return "Sell"
    
    return "Hold"

def run_scalping_strategy():
    print(f"Starting strategy with {config.INITIAL_BALANCE} initial balance")
    print(f"Stop Loss: {config.STOP_LOSS_PERCENT}%, Target Profit: {config.TARGET_PROFIT_PERCENT}%")
    
    df = load_market_data(config.CSV_FILE_PATH)
    
    balance = config.INITIAL_BALANCE
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_entry_time = None
    trades = []
    current_index = config.INITIAL_LOOKBACK
    
    # Create log file
    log_filename = f"trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{datetime.now()} - {message}\n")
        print(message)
    
    while current_index < len(df):
        market_data = get_market_data(df, current_index)
        if market_data is None:
            break
            
        current_price = market_data["bid_price"]
        
        # Check for exit conditions first
        if position is not None:
            # Check stop loss and target profit
            hit_stop_loss = (position == "Buy" and current_price <= stop_loss) or \
                           (position == "Sell" and current_price >= stop_loss)
            hit_target = (position == "Buy" and current_price >= target_profit) or \
                        (position == "Sell" and current_price <= target_profit)
            
            # Check technical exit signals
            decision = scalping_decision(market_data, position)
            technical_exit = decision == "Exit"
            
            if hit_stop_loss or hit_target or technical_exit:
                # Calculate profit/loss
                profit = (current_price - trade_price if position == "Buy" 
                         else trade_price - current_price)
                balance += profit
                
                # Determine exit reason
                exit_reason = "Stop Loss" if hit_stop_loss else \
                            "Target Profit" if hit_target else \
                            "Technical Exit"
                
                # Log trade
                trade_info = {
                    'entry_time': trade_entry_time,
                    'exit_time': market_data['timestamp'],
                    'type': position,
                    'entry_price': trade_price,
                    'exit_price': current_price,
                    'status': exit_reason,
                    'profit': profit
                }
                trades.append(trade_info)
                
                log_trade(f"\nClosed {position} position: {exit_reason}")
                log_trade(f"Entry: {trade_price:.2f}, Exit: {current_price:.2f}")
                log_trade(f"Profit/Loss: {profit:.2f}, New Balance: {balance:.2f}")
                
                # Reset position
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
                trade_entry_time = None
                
                # Add cooldown period
                current_index += config.COOLDOWN_PERIODS
                continue
        
        # Look for new entry only if not in position
        if position is None:
            decision = scalping_decision(market_data)
            
            if decision in ["Buy", "Sell"]:
                position = decision
                trade_price = current_price
                trade_entry_time = market_data['timestamp']
                
                # Set stop loss and target profit
                if position == "Buy":
                    stop_loss = trade_price * (1 - config.STOP_LOSS_PERCENT / 100)
                    target_profit = trade_price * (1 + config.TARGET_PROFIT_PERCENT / 100)
                else:  # Sell
                    stop_loss = trade_price * (1 + config.STOP_LOSS_PERCENT / 100)
                    target_profit = trade_price * (1 - config.TARGET_PROFIT_PERCENT / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target: {target_profit:.2f}")
        
        current_index += 1
    
    # Close any remaining position at the end
    if position is not None:
        final_price = df.iloc[-1]['close']
        profit = (final_price - trade_price if position == "Buy" 
                 else trade_price - final_price)
        balance += profit
        trades.append({
            'entry_time': trade_entry_time,
            'exit_time': df.iloc[-1]['time'],
            'type': position,
            'entry_price': trade_price,
            'exit_price': final_price,
            'status': 'Market Close',
            'profit': profit
        })
    
    # Create summary report
    if config.SAVE_TRADE_HISTORY:
        trades_df = pd.DataFrame(trades)
        trades_df.to_csv(f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    print("\nTrading Summary:")
    print(f"Initial Balance: {config.INITIAL_BALANCE:.2f}")
    print(f"Final Balance: {balance:.2f}")
    print(f"Total Profit/Loss: {balance - config.INITIAL_BALANCE:.2f}")
    print(f"Total Trades: {len(trades)}")
    
    if len(trades) > 0:
        trades_df = pd.DataFrame(trades)
        trades_df['profit'] = trades_df['profit'].astype(float)
        profit_trades = trades_df[trades_df['profit'] > 0]
        loss_trades = trades_df[trades_df['profit'] < 0]
        
        print(f"Profitable Trades: {len(profit_trades)}")
        print(f"Loss-making Trades: {len(loss_trades)}")
        if len(profit_trades) > 0:
            print(f"Average Profit per winning trade: {profit_trades['profit'].mean():.2f}")
        if len(loss_trades) > 0:
            print(f"Average Loss per losing trade: {loss_trades['profit'].mean():.2f}")
            
        # Calculate win rate
        win_rate = len(profit_trades) / len(trades) * 100
        print(f"Win Rate: {win_rate:.2f}%")
    
    return balance, trades

if __name__ == "__main__":
    final_balance, trades = run_scalping_strategy()
