import pandas as pd
import numpy as np
import logging
from datetime import datetime

def setup_logging():
    """Configure logging with custom format showing only trade timestamps"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",  # Removed timestamp from logging format
        filename=f"momentum_trading_log_{datetime.now().strftime('%Y%m%d')}.log"
    )

def calculate_technical_indicators(df):
    """Calculate additional technical indicators for better signal generation"""
    # EMA calculations
    df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    # Enhanced RSI calculation
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Volume indicators
    df['Volume MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume Ratio'] = df['Volume'] / df['Volume MA']
    
    # Bollinger Bands
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['Upper BB'] = df['BB_middle'] + (bb_std * 2)
    df['Lower BB'] = df['BB_middle'] - (bb_std * 2)
    
    # Trend strength
    df['ADX'] = calculate_adx(df)
    
    return df

def calculate_adx(df, period=14):
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
    """Enhanced momentum signal identification"""
    # Trend confirmation
    strong_trend = df['ADX'] > 25
    uptrend = (df['EMA9'] > df['EMA21']) & (df['EMA21'] > df['EMA50'])
    downtrend = (df['EMA9'] < df['EMA21']) & (df['EMA21'] < df['EMA50'])
    
    # Volume confirmation
    volume_surge = df['Volume Ratio'] > 1.5
    
    # Price momentum
    price_strength = (df['close'] - df['close'].shift(10)) / df['close'].shift(10) * 100
    
    # RSI conditions
    rsi_bullish = (df['RSI'] > 30) & (df['RSI'] < 70)
    rsi_bearish = df['RSI'] > 70
    
    # Enhanced signal combination
    bullish_signal = (
        strong_trend &
        uptrend &
        volume_surge &
        (price_strength > 0) &
        rsi_bullish &
        (df['close'] > df['BB_middle']) &
        (df['close'] < df['Upper BB'])
    )
    
    bearish_signal = (
        strong_trend &
        downtrend &
        volume_surge &
        (price_strength < 0) &
        rsi_bearish &
        (df['close'] < df['BB_middle']) &
        (df['close'] > df['Lower BB'])
    )
    
    return bullish_signal, bearish_signal

def log_trade(trade_type, action, price, time, reason=None, profit=None, balance=None):
    """Enhanced trade logging"""
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
    """
    Print detailed trading summary to terminal with enhanced statistics and formatting
    """
    if len(trades_df) == 0:
        print("\nNo trades were executed during this period.")
        return

    # Calculate basic statistics
    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    loss_trades = len(trades_df[trades_df['profit'] <= 0])
    win_rate = (profitable_trades / total_trades) * 100
    total_profit = trades_df['profit'].sum()
    avg_profit = trades_df['profit'].mean()
    max_profit = trades_df['profit'].max()
    max_loss = trades_df['profit'].min()
    
    # Calculate trade types distribution
    long_trades = len(trades_df[trades_df['type'] == 'LONG'])
    short_trades = len(trades_df[trades_df['type'] == 'SHORT'])
    
    # Calculate exit reason distribution
    exit_reasons = trades_df['reason'].value_counts()
    
    # Print summary with formatting
    print("\n" + "="*60)
    print(f"{'TRADING SUMMARY':^60}")
    print("="*60)
    
    # Performance Metrics
    print("\nPERFORMANCE METRICS")
    print("-"*60)
    print(f"Initial Balance:      ${initial_balance:,.2f}")
    print(f"Final Balance:        ${final_balance:,.2f}")
    print(f"Total Profit/Loss:    ${total_profit:,.2f}")
    print(f"Return on Investment: {((final_balance - initial_balance) / initial_balance * 100):,.2f}%")
    
    # Trade Statistics
    print("\nTRADE STATISTICS")
    print("-"*60)
    print(f"Total Trades:         {total_trades}")
    print(f"Profitable Trades:    {profitable_trades}")
    print(f"Loss-Making Trades:   {loss_trades}")
    print(f"Win Rate:            {win_rate:.2f}%")
    print(f"Average Profit:      ${avg_profit:.2f}")
    print(f"Maximum Profit:      ${max_profit:.2f}")
    print(f"Maximum Loss:        ${max_loss:.2f}")
    
    # # Trade Distribution
    # print("\nTRADE DISTRIBUTION")
    # print("-"*60)
    # print(f"Long Trades:         {long_trades} ({(long_trades/total_trades*100):.1f}%)")
    # print(f"Short Trades:        {short_trades} ({(short_trades/total_trades*100):.1f}%)")
    
    # Exit Reason Analysis
    print("\nEXIT REASON ANALYSIS")
    print("-"*60)
    for reason, count in exit_reasons.items():
        print(f"{reason:.<20} {count:>3} trades ({(count/total_trades*100):>6.1f}%)")
    
    print("\n" + "="*60)
def run_momentum_strategy(data_path, initial_balance=10000, stop_loss_pct=1.0, target_profit_pct=2.0):
    # Setup logging
    setup_logging()
    
    # Load and prepare data
    df = pd.read_csv(data_path)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    df = df.sort_values('time')
    
    # Calculate technical indicators
    df = calculate_technical_indicators(df)
    
    # Trading variables
    balance = initial_balance
    position = None
    entry_price = None
    trade_history = []
    
    # Get signals
    bullish_signals, bearish_signals = identify_momentum_signals(df)
    
    # Main trading loop
    for i in range(50, len(df)):  # Start after indicators are well-established
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]
        
        # Position entry logic
        if position is None:
            if bullish_signals.iloc[i]:
                position = "LONG"
                entry_price = current_price
                log_trade("LONG", "ENTRY", current_price, current_time, balance=balance)
                
            elif bearish_signals.iloc[i]:
                position = "SHORT"
                entry_price = current_price
                log_trade("SHORT", "ENTRY", current_price, current_time, balance=balance)
        
        # Position exit logic
        elif position == "LONG":
            profit = current_price - entry_price
            stop_loss = entry_price * (1 - stop_loss_pct/100)
            target = entry_price * (1 + target_profit_pct/100)
            
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
            stop_loss = entry_price * (1 + stop_loss_pct/100)
            target = entry_price * (1 - target_profit_pct/100)
            
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
    
    # Log final statistics
    trades_df = pd.DataFrame(trade_history)
    if len(trades_df) > 0:
        profitable_trades = len(trades_df[trades_df['profit'] > 0])
        total_trades = len(trades_df)
        win_rate = (profitable_trades / total_trades) * 100
        
        summary = (
            f"\nFINAL TRADING SUMMARY\n"
            f"{'='*50}\n"
            f"Total Trades: {total_trades}\n"
            f"Profitable Trades: {profitable_trades}\n"
            f"Win Rate: {win_rate:.2f}%\n"
            f"Total Profit/Loss: {balance - initial_balance:.2f}\n"
            f"Return on Investment: {((balance - initial_balance) / initial_balance * 100):.2f}%\n"
            f"Final Balance: {balance:.2f}\n"
            f"{'='*50}"
        )
        logging.info(summary)
    print_trading_summary(trades_df, initial_balance, balance)
    return balance, trades_df

if __name__ == "__main__":
    DATA_PATH = r"C:\assignement\sem5\Internship\MomentumInvesting\NSE_NIFTY, 1D.csv"
    final_balance, trades = run_momentum_strategy(
        DATA_PATH,
        initial_balance=10000,
        stop_loss_pct=1.0,
        target_profit_pct=2.0
    )
