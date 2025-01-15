import pandas as pd
import numpy as np
import logging
from datetime import datetime
import config
import json
import os
from pathlib import Path

# Set up logging directory
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

# Set up multiple log handlers
def setup_logging():
    """Configure logging with multiple handlers for different log types"""
    logger = logging.getLogger('trading_system')
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Main log file handler
    main_log = log_dir / f"trading_log_{timestamp}.log"
    main_handler = logging.FileHandler(main_log)
    main_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(main_handler)
    
    # Trade-specific log file handler
    trade_log = log_dir / f"trade_details_{timestamp}.log"
    trade_handler = logging.FileHandler(trade_log)
    trade_handler.setFormatter(logging.Formatter('%(asctime)s - TRADE - %(message)s'))
    logger.addHandler(trade_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(config.LOG_FORMAT))
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

def log_trade_entry(trade_data, current_balance):
    """Log details of trade entry"""
    trade_info = {
        'type': 'ENTRY',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'direction': 'LONG' if trade_data['direction'] == 1 else 'SHORT',
        'entry_price': trade_data['entry_price'],
        'position_size': trade_data['size'],
        'current_balance': current_balance
    }
    logger.info(f"TRADE_ENTRY: {json.dumps(trade_info)}")

def log_trade_exit(trade_data, current_balance, exit_reason):
    """Log details of trade exit"""
    trade_info = {
        'type': 'EXIT',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'exit_price': trade_data['exit_price'],
        'entry_price': trade_data['entry_price'],
        'profit': trade_data['profit'],
        'current_balance': current_balance,
        'exit_reason': exit_reason
    }
    logger.info(f"TRADE_EXIT: {json.dumps(trade_info)}")

def log_trading_summary(initial_balance, final_balance, trades_df):
    """Generate and log trading session summary"""
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    total_trades = len(trades_df)
    
    summary = {
        'session_timestamp': timestamp,
        'initial_balance': initial_balance,
        'final_balance': final_balance,
        'total_profit_loss': final_balance - initial_balance,
        'return_percentage': ((final_balance - initial_balance) / initial_balance * 100),
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': (profitable_trades / total_trades * 100) if total_trades > 0 else 0,
        'average_profit_per_trade': trades_df['profit'].mean() if total_trades > 0 else 0,
        'largest_win': trades_df['profit'].max() if total_trades > 0 else 0,
        'largest_loss': trades_df['profit'].min() if total_trades > 0 else 0
    }
    
    # Log summary to main log file
    logger.info(f"SESSION_SUMMARY: {json.dumps(summary)}")
    
    # Save detailed summary to separate file
    summary_file = log_dir / f"session_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=4)

# Set up logging using config parameters
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)

def validate_data(df):
    """Validate that all required columns are present in the dataset"""
    missing_columns = [col for col in config.REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    logging.info("Data validation passed.")
    return True

def calculate_trend_strength(df):
    """Calculate market trend strength using multiple indicators"""
    # Calculate SMAs using config parameters
    df['SMA20'] = df['close'].rolling(window=config.SMA_SHORT_PERIOD).mean()
    df['SMA50'] = df['close'].rolling(window=config.SMA_LONG_PERIOD).mean()

    # Calculate ADX using config parameters
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    tr = pd.DataFrame([
        df['high'] - df['low'],
        (df['high'] - df['close'].shift()).abs(),
        (df['low'] - df['close'].shift()).abs()
    ]).max()
    
    plus_di = (plus_dm.rolling(window=config.ADX_PERIOD).mean() / 
              tr.rolling(window=config.ADX_PERIOD).mean()) * 100
    minus_di = (minus_dm.rolling(window=config.ADX_PERIOD).mean() / 
               tr.rolling(window=config.ADX_PERIOD).mean()) * 100
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di).abs() * 100
    df['ADX'] = dx.rolling(window=config.ADX_PERIOD).mean()

    logging.info("Trend strength calculated.")
    return df

