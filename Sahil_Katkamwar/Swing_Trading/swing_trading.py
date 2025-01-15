import pandas as pd
import config

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
        "close_price": current_row[config.MARKET_DATA_COLUMNS['close']],
        "volume": current_row[config.MARKET_DATA_COLUMNS['volume']],
        "volume_ma": current_row[config.MARKET_DATA_COLUMNS['volume_ma']],
        "rsi": current_row[config.MARKET_DATA_COLUMNS['rsi']],
        "macd": current_row[config.MARKET_DATA_COLUMNS['macd']],
        "signal": current_row[config.MARKET_DATA_COLUMNS['signal']],
        "upper_band": current_row[config.MARKET_DATA_COLUMNS['upper_band']],
        "lower_band": current_row[config.MARKET_DATA_COLUMNS['lower_band']],
        "timestamp": current_row[config.MARKET_DATA_COLUMNS['timestamp']],
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
        if rsi < config.RSI_OVERSOLD and macd > signal:
            reason = f"RSI={rsi:.2f} (Oversold) and MACD ({macd:.2f}) > Signal ({signal:.2f})"
            return "BUY", close_price, reason
        elif rsi > config.RSI_OVERBOUGHT and macd < signal:
            reason = f"RSI={rsi:.2f} (Overbought) and MACD ({macd:.2f}) < Signal ({signal:.2f})"
            return "SELL", close_price, reason
    else:  # Already in a position, decide exit
        if position == "BUY":
            if close_price >= upper_band or rsi > config.RSI_EXIT_OVERBOUGHT:
                reason = f"RSI={rsi:.2f} (Overbought) or Close Price={close_price:.2f} >= Upper Band ({upper_band:.2f})"
                return "EXIT", close_price, reason
            elif close_price < (entry_price * config.STOP_LOSS_MULTIPLIER):
                reason = f"Close Price={close_price:.2f} < Entry Price * {config.STOP_LOSS_MULTIPLIER} (Exit at small loss)"
                return "EXIT", close_price, reason
        elif position == "SELL":
            if close_price <= lower_band or rsi < config.RSI_EXIT_OVERSOLD:
                reason = f"RSI={rsi:.2f} (Oversold) or Close Price={close_price:.2f} <= Lower Band ({lower_band:.2f})"
                return "EXIT", close_price, reason
            elif close_price > (entry_price * config.PROFIT_TARGET_MULTIPLIER):
                reason = f"Close Price={close_price:.2f} > Entry Price * {config.PROFIT_TARGET_MULTIPLIER} (Exit at small profit)"
                return "EXIT", close_price, reason

    return "HOLD", close_price, "No conditions met."

def run_swing_trading_strategy(csv_file, initial_balance, stop_loss_pct, target_profit_pct, log_file=config.LOG_FILE_PATH, log_details=config.LOG_DETAILS):
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

if __name__ == "__main__":
    final_balance, trades = run_swing_trading_strategy(
        csv_file=config.DATA_FILE_PATH,
        initial_balance=config.INITIAL_BALANCE,
        stop_loss_pct=config.STOP_LOSS_PCT,
        target_profit_pct=config.TARGET_PROFIT_PCT,
        log_file=config.LOG_FILE_PATH,
        log_details=config.LOG_DETAILS
    )