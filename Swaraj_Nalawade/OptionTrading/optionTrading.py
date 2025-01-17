# main.py

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from config import DATA_CONFIG, TRADING_PARAMS, INDICATOR_PARAMS, REQUIRED_COLUMNS

def setup_logging():
    """Configure logging with custom format"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        filename=DATA_CONFIG["log_file"]
    )

def calculate_bollinger_bands(df):
    """Calculate Bollinger Bands for the given DataFrame"""
    window = INDICATOR_PARAMS["bollinger_window"]
    num_std = INDICATOR_PARAMS["bollinger_std"]
    
    df['Middle Band'] = df['close'].rolling(window=window).mean()
    df['Std Dev'] = df['close'].rolling(window=window).std()
    df['Upper Bollinger Band'] = df['Middle Band'] + (df['Std Dev'] * num_std)
    df['Lower Bollinger Band'] = df['Middle Band'] - (df['Std Dev'] * num_std)
    return df

def calculate_options_metrics(df):
    """Calculate additional options trading metrics"""
    # Calculate Bollinger Bands
    df = calculate_bollinger_bands(df)

    # Implied Volatility proxy
    df['price_change'] = df['close'].pct_change()
    df['IV_proxy'] = df['price_change'].rolling(window=INDICATOR_PARAMS["iv_window"]).std() * 100

    # Delta calculation
    delta_threshold = INDICATOR_PARAMS["delta_threshold"]
    df['delta'] = np.where(
        df['close'] > df['Upper Bollinger Band'], delta_threshold,
        np.where(
            df['close'] < df['Lower Bollinger Band'], -delta_threshold,
            0.5
        )
    )

    # Gamma calculation
    df['gamma'] = np.abs(df['delta']) * INDICATOR_PARAMS["gamma_multiplier"]

    # Strategy signals
    df['strategy_signal'] = np.where(
        (df['IV_proxy'] < INDICATOR_PARAMS["iv_low_threshold"]) & (df['delta'] > 0.5),
        'CALL_BUY',
        np.where(
            (df['IV_proxy'] < INDICATOR_PARAMS["iv_low_threshold"]) & (df['delta'] < -0.5),
            'PUT_BUY',
            np.where(
                (df['IV_proxy'] > INDICATOR_PARAMS["iv_high_threshold"]) & (df['delta'] > 0.5),
                'CALL_SELL',
                np.where(
                    (df['IV_proxy'] > INDICATOR_PARAMS["iv_high_threshold"]) & (df['delta'] < -0.5),
                    'PUT_SELL',
                    'HOLD'
                )
            )
        )
    )

    return df

def print_trading_summary(trades_df, initial_balance, final_balance):
    """Print detailed trading summary"""
    if len(trades_df) == 0:
        print("\nNo trades were executed.")
        return

    total_trades = len(trades_df)
    profitable_trades = len(trades_df[trades_df['profit'] > 0])
    win_rate = (profitable_trades / total_trades) * 100 if total_trades > 0 else 0
    total_profit = trades_df['profit'].sum()

    print("\n" + "="*50)
    print(f"{'OPTIONS TRADING SUMMARY':^50}")
    print("="*50)
    print(f"\nInitial Balance: ${initial_balance:,.2f}")
    print(f"Final Balance:   ${final_balance:,.2f}")
    print(f"Total Profit:    ${total_profit:,.2f}")
    print(f"Return:          {((final_balance - initial_balance) / initial_balance * 100):.2f}%")
    print(f"Total Trades:    {total_trades}")
    print(f"Win Rate:        {win_rate:.2f}%")
    print("="*50)

def run_options_trading_strategy():
    # Setup logging
    setup_logging()

    # Load and prepare data
    df = pd.read_csv(DATA_CONFIG["data_path"])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')
    
    # Ensure numeric columns
    numeric_columns = [col for col in REQUIRED_COLUMNS if col != 'time']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Calculate options metrics
    df = calculate_options_metrics(df)

    # Trading variables
    balance = TRADING_PARAMS["initial_balance"]
    position = None
    entry_price = None
    trade_history = []

    # Main trading loop
    for i in range(1, len(df)):
        current_time = df['time'].iloc[i]
        current_price = df['close'].iloc[i]
        strategy_signal = df['strategy_signal'].iloc[i]

        # Position management
        if position is None:
            # Entry logic
            if strategy_signal == 'CALL_BUY':
                trade_size = balance * TRADING_PARAMS["risk_per_trade"]
                position = 'CALL_LONG'
                entry_price = current_price
                shares = trade_size / current_price
                
                logging.info(f"CALL_BUY at {current_time}: Price {current_price}, Size {trade_size}")
                trade_history.append({
                    'type': 'CALL_LONG',
                    'entry_time': current_time,
                    'entry_price': entry_price,
                    'trade_size': trade_size
                })

            elif strategy_signal == 'PUT_BUY':
                trade_size = balance * TRADING_PARAMS["risk_per_trade"]
                position = 'PUT_LONG'
                entry_price = current_price
                shares = trade_size / current_price
                
                logging.info(f"PUT_BUY at {current_time}: Price {current_price}, Size {trade_size}")
                trade_history.append({
                    'type': 'PUT_LONG',
                    'entry_time': current_time,
                    'entry_price': entry_price,
                    'trade_size': trade_size
                })

        else:
            # Exit logic
            if position == 'CALL_LONG' and (strategy_signal in ['PUT_BUY', 'PUT_SELL'] or 
                                            current_price < entry_price * TRADING_PARAMS["stop_loss"]):
                profit = (current_price - entry_price) * shares
                balance += profit
                
                logging.info(f"CALL_EXIT at {current_time}: Price {current_price}, Profit {profit}")
                trade_history[-1].update({
                    'exit_time': current_time,
                    'exit_price': current_price,
                    'profit': profit
                })
                position = None

            elif position == 'PUT_LONG' and (strategy_signal in ['CALL_BUY', 'CALL_SELL'] or 
                                             current_price > entry_price * TRADING_PARAMS["take_profit"]):
                profit = (entry_price - current_price) * shares
                balance += profit
                
                logging.info(f"PUT_EXIT at {current_time}: Price {current_price}, Profit {profit}")
                trade_history[-1].update({
                    'exit_time': current_time,
                    'exit_price': current_price,
                    'profit': profit
                })
                position = None

    # Create trade history DataFrame and print summary
    trades_df = pd.DataFrame(trade_history)
    print_trading_summary(trades_df, TRADING_PARAMS["initial_balance"], balance)

    return balance, trades_df

if __name__ == "__main__":
    final_balance, trades = run_options_trading_strategy()
