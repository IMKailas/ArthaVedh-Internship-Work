import pandas as pd
import time
import os
from datetime import datetime
import config_MicroFuturesTrading

def create_log_directory():
    log_dir = os.path.join(os.getcwd(), './Micro_Futures_Trading/logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_market_data(csv_file):
    try:
        data = pd.read_csv(filepath_or_buffer=csv_file)
        return data
    except FileNotFoundError:
        error_msg = f"Error: File not found at {csv_file}"
        log_error(error_msg)
        raise

def log_error(message):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, "error_log.txt")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_filename, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")

def micro_futures_decision(row, position, entry_made):
    volume = row["Volume"]
    min_volume = config_MicroFuturesTrading.min_volume
    
    # Build detailed reasoning components
    reasoning = []
    reasoning.append(f"Volume: {volume} ({['Insufficient', 'Sufficient'][volume >= min_volume]})")
    reasoning.append(f"RSI: {row['RSI']:.2f}")
    reasoning.append(f"Position: {position if position else 'None'}")
    reasoning.append(f"Entry Status: {'Entry Made' if entry_made else 'No Entry'}")
    
    # Combine reasoning
    full_reasoning = " | ".join(reasoning)

    if config_MicroFuturesTrading.ENABLE_DEBUG_LOGGING:
        print(f"\nAnalyzing conditions:")
        print(full_reasoning)

    if position is None and not entry_made and volume >= min_volume:
        if row['RSI'] < config_MicroFuturesTrading.rsi_threshold: 
            return "Buy", full_reasoning

    return "Hold", full_reasoning

def run_micro_futures_strategy(csv_file, initial_balance, leverage, stop_loss_pct, target_profit_pct):
    log_dir = create_log_directory()
    log_filename = os.path.join(log_dir, f"microfutures_trading_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    def log_trade(message):
        with open(log_filename, 'a') as f:
            f.write(f"{message}\n")
        print(message)

    data = load_market_data(csv_file)
    balance = initial_balance
    position = None
    trade_price = None
    stop_loss = None
    target_profit = None
    entry_made = False
    trade_entry_time = None
    trade_entry_reason = None
    trades = []

    log_trade(f"===========================================")
    log_trade(f"  Micro Futures Trading Strategy Started  ")
    log_trade(f"===========================================")
    log_trade(f"Initial Balance: {balance:.2f}")
    log_trade(f"Leverage: {leverage}x")
    log_trade(f"Stop Loss Percentage: {stop_loss_pct}%")
    log_trade(f"Target Profit Percentage: {target_profit_pct}%")
    log_trade(f"Minimum Volume: {config_MicroFuturesTrading.min_volume}")
    log_trade(f"RSI Threshold: {config_MicroFuturesTrading.rsi_threshold}")

    for index, row in data.iterrows():
        current_price = row["close"]
        timestamp = pd.Timestamp(row['time'])

        if position is None:
            decision, reasoning = micro_futures_decision(row, position, entry_made)

            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                trade_entry_time = timestamp
                trade_entry_reason = reasoning
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                entry_made = True
                
                log_trade(f"\nOpened {position} position at {trade_price:.2f}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Stop Loss: {stop_loss:.2f}, Target Profit: {target_profit:.2f}")
                log_trade(f"Entry Time: {trade_entry_time}")

        if position == "Buy":
            if current_price <= stop_loss or current_price >= target_profit:
                profit = (current_price - trade_price) * leverage
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
                    'leverage': leverage,
                    'entry_reasoning': trade_entry_reason
                }
                trades.append(trade_info)

                log_trade(f"\n===========================================")
                log_trade(f"Closed {position} position: {exit_reason}")
                log_trade(f"Entry Reasoning: {trade_entry_reason}")
                log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {current_price:.2f}")
                log_trade(f"Profit/Loss (with {leverage}x leverage): {profit:.2f}")
                log_trade(f"New Balance: {balance:.2f}")
                log_trade(f"Exit Time: {timestamp}")
                log_trade(f"===========================================")
                
                position = None
                trade_price = None
                stop_loss = None
                target_profit = None
                trade_entry_time = None
                trade_entry_reason = None
                entry_made = False

        if balance <= initial_balance * 0.7:
            log_trade(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    if position is not None:
        final_price = data.iloc[-1]['close']
        profit = (final_price - trade_price) * leverage
        balance += profit
        trades.append({
            'entry_time': trade_entry_time,
            'exit_time': timestamp,
            'type': position,
            'entry_price': trade_price,
            'exit_price': final_price,
            'status': 'Market Close',
            'profit': profit,
            'leverage': leverage,
            'entry_reasoning': trade_entry_reason
        })

        log_trade(f"\n===========================================")
        log_trade(f"Closed remaining position at market close")
        log_trade(f"Entry Reasoning: {trade_entry_reason}")
        log_trade(f"Entry Price: {trade_price:.2f}, Exit Price: {final_price:.2f}")
        log_trade(f"Profit/Loss (with {leverage}x leverage): {profit:.2f}")
        log_trade(f"Final Balance: {balance:.2f}")
        log_trade(f"===========================================")

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
        if len(loss_trades) > 0:
            log_trade(f"Average Loss per Losing Trade: {loss_trades['profit'].mean():.2f}")

        win_rate = len(profit_trades) / len(trades) * 100
        log_trade(f"Win Rate: {win_rate:.2f}%")

        log_trade(f"\nLeverage-specific Metrics:")
        log_trade(f"Maximum Drawdown: {trades_df['profit'].min():.2f}")
        log_trade(f"Largest Profit: {trades_df['profit'].max():.2f}")
        log_trade(f"Average Leverage Used: {trades_df['leverage'].mean():.2f}x")
    
    log_trade("\n===========================================")
    return balance, trades

if __name__ == "__main__":
    csv_file = os.path.join(os.getcwd(), './Momentum_Trading/NSE_NIFTY, 1 Intraday.csv')
    
    try:
        initial_balance = config_MicroFuturesTrading.initial_balance
        leverage = config_MicroFuturesTrading.leverage
        stop_loss_pct = config_MicroFuturesTrading.stop_loss_pct
        target_profit_pct = config_MicroFuturesTrading.target_profit_pct
        
        final_balance, trades = run_micro_futures_strategy(
            csv_file, 
            initial_balance, 
            leverage, 
            stop_loss_pct, 
            target_profit_pct
        )
    except FileNotFoundError:
        print(f"File not found: {csv_file}")