import pandas as pd
import numpy as np
import os
import talib
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
        # log_error(f"Error: File not found at {file_path}")
        raise

def calculate_technical_indicators(data):
    """Calculate various technical indicators using TALib"""
    high = data['high'].values
    low = data['low'].values
    close = data['close'].values
    volume = data['Volume'].values
    
    # Volatility Indicators
    data['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    data['NATR'] = talib.NATR(high, low, close, timeperiod=14)
    data['TRANGE'] = talib.TRANGE(high, low, close)
    
    # Momentum and Trend Indicators
    data['ADX'] = talib.ADX(high, low, close, timeperiod=14)
    data['RSI'] = talib.RSI(close, timeperiod=14)
    
    # Bollinger Bands for Volatility
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
    data['BB_UPPER'] = upper
    data['BB_MIDDLE'] = middle
    data['BB_LOWER'] = lower
    data['BB_WIDTH'] = (upper - lower) / middle
    
    # Custom Volatility Score
    data['VOL_SCORE'] = (data['NATR'] + data['BB_WIDTH']) / 2
    
    return data

def calculate_implied_volatility(data):
    """
    Calculate a synthetic implied volatility measure
    Note: This is a simplified approximation since real implied volatility 
    requires options data
    """
    close = data['close'].values
    high = data['high'].values
    low = data['low'].values
    
    # Calculate historical volatility using log returns
    log_returns = np.log(close[1:] / close[:-1])
    hist_vol = np.std(log_returns) * np.sqrt(252)  # Annualized
    
    # Calculate Parkinson volatility estimator
    parkinsons_vol = np.sqrt(1 / (4 * np.log(2)) * np.mean(np.log(high/low)**2)) * np.sqrt(252)
    
    # Synthetic IV (combination of historical and Parkinson's volatility)
    synthetic_iv = (hist_vol + parkinsons_vol) / 2
    
    return synthetic_iv

def volatility_decision(row, previous_row, synthetic_iv):
    """Enhanced decision making using technical indicators and volatility measures"""
    
    # Define thresholds
    vol_score_threshold = config.VOL_SCORE_THRESHOLD
    atr_threshold = config.ATR_THRESHOLD
    adx_threshold = config.ADX_THRESHOLD
    rsi_oversold = config.RSI_OVERSOLD
    
    # Volatility conditions
    high_volatility = (row['VOL_SCORE'] > vol_score_threshold and 
                      row['ATR'] > atr_threshold)
    
    # Trend strength
    strong_trend = row['ADX'] > adx_threshold
    
    # RSI conditions
    oversold = row['RSI'] < rsi_oversold

    if (high_volatility and strong_trend and oversold):
        return "Buy"
    
    return "Hold"

def run_volatility_strategy(data, initial_balance, stop_loss_pct, target_profit_pct):
    # Calculate technical indicators
    data = calculate_technical_indicators(data)
    synthetic_iv = calculate_implied_volatility(data)
    
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
    log_trade(f"  Enhanced Volatility Trading Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    
    previous_row = None
    for index, row in data.iterrows():
        if index < 20:  # Skip initial periods to allow for indicator calculation
            previous_row = row
            continue
            
        current_price = row['close']
        timestamp = pd.Timestamp(row['time']) if 'time' in row else pd.Timestamp.now()
        
        if position is None:
            decision = volatility_decision(row, previous_row, synthetic_iv)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")
                log_trade(f"Current VOL_SCORE: {row['VOL_SCORE']:.2f}")
                log_trade(f"Current ATR: {row['ATR']:.2f}")
                log_trade(f"Current Synthetic IV: {synthetic_iv:.2f}")
        
        if position == "Buy":
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
                    'vol_score_at_entry': row['VOL_SCORE'],
                    'synthetic_iv_at_entry': synthetic_iv
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
    
    # Trading Summary and Analysis
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
        
        # Analyze trade performance
        profitable_trades = trades_df[trades_df['profit'] > 0]
        losing_trades = trades_df[trades_df['profit'] < 0]
        
        log_trade(f"\nTrade Analysis:")
        log_trade(f"Win Rate: {(len(profitable_trades)/len(trades))*100:.2f}%")
        log_trade(f"Average Profit (winning trades): {profitable_trades['profit'].mean():.2f}")
        log_trade(f"Average Loss (losing trades): {losing_trades['profit'].mean():.2f}")
        log_trade(f"Average Volatility Score at Entry: {trades_df['vol_score_at_entry'].mean():.2f}")
        log_trade(f"Average Synthetic IV at Entry: {trades_df['synthetic_iv_at_entry'].mean():.2f}")
    
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