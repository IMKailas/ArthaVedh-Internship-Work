import pandas as pd
import numpy as np

def load_market_data(csv_file):
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y')
    
    # Advanced technical indicators
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    df['RSI'] = compute_rsi(df['close'])
    df['Volume_MA'] = df['volume'].rolling(window=20).mean()
    
    # More sophisticated Bollinger Bands
    rolling_window = 20
    rolling_mean = df['close'].rolling(window=rolling_window).mean()
    rolling_std = df['close'].rolling(window=rolling_window).std()
    
    df['Upper_BB'] = rolling_mean + (2.5 * rolling_std)
    df['Lower_BB'] = rolling_mean - (2.5 * rolling_std)
    
    return df

def compute_rsi(price, periods=14):
    delta = price.diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    
    rs = gain / loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50)

def advanced_mean_reversion_decision(market_data, position=None):
    close = market_data['close']
    rsi = market_data['rsi']
    sma_50 = market_data['sma_50']
    sma_200 = market_data['sma_200']
    volume = market_data['volume']
    volume_ma = market_data['volume_ma']
    upper_bb = market_data['upper_bb']
    lower_bb = market_data['lower_bb']
    
    # More sophisticated entry and exit conditions
    if position is None:
        # Strict entry conditions with multiple confirmations
        buy_conditions = (
            rsi < 30 and  # Oversold
            close < lower_bb and  # Below lower Bollinger Band
            close < sma_50 and  # Below short-term moving average
            close < sma_200 and  # Below long-term moving average
            volume > volume_ma * 1.5  # High volume confirmation
        )
        
        sell_conditions = (
            rsi > 70 and  # Overbought
            close > upper_bb and  # Above upper Bollinger Band
            close > sma_50 and  # Above short-term moving average
            close > sma_200 and  # Above long-term moving average
            volume > volume_ma * 1.5  # High volume confirmation
        )
        
        if buy_conditions:
            return "BUY", close
        elif sell_conditions:
            return "SELL", close
    
    else:
        # More nuanced exit conditions
        if position['type'] == "BUY":
            exit_buy = (
                rsi > 70 or  # Overbought
                close > sma_50 or  # Price above short-term MA
                close > position['entry_price'] * 1.02  # 2% profit target
            )
            if exit_buy:
                return "EXIT", close
        
        elif position['type'] == "SELL":
            exit_sell = (
                rsi < 30 or  # Oversold
                close < sma_50 or  # Price below short-term MA
                close < position['entry_price'] * 0.98  # 2% profit target
            )
            if exit_sell:
                return "EXIT", close
    
    return "HOLD", close

def run_advanced_mean_reversion_strategy(csv_file, initial_balance, 
                                         stop_loss_pct=2.0, 
                                         target_profit_pct=3.0, 
                                         max_loss_pct=5.0):
    df = load_market_data(csv_file)
    balance = initial_balance
    position = None
    trades = []
    
    trade_allocation = 0.1  # 10% of balance per trade
    max_simultaneous_trades = 3
    active_trades = 0
    
    for i in range(len(df)):
        market_data = {
            "close": df.iloc[i]['close'],
            "volume": df.iloc[i]['volume'],
            "rsi": df.iloc[i]['RSI'],
            "sma_50": df.iloc[i]['SMA_50'],
            "sma_200": df.iloc[i]['SMA_200'],
            "volume_ma": df.iloc[i]['Volume_MA'],
            "upper_bb": df.iloc[i]['Upper_BB'],
            "lower_bb": df.iloc[i]['Lower_BB'],
            "time": df.iloc[i]['time']
        }
        
        if position and active_trades < max_simultaneous_trades:
            # Risk management: dynamic stop-loss and take-profit
            current_profit_pct = abs(market_data['close'] - position['entry_price']) / position['entry_price'] * 100
            
            if current_profit_pct >= target_profit_pct or current_profit_pct >= max_loss_pct:
                position['rsi'] = 50  # Force exit
        
        decision, price = advanced_mean_reversion_decision(market_data, position)
        
        trade_size = balance * trade_allocation
        
        if decision == "BUY" and position is None and active_trades < max_simultaneous_trades:
            position = {
                'type': "BUY",
                'entry_price': price,
                'trade_size': trade_size,
                'stop_loss': price * (1 - stop_loss_pct / 100),
                'target_profit': price * (1 + target_profit_pct / 100)
            }
            active_trades += 1
        
        elif decision == "SELL" and position is None and active_trades < max_simultaneous_trades:
            position = {
                'type': "SELL",
                'entry_price': price,
                'trade_size': trade_size,
                'stop_loss': price * (1 + stop_loss_pct / 100),
                'target_profit': price * (1 - target_profit_pct / 100)
            }
            active_trades += 1
        
        elif decision == "EXIT" and position is not None:
            profit = (price - position['entry_price']) * (position['trade_size'] / price) if position['type'] == "BUY" else (position['entry_price'] - price) * (position['trade_size'] / price)
            balance += profit
            
            trades.append({
                'position': position['type'],
                'entry_price': position['entry_price'],
                'exit_price': price,
                'profit': profit,
                'timestamp': market_data['time']
            })
            
            position = None
            active_trades -= 1
    
    # Performance analysis
    net_profit = balance - initial_balance
    win_trades = [trade for trade in trades if trade['profit'] > 0]
    loss_trades = [trade for trade in trades if trade['profit'] <= 0]
    win_rate = len(win_trades) / len(trades) if trades else 0
    avg_win = np.mean([trade['profit'] for trade in win_trades]) if win_trades else 0
    avg_loss = np.mean([trade['profit'] for trade in loss_trades]) if loss_trades else 0
    
    print(f"\nFinal Balance: {balance:.2f}")
    print(f"Net Profit: {net_profit:.2f}")
    print(f"Total Trades: {len(trades)}")
    print(f"Win Rate: {win_rate * 100:.2f}%")
    print(f"Average Win: {avg_win:.2f}")
    print(f"Average Loss: {avg_loss:.2f}")
    print(f"Profit Factor: {abs(avg_win/avg_loss) if avg_loss != 0 else 'N/A'}")
    
    return balance, trades

# Example usage
if __name__ == "__main__":
    csv_file = "NSE_NIFTY, 1D.csv"  # Replace with your CSV path
    initial_balance = 10000
    
    final_balance, trades = run_advanced_mean_reversion_strategy(
        csv_file, 
        initial_balance, 
        stop_loss_pct=2.0,   # 2% stop loss
        target_profit_pct=3.0,  # 3% target profit
        max_loss_pct=5.0  # Maximum total loss percentage
    )