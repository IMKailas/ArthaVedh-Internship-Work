import pandas as pd
import os
from datetime import datetime
import config_QuantitativeTrading as config
import talib

def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Quantitative_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_market_data(file_path):
    try:
        data = pd.read_csv(file_path)
        if config.ENABLE_DEBUG_LOGGING:
            print(f"Data loaded successfully from {file_path}")
        
        # Calculate indicators using TA-Lib
        data['RSI'] = talib.RSI(data['close'], timeperiod=14)  # 14-period RSI
        data['MACD'], data['Signal'], _ = talib.MACD(data['close'], fastperiod=12, slowperiod=26, signalperiod=9)  # MACD
        data['Upper Bollinger Band'], data['Middle Bollinger Band'], data['Lower Bollinger Band'] = talib.BBANDS(data['close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)  # Bollinger Bands
        data['Volume_MA'] = talib.SMA(data['Volume'], timeperiod=14)  # Volume Moving Average
        
        return data
    except FileNotFoundError:
        log_error(f"Error: File not found at {file_path}")
        raise

def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    with open(log_filename, 'a') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

def quantitative_decision(row, rsi_overbought, rsi_oversold, volume_ma):
    macd = row['MACD']
    signal = row['Signal']
    rsi = row['RSI']
    price = row['close']
    volume = row['Volume']
    upper_band = row['Upper Bollinger Band']
    lower_band = row['Lower Bollinger Band']

    # Build reasoning components
    reasoning = []
    
    # Volume analysis
    volume_status = "High" if volume > volume_ma else "Low"
    reasoning.append(f"Volume: {volume:,} vs MA: {volume_ma:,} ({volume_status})")
    
    # MACD analysis
    macd_diff = macd - signal
    macd_status = "Bullish" if macd_diff > 0 else "Bearish"
    reasoning.append(f"MACD: {macd:.2f} vs Signal: {signal:.2f} ({macd_status})")
    
    # RSI analysis
    if rsi < rsi_oversold:
        rsi_status = "Oversold"
    elif rsi > rsi_overbought:
        rsi_status = "Overbought"
    else:
        rsi_status = "Normal"
    reasoning.append(f"RSI: {rsi:.2f} ({rsi_status})")
    
    # Bollinger Bands analysis
    bb_status = "Below Lower Band" if price < lower_band else "Above Upper Band" if price > upper_band else "Within Bands"
    reasoning.append(f"Price: {price:.2f} ({bb_status})")

    # Combine reasoning
    full_reasoning = " | ".join(reasoning)

    if rsi < rsi_oversold and volume > volume_ma:
        return "Buy", full_reasoning
    return "Hold", full_reasoning

def run_quantitative_strategy(data, initial_balance, stop_loss_pct, target_profit_pct, rsi_oversold, rsi_overbought, volume_ma):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"quantitative_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        print(message)

    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    # Enhanced Trading Initialization Logs
    log_trade(f"===========================================")
    log_trade(f"  Quantitative Trading Strategy Started")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    log_trade(f"RSI Parameters - Oversold: {rsi_oversold}, Overbought: {rsi_overbought}")
    log_trade(f"Volume MA Threshold: {volume_ma:,}")

    for index, row in data.iterrows():
        current_price = row['close']
        timestamp = pd.Timestamp(row['time']) if 'time' in row else pd.Timestamp.now()

        if position is None:
            decision, reasoning = quantitative_decision(row, rsi_overbought, rsi_oversold, volume_ma)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                trade_entry_reason = reasoning
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")

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
                    'entry_reasoning': trade_entry_reason
                }
                trades.append(trade_info)

                log_trade(f"\n===========================================")
                log_trade(f"Closed {position} position: {exit_reason}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
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
                trade_entry_reason = None

        if balance <= initial_balance * 0.7:
            log_trade(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    # Close any remaining position at the end
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
            'entry_reasoning': trade_entry_reason
        })

        log_trade(f"\n===========================================")
        log_trade(f"Closed remaining position at market close.")
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
            log_trade(f"Average Profit per Winning Trade: {profit_trades['profit'].mean():.2f}")
            log_trade(f"Largest Winning Trade: {profit_trades['profit'].max():.2f}")
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per Losing Trade: {loss_trades['profit'].mean():.2f}")
            log_trade(f"Largest Losing Trade: {loss_trades['profit'].min():.2f}")

        # Performance Metrics
        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")
        
        if len(profit_trades) > 0 and len(loss_trades) > 0:
            profit_factor = abs(profit_trades['profit'].sum() / loss_trades['profit'].sum())
            log_trade(f"Profit Factor: {profit_factor:.2f}")
    
    log_trade("\n===========================================")
    return balance, trades

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), './Quantitative_Trading/NSE_NIFTY, 1 Intraday.csv')
    
    try:
        data = load_market_data(file_path)
        final_balance, trades = run_quantitative_strategy(
            data,
            initial_balance=config.initial_balance,
            stop_loss_pct=config.stop_loss_pct,
            target_profit_pct=config.target_profit_pct,
            rsi_oversold=config.rsi_oversold,
            rsi_overbought=config.rsi_overbought,
            volume_ma=config.volume_ma
        )
    except FileNotFoundError:
        print(f"File not found: {file_path}")