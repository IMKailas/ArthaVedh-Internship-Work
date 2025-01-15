import pandas as pd
import numpy as np
import logging
from config import config  # Importing configuration from config.py

# Setup logging
logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def load_market_data(csv_file):
    """Load market data from the given CSV file and compute necessary indicators."""
    df = pd.read_csv(csv_file)
    df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y')

    # Advanced technical indicators
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    df['RSI'] = compute_rsi(df['close'])
    df['Volume_MA'] = df['Volume'].rolling(window=20).mean()

    # Bollinger Bands
    rolling_window = 20
    rolling_mean = df['close'].rolling(window=rolling_window).mean()
    rolling_std = df['close'].rolling(window=rolling_window).std()

    df['Upper_BB'] = rolling_mean + (2.5 * rolling_std)
    df['Lower_BB'] = rolling_mean - (2.5 * rolling_std)

    return df

def compute_rsi(price, periods=14):
    """Compute Relative Strength Index (RSI) for a given price series."""
    delta = price.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()

    rs = gain / loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50)

def advanced_mean_reversion_decision(market_data, position=None):
    """Make buy, sell, or hold decision based on advanced mean reversion strategy."""
    close = market_data['close']
    rsi = market_data['rsi']
    sma_50 = market_data['sma_50']
    sma_200 = market_data['sma_200']
    volume = market_data['volume']
    volume_ma = market_data['volume_ma']
    upper_bb = market_data['upper_bb']
    lower_bb = market_data['lower_bb']

    # Entry and exit conditions
    if position is None:
        buy_conditions = (
            rsi < 30 and
            close < lower_bb and
            close < sma_50 and
            close < sma_200 and
            volume > volume_ma * 1.5
        )
        sell_conditions = (
            rsi > 70 and
            close > upper_bb and
            close > sma_50 and
            close > sma_200 and
            volume > volume_ma * 1.5
        )

        if buy_conditions:
            return "BUY", close
        elif sell_conditions:
            return "SELL", close
    else:
        if position['type'] == "BUY":
            exit_buy = (
                rsi > 70 or
                close > sma_50 or
                close > position['entry_price'] * 1.02
            )
            if exit_buy:
                return "EXIT", close

        elif position['type'] == "SELL":
            exit_sell = (
                rsi < 30 or
                close < sma_50 or
                close < position['entry_price'] * 0.98
            )
            if exit_sell:
                return "EXIT", close

    return "HOLD", close

def run_advanced_mean_reversion_strategy(config):
    """Run the advanced mean reversion strategy based on the given configuration."""
    df = load_market_data(config["csv_file"])
    balance = config["initial_balance"]
    position = None
    trades = []
    active_trades = 0

    for i in range(len(df)):
        market_data = {
            "close": df.iloc[i]['close'],
            "volume": df.iloc[i]['Volume'],
            "rsi": df.iloc[i]['RSI'],
            "sma_50": df.iloc[i]['SMA_50'],
            "sma_200": df.iloc[i]['SMA_200'],
            "volume_ma": df.iloc[i]['Volume_MA'],
            "upper_bb": df.iloc[i]['Upper_BB'],
            "lower_bb": df.iloc[i]['Lower_BB'],
            "time": df.iloc[i]['time']
        }

        decision, price = advanced_mean_reversion_decision(market_data, position)

        if decision == "BUY" and position is None and active_trades < config["max_simultaneous_trades"]:
            trade_size = balance * config["trade_allocation"]
            position = {
                'type': "BUY",
                'entry_price': price,
                'trade_size': trade_size,
                'stop_loss': price * (1 - config["stop_loss_pct"] / 100),
                'target_profit': price * (1 + config["target_profit_pct"] / 100)
            }
            active_trades += 1
            logging.info(f"BUY at {price:.2f}, Trade Size: {trade_size:.2f}")

        elif decision == "SELL" and position is None and active_trades < config["max_simultaneous_trades"]:
            trade_size = balance * config["trade_allocation"]
            position = {
                'type': "SELL",
                'entry_price': price,
                'trade_size': trade_size,
                'stop_loss': price * (1 + config["stop_loss_pct"] / 100),
                'target_profit': price * (1 - config["target_profit_pct"] / 100)
            }
            active_trades += 1
            logging.info(f"SELL at {price:.2f}, Trade Size: {trade_size:.2f}")

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
            logging.info(f"EXIT {position['type']} at {price:.2f}, Profit: {profit:.2f}")
            position = None
            active_trades -= 1

    # Performance analysis
    net_profit = balance - config["initial_balance"]
    win_trades = [trade for trade in trades if trade['profit'] > 0]
    loss_trades = [trade for trade in trades if trade['profit'] <= 0]
    win_rate = len(win_trades) / len(trades) if trades else 0

    # Log final summary
    logging.info(f"\nFinal Balance: {balance:.2f}")
    logging.info(f"Net Profit: {net_profit:.2f}")
    logging.info(f"Total Trades: {len(trades)}")
    logging.info(f"Win Rate: {win_rate * 100:.2f}%")

    # Print summary to terminal
    print(f"\nFinal Balance: {balance:.2f}")
    print(f"Net Profit: {net_profit:.2f}")
    print(f"Total Trades: {len(trades)}")
    print(f"Win Rate: {win_rate * 100:.2f}%")

    return balance, trades

# Run strategy
if __name__ == "__main__":
    run_advanced_mean_reversion_strategy(config)
