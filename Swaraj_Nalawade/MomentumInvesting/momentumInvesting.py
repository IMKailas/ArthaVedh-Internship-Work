# momentum_strategy.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import config

def setup_logging():
    """Configure logging with custom format"""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        filename=f"{config.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d')}.log"
    )

def calculate_technical_indicators(df):
    """Calculate technical indicators for signal generation"""
    # EMA calculations
    df['EMA9'] = df['close'].ewm(span=config.EMA_PERIODS['fast'], adjust=False).mean()
    df['EMA21'] = df['close'].ewm(span=config.EMA_PERIODS['medium'], adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=config.EMA_PERIODS['slow'], adjust=False).mean()
    
    # RSI calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=config.RSI_PERIOD).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Volume indicators
    df['Volume MA'] = df['Volume'].rolling(window=config.VOLUME_MA_PERIOD).mean()
    df['Volume Ratio'] = df['Volume'] / df['Volume MA']
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=config.BOLLINGER_PERIOD).mean()
    bb_std = df['close'].rolling(window=config.BOLLINGER_PERIOD).std()
    df['Upper BB'] = df['BB_middle'] + (bb_std * config.BOLLINGER_STD)
    df['Lower BB'] = df['BB_middle'] - (bb_std * config.BOLLINGER_STD)
    
    # Trend strength
    df['ADX'] = calculate_adx(df)
    
    return df

