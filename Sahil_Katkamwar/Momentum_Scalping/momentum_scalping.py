import pandas as pd
import logging

# Set up logging to log information to a file
logging.basicConfig(filename='momentum_strategy.log', level=logging.DEBUG,
                    format='%(message)s')

def calculate_indicators(df):
    """
    Calculate and verify technical indicators for momentum strategy
    """
    logging.info("Step 1: Calculating technical indicators...")

    # VWAP Calculation
    logging.info("Calculating VWAP...")
    df['Cum_Vol'] = df['Volume'].cumsum()
    df['Cum_Vol_Price'] = (df['Plot'] * df['Volume']).cumsum()
    df['VWAP'] = df['Cum_Vol_Price'] / df['Cum_Vol']

    # Volume Analysis
    logging.info("Calculating volume moving averages and ratios...")
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

    # Momentum and Volatility
    logging.info("Calculating price momentum and volatility...")
    df['Price_Momentum'] = df['Plot'].pct_change(periods=5) * 100
    df['ATR'] = calculate_atr(df)

    logging.info("Technical indicators calculated successfully.\n")
    return df


def calculate_atr(df, period=14):
    """
    Calculate Average True Range for volatility-based exits
    """
    logging.info(f"Calculating ATR with period {period}...")
    high = df['Plot'].rolling(window=2).max()
    low = df['Plot'].rolling(window=2).min()
    prev_close = df['Plot'].shift(1)

    tr = pd.DataFrame({
        'hl': high - low,
        'hc': abs(high - prev_close),
        'lc': abs(low - prev_close)
    }).max(axis=1)

    atr = tr.rolling(window=period).mean()
    logging.info("ATR calculation completed.\n")
    return atr


def identify_entry_signals(df, i, lookback=5):
    """
    Identify entry signals based on multiple confirmations
    Returns bullish and bearish signals with confidence levels
    """
    current_row = df.iloc[i]
    prev_rows = df.iloc[max(0, i - lookback):i]

    # Calculate trend strength
    price_trend = current_row['Plot'] - prev_rows['Plot'].mean()
    volume_trend = current_row['Volume_Ratio'] > prev_rows['Volume_Ratio'].mean()

    # Initialize scores
    bullish_score = 0
    bearish_score = 0

    # Bullish conditions
    if current_row['Plot'] > current_row['VWAP']:
        bullish_score += 2
        logging.info("Bullish: Price is above VWAP (+2)")

    if 30 < current_row['RSI'] < 70:
        bullish_score += 1
        logging.info("Bullish: RSI in healthy range (+1)")

    if current_row['MACD'] > current_row['Signal']:
        bullish_score += 2
        logging.info("Bullish: MACD is above Signal line (+2)")

    if current_row['Histogram'] > 0:
        bullish_score += 1
        logging.info("Bullish: MACD Histogram is positive (+1)")

    if current_row['Volume_Ratio'] > 1.2:
        bullish_score += 1
        logging.info("Bullish: Volume Ratio indicates high volume (+1)")

    if price_trend > 0 and volume_trend:
        bullish_score += 2
        logging.info("Bullish: Positive price and volume trend (+2)")

    # Bearish conditions
    if current_row['Plot'] < current_row['VWAP']:
        bearish_score += 2
        logging.info("Bearish: Price is below VWAP (+2)")

    if 30 < current_row['RSI'] < 70:
        bearish_score += 1
        logging.info("Bearish: RSI in healthy range (+1)")

    if current_row['MACD'] < current_row['Signal']:
        bearish_score += 2
        logging.info("Bearish: MACD is below Signal line (+2)")

    if current_row['Histogram'] < 0:
        bearish_score += 1
        logging.info("Bearish: MACD Histogram is negative (+1)")

    if current_row['Volume_Ratio'] > 1.2:
        bearish_score += 1
        logging.info("Bearish: Volume Ratio indicates high volume (+1)")

    if price_trend < 0 and volume_trend:
        bearish_score += 2
        logging.info("Bearish: Negative price and volume trend (+2)")

    # Log and print results
    logging.info(f"""
    Entry Signal Analysis:
    Current Price: {current_row['Plot']:.2f}
    VWAP: {current_row['VWAP']:.2f}
    RSI: {current_row['RSI']:.2f}
    MACD Histogram: {current_row['Histogram']:.4f}
    Volume Ratio: {current_row['Volume_Ratio']:.2f}
    Bullish Score: {bullish_score}/9
    Bearish Score: {bearish_score}/9
    """)

    return bullish_score >= 6, bearish_score >= 6