def generate_signals(df):
    """Generate trading signals with improved risk management"""
    df = calculate_trend_strength(df)

    # Initialize signal series
    signals = pd.Series(0, index=df.index)

    # Trend confirmation using config parameters
    strong_trend = df['ADX'] > config.ADX_TREND_THRESHOLD
    uptrend = (df['close'] > df['SMA20']) & (df['SMA20'] > df['SMA50'])
    downtrend = (df['close'] < df['SMA20']) & (df['SMA20'] < df['SMA50'])

    # Volume confirmation
    volume_confirmation = df['Volume'] > df['Volume MA'] * config.VOLUME_CONFIRMATION_MULTIPLIER

    # RSI conditions with trend confirmation
    rsi_oversold = (df['RSI'] < config.RSI_OVERSOLD) & uptrend
    rsi_overbought = (df['RSI'] > config.RSI_OVERBOUGHT) & downtrend

    # MACD signals with volume confirmation
    macd_bullish = (df['MACD'] > df['Signal']) & (df['Histogram'] > 0) & volume_confirmation
    macd_bearish = (df['MACD'] < df['Signal']) & (df['Histogram'] < 0) & volume_confirmation

    # Combined signals using config parameters
    if config.TREND_CONFIRMATION_REQUIRED:
        bullish_signal = (uptrend & 
                         strong_trend & 
                         macd_bullish & 
                         (rsi_oversold | (df['RSI'] > df['RSI-based MA'])))
        
        bearish_signal = (downtrend & 
                         strong_trend & 
                         macd_bearish & 
                         (rsi_overbought | (df['RSI'] < df['RSI-based MA'])))
    else:
        bullish_signal = macd_bullish & (rsi_oversold | (df['RSI'] > df['RSI-based MA']))
        bearish_signal = macd_bearish & (rsi_overbought | (df['RSI'] < df['RSI-based MA']))

    # Apply signals
    signals[bullish_signal] = 1
    signals[bearish_signal] = -1

    logging.info("Signals generated.")
    return signals

def calculate_volatility(df):
    """Calculate historical volatility"""
    returns = np.log(df['close'] / df['close'].shift(1))
    return returns.rolling(window=config.VOLATILITY_WINDOW).std() * np.sqrt(252)

def calculate_position_size(balance, price, volatility):
    """Calculate position size based on risk parameters"""
    risk_amount = balance * config.RISK_PER_TRADE
    position_value = risk_amount / (config.STOP_LOSS_PERCENT / 100)
    position_size = min(
        position_value / price,
        config.MAX_POSITION_SIZE
    )
    return max(1, round(position_size))

def run_strategy():
    """Run the trading strategy and generate a report"""
    try:
        logger.info("Starting trading session...")
        
        # Load data
        logger.info("Loading data...")
        df = pd.read_csv(config.DATA_PATH)
        validate_data(df)
        
        # Prepare data
        df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y')
        df = df.sort_values('time')
        df['volatility'] = calculate_volatility(df)
        df['ATR'] = df['volatility'] * df['close']
        
        # Generate signals
        signals = generate_signals(df)
        logger.info(f"Generated {len(signals[signals != 0])} signals")
        
        # Check if signals are generated
        if signals.sum() == 0:
            logger.warning("No trading signals generated. Check data and conditions.")
            return
        
        # Initialize trading variables
        balance = config.INITIAL_BALANCE
        trades = []
        current_position = None
        trade_count = 0
        
        # Simulate trading
        for i in range(len(df)):
            current_row = df.iloc[i]
            signal = signals.iloc[i]
            
            # Exit existing position
            if current_position is not None:
                exit_price = current_row['close']
                pnl = (exit_price - current_position['entry_price']) * current_position['size']
                if current_position['direction'] == -1:
                    pnl = -pnl
                
                profit_target = current_position['entry_price'] * (1 + config.PROFIT_TARGET_PERCENT/100)
                stop_loss = current_position['entry_price'] * (1 - config.STOP_LOSS_PERCENT/100)
                
                if ((current_position['direction'] == 1 and 
                     (exit_price >= profit_target or exit_price <= stop_loss)) or
                    (current_position['direction'] == -1 and 
                     (exit_price <= profit_target or exit_price >= stop_loss))):
                    
                    balance += pnl
                    trade_data = {
                        'entry_price': current_position['entry_price'],
                        'exit_price': exit_price,
                        'profit': pnl
                    }
                    trades.append(trade_data)
                    
                    # Log trade exit
                    exit_reason = "Target Hit" if (
                        (current_position['direction'] == 1 and exit_price >= profit_target) or
                        (current_position['direction'] == -1 and exit_price <= profit_target)
                    ) else "Stop Loss"
                    log_trade_exit(trade_data, balance, exit_reason)
                    
                    current_position = None
                    trade_count += 1
            
            # Enter new position if conditions met
            elif signal != 0 and trade_count < config.MAX_TRADES_PER_DAY:
                position_size = calculate_position_size(
                    balance,
                    current_row['close'],
                    current_row['volatility']
                )
                
                current_position = {
                    'direction': signal,
                    'entry_price': current_row['close'],
                    'size': position_size
                }
                
                # Log trade entry
                log_trade_entry(current_position, balance)
        
        # Create trades DataFrame
        trades_df = pd.DataFrame(trades)
        
        # Generate and log trading summary
        log_trading_summary(config.INITIAL_BALANCE, balance, trades_df)
        logging.info("Trading summary:")
        print(trades_df)
        print(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
        print(f"Final Balance: ${balance:,.2f}")
        
        # Save detailed trade history if enabled
        if config.DETAILED_OUTPUT:
            trades_df.to_csv(log_dir / f"trade_history_{timestamp}.csv", index=False)
        
        logger.info("Trading session completed successfully.")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_strategy()

