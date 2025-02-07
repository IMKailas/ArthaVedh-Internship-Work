# gamma_scalping.py

import pandas as pd
import numpy as np
from datetime import datetime
import math
import config
import talib

def load_market_data(csv_file):
    """Load and preprocess the CSV data, calculate indicators using TA-Lib"""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'])
    
    # Calculate RSI using TA-Lib
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    
    # Calculate VWAP (Custom, not directly available in TA-Lib)
    df['VWAP'] = (df['close'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # Calculate Bollinger Bands (Upper and Lower Bands) using TA-Lib
    df['Upper Band #1'], df['Middle Band'], df['Lower Band #1'] = talib.BBANDS(df['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    
    # Delta (still calculated manually as per your previous formula)
    df['delta'] = 0.5 + (df['RSI'] - 50) / 100  # Delta between 0 and 1
    
    # Gamma (Adjusted for proximity to VWAP as before)
    df['gamma'] = 0.05 * np.exp(-(df['close'] - df['VWAP'])**2 / (100**2))
    
    # Vega (Adjusted for price level)
    df['vega'] = abs(df['Upper Band #1'] - df['Lower Band #1']) / df['close']
    
    print("\nData Overview:")
    print(f"Total rows: {len(df)}")
    print("\nSample of loaded data with Greeks:")
    print(df.head(1).to_string())
    return df

def get_market_data(df, current_index):
    """Get market data including Greeks from DataFrame"""
    if current_index >= len(df):
        return None
    
    current_row = df.iloc[current_index]
    
    market_data = {
        "price": current_row['close'],
        "volume": current_row['Volume'],
        "delta": current_row['delta'],
        "gamma": current_row['gamma'],
        "vega": current_row['vega'],
        "timestamp": current_row['time'],
        "vwap": current_row['VWAP'],
        "upper_band": current_row['Upper Band #1'],
        "lower_band": current_row['Lower Band #1']
    }
    return market_data

def gamma_scalping_decision(market_data, position=None, hedge_ratio=0, entry_price=None):
    """Enhanced decision making with better risk management and profit targets"""
    if position is None:
        # Entry conditions with stricter criteria
        high_gamma = market_data["gamma"] > config.GAMMA_ENTRY_THRESHOLD
        near_vwap = abs(market_data["price"] - market_data["vwap"]) < market_data["price"] * config.VWAP_ENTRY_THRESHOLD
        acceptable_vega = market_data["vega"] < config.VEGA_ENTRY_THRESHOLD
        min_volume = market_data["volume"] > market_data.get("Volume MA", 0)  # Volume confirmation
        
        if high_gamma and near_vwap and acceptable_vega and min_volume:
            return "Buy", market_data["delta"]
            
    else:
        # Calculate current P&L if in position
        if entry_price:
            price_change = market_data["price"] - entry_price
            option_pnl = price_change * market_data["gamma"] * config.GAMMA_POSITION_MULTIPLIER
            hedge_pnl = -hedge_ratio * price_change
            total_pnl = option_pnl + hedge_pnl
            
            # Take profit or stop loss check
            if total_pnl > entry_price * config.TAKE_PROFIT_THRESHOLD or total_pnl < entry_price * config.STOP_LOSS_THRESHOLD:
                return "Exit", -hedge_ratio
        
        # Exit conditions
        low_gamma = market_data["gamma"] < config.GAMMA_EXIT_THRESHOLD
        high_vega = market_data["vega"] > config.VEGA_EXIT_THRESHOLD
        price_far_from_vwap = abs(market_data["price"] - market_data["vwap"]) > market_data["price"] * config.VWAP_EXIT_THRESHOLD
        
        if low_gamma or high_vega or price_far_from_vwap:
            return "Exit", -hedge_ratio
        
        # Hedge adjustment with tighter control
        current_delta = market_data["delta"]
        hedge_adjustment = current_delta - hedge_ratio
        
        if abs(hedge_adjustment) > config.HEDGE_ADJUSTMENT_THRESHOLD:
            return "Adjust", hedge_adjustment
            
    return "Hold", 0

def run_gamma_scalping(csv_file, initial_balance, risk_per_trade=0.02):
    print(f"Starting gamma scalping strategy with {initial_balance} initial balance")
    print(f"Risk per trade: {risk_per_trade * 100}% of balance")
    
    df = load_market_data(csv_file)
    
    balance = initial_balance
    position = None
    hedge_ratio = 0
    entry_price = None
    entry_time = None
    trades = []
    current_index = config.MIN_LOOKBACK  # Start after indicators have enough data
    
    # Create log file
    log_filename = f"{config.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{datetime.now()} - {message}\n")
        print(message)
    
    while current_index < len(df):
        market_data = get_market_data(df, current_index)
        if market_data is None:
            break
            
        current_price = market_data["price"]
        
        # Get decision and hedge adjustment with current position info
        decision, hedge_adjust = gamma_scalping_decision(
            market_data, 
            position, 
            hedge_ratio,
            entry_price
        )
        
        # Position management with improved P&L calculation
        if position is not None:
            price_change = current_price - entry_price
            option_pnl = price_change * market_data["gamma"] * config.GAMMA_POSITION_MULTIPLIER
            hedge_pnl = -hedge_ratio * price_change
            total_pnl = option_pnl + hedge_pnl
            
            # Add position sizing based on risk
            position_size = (initial_balance * risk_per_trade) / (current_price * market_data["gamma"])
            total_pnl *= position_size
            
            if decision in ["Exit", "Adjust"]:
                if decision == "Exit":
                    # Close position
                    balance += total_pnl
                    
                    trade_info = {
                        'entry_time': entry_time,
                        'exit_time': market_data['timestamp'],
                        'type': 'Gamma Scalp',
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'hedge_ratio': hedge_ratio,
                        'final_gamma': market_data["gamma"],
                        'final_vega': market_data["vega"],
                        'option_pnl': option_pnl,
                        'hedge_pnl': hedge_pnl,
                        'total_pnl': total_pnl
                    }
                    trades.append(trade_info)
                    
                    log_trade(f"\nClosed gamma scalping position:")
                    log_trade(f"Entry: {entry_price:.2f}, Exit: {current_price:.2f}")
                    log_trade(f"Option P&L: {option_pnl:.2f}, Hedge P&L: {hedge_pnl:.2f}")
                    log_trade(f"Total P&L: {total_pnl:.2f}, New Balance: {balance:.2f}")
                    
                    position = None
                    hedge_ratio = 0
                    entry_price = None
                    entry_time = None
                    
                elif decision == "Adjust":
                    # Adjust hedge
                    old_hedge = hedge_ratio
                    hedge_ratio += hedge_adjust
                    log_trade(f"\nAdjusted hedge ratio from {old_hedge:.2f} to {hedge_ratio:.2f}")
        
        # New entry with position sizing
        elif decision == "Buy":
            position = "Long Gamma"
            entry_price = current_price
            entry_time = market_data['timestamp']
            hedge_ratio = hedge_adjust
            
            # Calculate position size based on risk
            position_size = (initial_balance * risk_per_trade) / (current_price * market_data["gamma"])
            
            log_trade(f"\nOpened gamma scalping position at {entry_price:.2f}")
            log_trade(f"Position size: {position_size:.2f}")
            log_trade(f"Initial hedge ratio: {hedge_ratio:.2f}")
            log_trade(f"Initial gamma: {market_data['gamma']:.4f}")
            log_trade(f"Initial vega: {market_data['vega']:.4f}")
        
        current_index += 1
    
    # Close any remaining position at the end
    if position is not None:
        final_price = df.iloc[-1]['close']
        final_market_data = get_market_data(df, -1)
        
        option_pnl = (final_price - entry_price) * final_market_data["gamma"] * 100
        hedge_pnl = -hedge_ratio * (final_price - entry_price)
        total_pnl = option_pnl + hedge_pnl
        
        balance += total_pnl
        trades.append({
            'entry_time': entry_time,
            'exit_time': final_market_data['timestamp'],
            'type': 'Gamma Scalp',
            'entry_price': entry_price,
            'exit_price': final_price,
            'hedge_ratio': hedge_ratio,
            'final_gamma': final_market_data["gamma"],
            'final_vega': final_market_data["vega"],
            'option_pnl': option_pnl,
            'hedge_pnl': hedge_pnl,
            'total_pnl': total_pnl,
            'status': 'Market Close'
        })
    
    # Create summary report
    trades_df = pd.DataFrame(trades)
    trades_df.to_csv(f"{config.TRADE_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    print("\nTrading Summary:")
    print(f"Initial Balance: {initial_balance:.2f}")
    print(f"Final Balance: {balance:.2f}")
    print(f"Total P&L: {balance - initial_balance:.2f}")
    print(f"Total Trades: {len(trades)}")
    
    if len(trades) > 0:
        trades_df['total_pnl'] = trades_df['total_pnl'].astype(float)
        profit_trades = trades_df[trades_df['total_pnl'] > 0]
        loss_trades = trades_df[trades_df['total_pnl'] < 0]
        
        print(f"Profitable Trades: {len(profit_trades)}")
        print(f"Loss-making Trades: {len(loss_trades)}")
        if len(profit_trades) > 0:
            print(f"Average Profit per winning trade: {profit_trades['total_pnl'].mean():.2f}")
        if len(loss_trades) > 0:
            print(f"Average Loss per losing trade: {loss_trades['total_pnl'].mean():.2f}")
        
        print("\nGreeks Analysis:")
        print(f"Average Entry Gamma: {trades_df['final_gamma'].mean():.4f}")
        print(f"Average Entry Vega: {trades_df['final_vega'].mean():.4f}")
        print(f"Average Hedge Ratio: {trades_df['hedge_ratio'].mean():.2f}")
    
    return balance, trades

if __name__ == "__main__":
    final_balance, trades = run_gamma_scalping(
        config.DATA_PATH,
        config.INITIAL_BALANCE,
        config.RISK_PER_TRADE
    )