def calculate_adx(df, period=config.ADX_PERIOD):
    """Calculate Average Directional Index (ADX)"""
    df['TR'] = np.maximum(
        np.maximum(
            df['high'] - df['low'],
            abs(df['high'] - df['close'].shift(1))
        ),
        abs(df['low'] - df['close'].shift(1))
    )
    
    df['+DM'] = np.where(
        (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
        np.maximum(df['high'] - df['high'].shift(1), 0),
        0
    )
    
    df['-DM'] = np.where(
        (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
        np.maximum(df['low'].shift(1) - df['low'], 0),
        0
    )
    
    df['TR14'] = df['TR'].rolling(window=period).sum()
    df['+DM14'] = df['+DM'].rolling(window=period).sum()
    df['-DM14'] = df['-DM'].rolling(window=period).sum()
    
    df['+DI14'] = (df['+DM14'] / df['TR14']) * 100
    df['-DI14'] = (df['-DM14'] / df['TR14']) * 100
    
    df['DX'] = abs(df['+DI14'] - df['-DI14']) / (df['+DI14'] + df['-DI14']) * 100
    df['ADX'] = df['DX'].rolling(window=period).mean()
    
    return df['ADX']

def identify_momentum_signals(df):
    """Identify momentum trading signals based on configured conditions"""
    signals = pd.DataFrame(index=df.index)
    
    if config.SIGNAL_REQUIREMENTS['trend_strength']:
        signals['strong_trend'] = df['ADX'] > config.ADX_THRESHOLD
    else:
        signals['strong_trend'] = True
        
    if config.SIGNAL_REQUIREMENTS['ema_alignment']:
        signals['uptrend'] = (df['EMA9'] > df['EMA21']) & (df['EMA21'] > df['EMA50'])
        signals['downtrend'] = (df['EMA9'] < df['EMA21']) & (df['EMA21'] < df['EMA50'])
    else:
        signals['uptrend'] = signals['downtrend'] = True
        
    if config.SIGNAL_REQUIREMENTS['volume_confirmation']:
        signals['volume_surge'] = df['Volume Ratio'] > config.VOLUME_SURGE_THRESHOLD
    else:
        signals['volume_surge'] = True
        
    if config.SIGNAL_REQUIREMENTS['price_momentum']:
        price_strength = (df['close'] - df['close'].shift(config.MOMENTUM_LOOKBACK)) / df['close'].shift(config.MOMENTUM_LOOKBACK) * 100
        signals['price_momentum'] = price_strength > config.PRICE_STRENGTH_THRESHOLD
    else:
        signals['price_momentum'] = True
        
    if config.SIGNAL_REQUIREMENTS['rsi_filter']:
        signals['rsi_bullish'] = (df['RSI'] > config.RSI_OVERSOLD) & (df['RSI'] < config.RSI_OVERBOUGHT)
        signals['rsi_bearish'] = df['RSI'] > config.RSI_OVERBOUGHT
    else:
        signals['rsi_bullish'] = signals['rsi_bearish'] = True
        
    if config.SIGNAL_REQUIREMENTS['bollinger_bands']:
        signals['bb_bullish'] = (df['close'] > df['BB_middle']) & (df['close'] < df['Upper BB'])
        signals['bb_bearish'] = (df['close'] < df['BB_middle']) & (df['close'] > df['Lower BB'])
    else:
        signals['bb_bullish'] = signals['bb_bearish'] = True
    
    bullish_signal = (
        signals['strong_trend'] &
        signals['uptrend'] &
        signals['volume_surge'] &
        signals['price_momentum'] &
        signals['rsi_bullish'] &
        signals['bb_bullish']
    )
    
    bearish_signal = (
        signals['strong_trend'] &
        signals['downtrend'] &
        signals['volume_surge'] &
        ~signals['price_momentum'] &
        signals['rsi_bearish'] &
        signals['bb_bearish']
    )
    
    return bullish_signal, bearish_signal

def log_trade(trade_type, action, price, time, reason=None, profit=None, balance=None):
    """Log trade details"""
    if action == "ENTRY":
        log_msg = (
            f"[{time}] {trade_type} ENTRY\n"
            f"Price: {price:.2f}\n"
            f"Current Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    else:  # EXIT
        log_msg = (
            f"[{time}] {trade_type} EXIT\n"
            f"Price: {price:.2f}\n"
            f"Reason: {reason}\n"
            f"Profit/Loss: {profit:.2f}\n"
            f"New Balance: {balance:.2f}\n"
            f"{'-'*50}"
        )
    logging.info(log_msg)

def print_trading_summary(trades_df, initial_balance, final_balance):
    """Print detailed trading summary"""
    if len(trades_df) == 0:
        print("\nNo trades were executed during this period.")
        return

    # Calculate statistics
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    loss_trades = len(trades_df[trades_df['profit'] <= 0])
    win_rate = (profitable_trades / total_trades) * 100
    total_profit = trades_df['profit'].sum()
    avg_profit = trades_df['profit'].mean()
    max_profit = trades_df['profit'].max()
    max_loss = trades_df['profit'].min()
    exit_reasons = trades_df['reason'].value_counts()
    
    # Print formatted summary
    print("\n" + "="*60)
    print(f"{'TRADING SUMMARY':^60}")
    print("="*60)
    
    print("\nPERFORMANCE METRICS")
    print("-"*60)
    print(f"Initial Balance:      ${initial_balance:,.2f}")
    print(f"Final Balance:        ${final_balance:,.2f}")
    print(f"Total Profit/Loss:    ${total_profit:,.2f}")
    print(f"Return on Investment: {((final_balance - initial_balance) / initial_balance * 100):,.2f}%")
    
    print("\nTRADE STATISTICS")
    print("-"*60)
    print(f"Total Trades:         {total_trades}")
    print(f"Profitable Trades:    {profitable_trades}")
    print(f"Loss-Making Trades:   {loss_trades}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Average Profit:      ${avg_profit:.2f}")
    print(f"Maximum Profit:      ${max_profit:.2f}")
    print(f"Maximum Loss:        ${max_loss:.2f}")
    
    print("\nEXIT REASON ANALYSIS")
    print("-"*60)
    for reason, count in exit_reasons.items():
        print(f"{reason:.<20} {count:>3} trades ({(count/total_trades*100):>6.1f}%)")
    
    print("\n" + "="*60)

def run_momentum_strategy():
    """Execute the momentum trading strategy"""
    setup_logging()
    
    # Load and prepare data
    df = pd.read_csv(config.DATA_PATH)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    df = df.sort_values('time')
    
    # Calculate indicators
    df = calculate_technical_indicators(df)
    
    # Initialize trading variables
    balance = config.INITIAL_BALANCE
    position = None
    entry_price = None
    trade_history = []
    
    # Get trading signals
    bullish_signals, bearish_signals = identify_momentum_signals(df)
    
    # Main trading loop
    for i in range(config.MIN_LOOKBACK, len(df)):
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]
        
        if position is None:
            if bullish_signals.iloc[i]:
                position = "LONG"
                entry_price = current_price
                log_trade("LONG", "ENTRY", current_price, current_time, balance=balance)
                
            elif bearish_signals.iloc[i]:
                position = "SHORT"
                entry_price = current_price
                log_trade("SHORT", "ENTRY", current_price, current_time, balance=balance)
        
        elif position == "LONG":
            profit = current_price - entry_price
            stop_loss = entry_price * (1 - config.STOP_LOSS_PERCENT/100)
            target = entry_price * (1 + config.TARGET_PROFIT_PERCENT/100)
            
            if current_price <= stop_loss:
                log_trade("LONG", "EXIT", current_price, current_time, "Stop Loss", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "LONG", "profit": profit, "reason": "Stop Loss"})
                
            elif current_price >= target:
                log_trade("LONG", "EXIT", current_price, current_time, "Target Reached", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "LONG", "profit": profit, "reason": "Target"})
                
            elif bearish_signals.iloc[i]:
                log_trade("LONG", "EXIT", current_price, current_time, "Signal Reversal", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "LONG", "profit": profit, "reason": "Signal"})
        
        elif position == "SHORT":
            profit = entry_price - current_price
            stop_loss = entry_price * (1 + config.STOP_LOSS_PERCENT/100)
            target = entry_price * (1 - config.TARGET_PROFIT_PERCENT/100)
            
            if current_price >= stop_loss:
                log_trade("SHORT", "EXIT", current_price, current_time, "Stop Loss", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "SHORT", "profit": profit, "reason": "Stop Loss"})
                
            elif current_price <= target:
                log_trade("SHORT", "EXIT", current_price, current_time, "Target Reached", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "SHORT", "profit": profit, "reason": "Target"})
                
            elif bullish_signals.iloc[i]:
                log_trade("SHORT", "EXIT", current_price, current_time, "Signal Reversal", profit, balance + profit)
                balance += profit
                position = None
                trade_history.append({"type": "SHORT", "profit": profit, "reason": "Signal"})

    # Convert trade history to DataFrame for summary
    trades_df = pd.DataFrame(trade_history)

    # Print trading summary
    print_trading_summary(trades_df, config.INITIAL_BALANCE, balance)

    # Save trade history to a CSV for further analysis
    trades_df.to_csv(f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv", index=False)

if __name__ == "__main__":
    run_momentum_strategy()