def calculate_exit_points(entry_price, position_type, atr, risk_factor=1.5):
    """
    Calculate stop loss and take profit levels
    """
    logging.info(f"Calculating exit points for {position_type} position...")
    atr_multiple = atr * risk_factor

    if position_type == "LONG":
        stop_loss = entry_price - atr_multiple
        take_profit = entry_price + (atr_multiple * 2)
    else:  # SHORT
        stop_loss = entry_price + atr_multiple
        take_profit = entry_price - (atr_multiple * 2)

    logging.info(f"Exit Points: Stop Loss={stop_loss:.2f}, Take Profit={take_profit:.2f}\n")
    return stop_loss, take_profit


def check_exit_signals(df, i, position_type, entry_price, stop_loss, take_profit):
    """
    Check comprehensive exit conditions for LONG and SHORT positions.
    """
    current_row = df.iloc[i]
    current_price = current_row['Plot']

    exit_signals = []

    if position_type == "LONG":
        # Price-based exits
        if current_price <= stop_loss:
            exit_signals.append(("Stop Loss", "High Priority"))
        elif current_price >= take_profit:
            exit_signals.append(("Take Profit", "High Priority"))

        # Technical indicator exits for LONG
        if current_row['RSI'] > 70:
            exit_signals.append(("RSI Overbought", "Medium Priority"))
        if current_row['MACD'] < current_row['Signal']:
            exit_signals.append(("MACD Reversal", "Medium Priority"))
        if current_price < current_row['VWAP']:
            exit_signals.append(("VWAP Breakdown", "Medium Priority"))

    else:  # SHORT position
        # Price-based exits
        if current_price >= stop_loss:
            exit_signals.append(("Stop Loss", "High Priority"))
        elif current_price <= take_profit:
            exit_signals.append(("Take Profit", "High Priority"))

        # Technical indicator exits for SHORT
        if current_row['RSI'] < 30:
            exit_signals.append(("RSI Oversold", "Medium Priority"))
        if current_row['MACD'] > current_row['Signal']:
            exit_signals.append(("MACD Reversal", "Medium Priority"))
        if current_price > current_row['VWAP']:
            exit_signals.append(("VWAP Breakout", "Medium Priority"))

    # Log exit signal analysis if any signals present
    if exit_signals:
        logging.info(f"""
        Exit Signal Analysis:
        Current Price: {current_price:.2f}
        Entry Price: {entry_price:.2f}
        Current P&L: {(current_price - entry_price) if position_type == "LONG" else (entry_price - current_price):.2f}
        Detected Signals: {exit_signals}
        """)

    # Return highest priority exit signal if any
    for signal, priority in exit_signals:
        if priority == "High Priority":
            return True, signal

    return bool(exit_signals), exit_signals[0][0] if exit_signals else None


def run_momentum_strategy(data_path, initial_balance=100000):
    """
    Execute momentum scalping strategy
    """
    logging.info(f"Starting Momentum Scalping Strategy with initial balance: ₹{initial_balance:,.2f}\n")

    # Load data
    logging.info("Loading data...")
    df = pd.read_csv(data_path)
    df = calculate_indicators(df)

    # Trading Variables
    balance = initial_balance
    position = None
    entry_price = None
    trades = []

    # Risk Management
    logging.info("Starting trading simulation...\n")
    for i in range(20, len(df)):
        current_price = df.iloc[i]['Plot']

        if position is None:  # Searching for entry
            bullish_signal, bearish_signal = identify_entry_signals(df, i)

            if bullish_signal:
                position = "LONG"
                entry_price = current_price
                stop_loss, take_profit = calculate_exit_points(entry_price, position, df.iloc[i]['ATR'])
                logging.info(f"Entered LONG at price {entry_price:.2f}.\n")

            elif bearish_signal:
                position = "SHORT"
                entry_price = current_price
                stop_loss, take_profit = calculate_exit_points(entry_price, position, df.iloc[i]['ATR'])
                logging.info(f"Entered SHORT at price {entry_price:.2f}.\n")

        else:  # Managing position
            should_exit, exit_reason = check_exit_signals(df, i, position, entry_price, stop_loss, take_profit)

            if should_exit:
                profit = (current_price - entry_price) if position == "LONG" else (entry_price - current_price)
                balance += profit
                trades.append({
                    'entry_price': entry_price,
                    'exit_price': current_price,
                    'position': position,
                    'profit': profit
                })

                logging.info(f"Exited {position} at price {current_price:.2f} with profit/loss: ₹{profit:.2f}\n")
                position = None

    logging.info("Trading simulation complete.\n")

    # Summary
    logging.info(f"Final Balance: ₹{balance:,.2f}")
    logging.info(f"Total Trades: {len(trades)}")
    if trades:
        total_profit = sum([t['profit'] for t in trades])
        logging.info(f"Total Profit: ₹{total_profit:,.2f}\n")

    return trades, balance


if __name__ == "__main__":
    DATA_PATH = "./NSE_NIFTY, 1 Intraday.csv"
    trades, final_balance = run_momentum_strategy(DATA_PATH)
