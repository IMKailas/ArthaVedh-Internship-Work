import pandas as pd

def load_market_data(csv_file):
    """Load and preprocess the CSV data for swing trading."""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    return df


def get_market_data(df, current_index):
    """Get market data for the current index from DataFrame."""
    if current_index >= len(df):
        return None

    current_row = df.iloc[current_index]

    market_data = {
        "close_price": current_row['close'],  # Closing price
        "volume": current_row['Volume'],  # Current volume
        "volume_ma": current_row['Volume MA'],  # Moving average of volume
        "rsi": current_row['RSI'],  # RSI value
        "macd": current_row['MACD'],  # MACD value
        "signal": current_row['Signal'],  # MACD signal line
        "upper_band": current_row['Upper Band #1'],  # Bollinger upper band
        "lower_band": current_row['Lower Band #1'],  # Bollinger lower band
        "timestamp": current_row['time'],  # Timestamp
    }
    return market_data


def swing_trading_decision(market_data, position=None, entry_price=0.0):
    close_price = market_data['close_price']
    rsi = market_data['rsi']
    macd = market_data['macd']
    signal = market_data['signal']
    upper_band = market_data['upper_band']
    lower_band = market_data['lower_band']

    if position is None:  # No position, decide entry
        # Using both MACD and RSI as confirmation indicators
        if rsi < 30 and macd > signal:  # Conservative oversold condition for buying
            reason = f"RSI={rsi:.2f} (Oversold) and MACD ({macd:.2f}) > Signal ({signal:.2f})"
            return "BUY", close_price, reason
        elif rsi > 70 and macd < signal:  # Conservative overbought condition for selling
            reason = f"RSI={rsi:.2f} (Overbought) and MACD ({macd:.2f}) < Signal ({signal:.2f})"
            return "SELL", close_price, reason
    else:  # Already in a position, decide exit
        if position == "BUY":
            # More aggressive stop-loss or take-profit ratios
            if close_price >= upper_band or rsi > 80:  # Exit on overbought or price at upper band
                reason = f"RSI={rsi:.2f} (Overbought) or Close Price={close_price:.2f} >= Upper Band ({upper_band:.2f})"
                return "EXIT", close_price, reason
            elif close_price < (entry_price * 0.98):  # Exit at 2% loss
                reason = f"Close Price={close_price:.2f} < Entry Price * 0.98 (Exit at small loss)"
                return "EXIT", close_price, reason
        elif position == "SELL":
            if close_price <= lower_band or rsi < 30:  # Oversold condition for selling exit
                reason = f"RSI={rsi:.2f} (Oversold) or Close Price={close_price:.2f} <= Lower Band ({lower_band:.2f})"
                return "EXIT", close_price, reason
            elif close_price > (entry_price * 1.05):  # Exit at 5% profit for sell
                reason = f"Close Price={close_price:.2f} > Entry Price * 1.05 (Exit at small profit)"
                return "EXIT", close_price, reason

    return "HOLD", close_price, "No conditions met."


def run_swing_trading_strategy(csv_file, initial_balance, stop_loss_pct, target_profit_pct, log_file="swing_trade_log.txt", log_details=False):
    """Run the swing trading strategy with improved parameters."""
    df = load_market_data(csv_file)
    balance = initial_balance
    position = None
    entry_price = 0.0
    stop_loss = 0.0
    profit_target = 0.0
    trades = []

    if log_details:
        with open(log_file, 'w') as f:
            f.write("Detailed Swing Trade Log\n")
            f.write("=" * 40 + "\n")

    for i in range(len(df)):
        market_data = get_market_data(df, i)
        if not market_data:
            break

        decision, price, reason = swing_trading_decision(market_data, position, entry_price)

        if decision == "BUY":
            position = "BUY"
            entry_price = price
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
            profit_target = entry_price * (1 + target_profit_pct / 100)
            message = (f"[{market_data['timestamp']}] BUY at {price:.2f} | Reason: {reason}\n"
                       f"Stop Loss: {stop_loss:.2f}, Profit Target: {profit_target:.2f}")
            if log_details:
                with open(log_file, 'a') as f:
                    f.write(message + "\n")
        elif decision == "SELL":
            position = "SELL"
            entry_price = price
            stop_loss = entry_price * (1 + stop_loss_pct / 100)
            profit_target = entry_price * (1 - target_profit_pct / 100)
            message = (f"[{market_data['timestamp']}] SELL at {price:.2f} | Reason: {reason}\n"
                       f"Stop Loss: {stop_loss:.2f}, Profit Target: {profit_target:.2f}")
            if log_details:
                with open(log_file, 'a') as f:
                    f.write(message + "\n")
        elif decision == "EXIT" and position is not None:
            if position == "BUY":
                profit = price - entry_price
            elif position == "SELL":
                profit = entry_price - price

            balance += profit
            trades.append({
                'position': position,
                'entry_price': entry_price,
                'exit_price': price,
                'profit': profit,
                'timestamp': market_data['timestamp'],
                'reason': reason
            })
            message = (f"[{market_data['timestamp']}] EXIT {position} at {price:.2f} | Reason: {reason}\n"
                       f"Profit: {profit:.2f}, Balance: {balance:.2f}")
            if log_details:
                with open(log_file, 'a') as f:
                    f.write(message + "\n")
            position = None

    # Summary
    net_profit = balance - initial_balance

    if log_details:
        with open(log_file, 'a') as f:
            f.write(f"\nFinal Balance: {balance:.2f}\n")
            f.write(f"Net Profit: {net_profit:.2f}\n")
            f.write(f"Total Trades: {len(trades)}\n")

    return balance, trades


# Example usage
if __name__ == "__main__":
    csv_file = r"./NSE_NIFTY, 1D.csv"  # Path to your CSV file
    initial_balance = 10000
    stop_loss_pct = 2  # Increased stop loss to 2%
    target_profit_pct = 6  # Reduced target profit to 3%

    final_balance, trades = run_swing_trading_strategy(csv_file, initial_balance, stop_loss_pct, target_profit_pct, log_details=True)
