import pandas as pd
import os

# Load CSV data
def load_market_data(file_path):
    data = pd.read_csv(file_path)
    return data

# Quantitative decision logic with the updated columns
def quantitative_decision(row, rsi_overbought, rsi_oversold, volume_ma):
    macd = row['MACD']
    signal = row['Signal']
    rsi = row['RSI']
    price = row['close']
    volume = row['Volume']
    upper_band = row['Upper Bollinger Band']
    lower_band = row['Lower Bollinger Band']

    # Trading decision logic based on available indicators
    if rsi < rsi_oversold and macd > signal and price < lower_band and volume > volume_ma:
        return "Buy"  # Strong Buy signal based on oversold condition, MACD, Bollinger Bands, and volume confirmation
    elif rsi > rsi_overbought and macd < signal and price > upper_band and volume < volume_ma:
        return "Sell"  # Strong Sell signal based on overbought condition, MACD, Bollinger Bands, and volume confirmation

    return "Hold"  # No strong indication to trade

# Run quantitative strategy with customizable parameters
def run_quantitative_strategy(data, initial_balance, stop_loss_pct, target_profit_pct, rsi_oversold, rsi_overbought, volume_ma):
    balance = initial_balance
    position = None  # "Buy" or "Sell" position
    trade_price = None  # Entry price for the current trade
    stop_loss = None  # Stop loss price
    target_profit = None  # Target profit price

    print(f"Starting Quantitative Strategy with Initial Balance: {balance}\n")

    for index, row in data.iterrows():
        current_price = row['close']
        rsi = row['RSI']
        macd = row['MACD']
        signal = row['Signal']
        volume = row['Volume']
        upper_band = row['Upper Bollinger Band']
        lower_band = row['Lower Bollinger Band']

        # Log current market data
        print(f"Minute {index + 1}: Price={current_price:.2f}, Volume={volume}, MACD={macd:.2f}, Signal={signal:.2f}, RSI={rsi:.2f}")

        # Check if we should enter a position
        if position is None:
            decision = quantitative_decision(row, rsi_overbought, rsi_oversold, volume_ma)
            if decision == "Buy":
                position = "Buy"
                trade_price = current_price
                stop_loss = trade_price * (1 - stop_loss_pct / 100)
                target_profit = trade_price * (1 + target_profit_pct / 100)
                print(f"Entering Buy at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")
            elif decision == "Sell":
                position = "Sell"
                trade_price = current_price
                stop_loss = trade_price * (1 + stop_loss_pct / 100)  # Reverse stop loss for sell
                target_profit = trade_price * (1 - target_profit_pct / 100)  # Reverse target profit for sell
                print(f"Entering Sell at {trade_price:.2f} with Stop Loss at {stop_loss:.2f} and Target Profit at {target_profit:.2f}")

        # If in a position, check exit conditions
        if position == "Buy":
            if current_price <= stop_loss:
                print(f"Stop Loss hit! Exiting Buy trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss
                position = None
            elif current_price >= target_profit:
                print(f"Target Profit reached! Exiting Buy trade at {current_price:.2f}")
                balance += (current_price - trade_price)  # Add profit
                position = None

        if position == "Sell":
            if current_price >= stop_loss:
                print(f"Stop Loss hit! Exiting Sell trade at {current_price:.2f}")
                balance += (trade_price - current_price)  # Add profit (since selling short)
                position = None
            elif current_price <= target_profit:
                print(f"Target Profit reached! Exiting Sell trade at {current_price:.2f}")
                balance -= (trade_price - current_price)  # Deduct loss (since selling short)
                position = None

        # Risk management: stop trading if balance drops significantly
        if balance <= initial_balance * 0.7:
            print(f"Balance dropped below 70% of initial value. Stopping strategy.")
            break

    print(f"Final Balance: {balance:.2f}")

# Correct the file path using os.path
file_path = os.path.join(os.getcwd(), './Quantitative_Trading/NSE_NIFTY, 1 Intraday.csv')

# Define your parameters here
params = {
    'initial_balance': 10000,
    'stop_loss_pct': 0.1,
    'target_profit_pct': 1,
    'rsi_oversold': 30,  # RSI oversold threshold
    'rsi_overbought': 70,  # RSI overbought threshold
    'volume_ma': 1000000  # Moving average of volume (volume moving average threshold)
}

# Run strategy with data
try:
    data = load_market_data(file_path)
    run_quantitative_strategy(
        data,
        initial_balance=params['initial_balance'],
        stop_loss_pct=params['stop_loss_pct'],
        target_profit_pct=params['target_profit_pct'],
        rsi_oversold=params['rsi_oversold'],
        rsi_overbought=params['rsi_overbought'],
        volume_ma=params['volume_ma']
    )
except FileNotFoundError:
    print(f"File not found: {file_path}")
