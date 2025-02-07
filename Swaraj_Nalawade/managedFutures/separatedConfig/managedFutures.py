import pandas as pd
import numpy as np
import talib
import logging
from datetime import datetime
import config
import json
import os
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("trading_system")


def load_data():
    """Load and preprocess market data from CSV."""
    df = pd.read_csv(config.DATA_PATH, usecols=['time', 'open', 'high', 'low', 'close', 'Volume'])
    df['time'] = pd.to_datetime(df['time'], format='%d-%m-%Y')
    df = df.sort_values('time')
    return df


def calculate_indicators(df):
    """Calculate all technical indicators using TA-Lib."""
    df['SMA20'] = talib.SMA(df['close'], timeperiod=config.SMA_SHORT_PERIOD)
    df['SMA50'] = talib.SMA(df['close'], timeperiod=config.SMA_LONG_PERIOD)

    df['ADX'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=config.ADX_PERIOD)
    df['RSI'] = talib.RSI(df['close'], timeperiod=config.RSI_PERIOD)

    df['Upper_Band'], df['Middle_Band'], df['Lower_Band'] = talib.BBANDS(
        df['close'], timeperiod=config.BBANDS_PERIOD, nbdevup=config.BBANDS_STDDEV, nbdevdn=config.BBANDS_STDDEV
    )

    df['MACD'], df['MACD_Signal'], df['MACD_Histogram'] = talib.MACD(
        df['close'], fastperiod=config.MACD_FAST, slowperiod=config.MACD_SLOW, signalperiod=config.MACD_SIGNAL
    )

    return df


def generate_signals(df):
    """Generate trading signals based on TA-Lib indicators."""
    signals = pd.Series(0, index=df.index)

    uptrend = (df['close'] > df['SMA20']) & (df['SMA20'] > df['SMA50'])
    downtrend = (df['close'] < df['SMA20']) & (df['SMA20'] < df['SMA50'])

    strong_trend = df['ADX'] > 25

    bullish_signal = (uptrend & strong_trend & (df['MACD'] > df['MACD_Signal']) & (df['RSI'] > 30))
    bearish_signal = (downtrend & strong_trend & (df['MACD'] < df['MACD_Signal']) & (df['RSI'] < 70))

    signals[bullish_signal] = 1
    signals[bearish_signal] = -1

    return signals


def calculate_position_size(balance, price):
    """Calculate position size based on risk management."""
    risk_amount = balance * config.RISK_PER_TRADE
    position_value = risk_amount / (config.STOP_LOSS_PERCENT / 100)
    position_size = position_value / price
    return max(1, round(position_size))


def run_strategy():
    """Execute trading strategy and generate a summary."""
    try:
        logger.info("Starting managed futures trading strategy...")

        df = load_data()
        df = calculate_indicators(df)
        signals = generate_signals(df)

        balance = config.INITIAL_BALANCE
        trades = []
        current_position = None

        for i in range(len(df)):
            current_row = df.iloc[i]
            signal = signals.iloc[i]

            if current_position is not None:
                exit_price = current_row['close']
                pnl = (exit_price - current_position['entry_price']) * current_position['size']
                if current_position['direction'] == -1:
                    pnl = -pnl

                profit_target = current_position['entry_price'] * (1 + config.PROFIT_TARGET_PERCENT / 100)
                stop_loss = current_position['entry_price'] * (1 - config.STOP_LOSS_PERCENT / 100)

                if ((current_position['direction'] == 1 and exit_price >= profit_target) or
                        (current_position['direction'] == -1 and exit_price <= profit_target) or
                        (current_position['direction'] == 1 and exit_price <= stop_loss) or
                        (current_position['direction'] == -1 and exit_price >= stop_loss)):

                    balance += pnl
                    trades.append({'entry_price': current_position['entry_price'], 'exit_price': exit_price, 'profit': pnl})

                    current_position = None

            elif signal != 0:
                position_size = calculate_position_size(balance, current_row['close'])
                current_position = {'direction': signal, 'entry_price': current_row['close'], 'size': position_size}

        trades_df = pd.DataFrame(trades)
        final_balance = balance

        logger.info("Trading completed successfully.")
        logger.info(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
        logger.info(f"Final Balance: ${final_balance:,.2f}")
        logger.info(f"Total P/L: ${final_balance - config.INITIAL_BALANCE:,.2f}")
        logger.info(f"Profit Percentage: {((final_balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100:.2f}%")

        print(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
        print(f"Final Balance: ${final_balance:,.2f}")
        print(f"Total P/L: ${final_balance - config.INITIAL_BALANCE:,.2f}")
        print(f"Profit Percentage: {((final_balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE) * 100:.2f}%")

        trades_df.to_csv(log_dir / f"trade_history_{timestamp}.csv", index=False)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_strategy()
