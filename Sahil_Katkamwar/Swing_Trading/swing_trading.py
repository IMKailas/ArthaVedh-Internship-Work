import pandas as pd
import numpy as np
import talib
import config
import logging
from typing import Dict, List, Tuple, Optional


class SwingTradingStrategy:
    def __init__(self,
                 csv_file: str,
                 initial_balance: float,
                 stop_loss_pct: float,
                 target_profit_pct: float,
                 log_file: Optional[str] = None):
        """
        Initialize the swing trading strategy.

        :param csv_file: Path to the input CSV file
        :param initial_balance: Starting trading balance
        :param stop_loss_pct: Stop loss percentage
        :param target_profit_pct: Target profit percentage
        :param log_file: Optional log file path
        """
        # Configure logging
        logging.basicConfig(
            filename=log_file or 'swing_trading.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )

        # Load and preprocess data
        self.df = self._load_market_data(csv_file)

        # Strategy parameters
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.stop_loss_pct = stop_loss_pct
        self.target_profit_pct = target_profit_pct

        # Trading state variables
        self.position = None
        self.entry_price = 0.0
        self.trades = []

    def _load_market_data(self, csv_file: str) -> pd.DataFrame:
        """
        Load and preprocess market data from CSV.

        :param csv_file: Path to the CSV file
        :return: Processed DataFrame
        """
        # Load CSV
        df = pd.read_csv(csv_file)

        # Ensure datetime conversion
        df['time'] = pd.to_datetime(df['time'], dayfirst=True)

        # Calculate technical indicators using TA-Lib
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['macd'], df['signal'], _ = talib.MACD(
            df['close'],
            fastperiod=12,
            slowperiod=26,
            signalperiod=9
        )

        # Bollinger Bands
        df['upper_band'], df['middle_band'], df['lower_band'] = talib.BBANDS(
            df['close'],
            timeperiod=20,
            nbdevup=2,
            nbdevdn=2,
            matype=0
        )

        # Volume Moving Average
        df['Volume_ma'] = talib.SMA(df['Volume'], timeperiod=20)

        # Drop initial rows with NaN values due to indicator calculations
        df.dropna(inplace=True)

        return df

    def _get_market_data(self, index: int) -> Dict[str, float]:
        """
        Retrieve market data for a specific index.

        :param index: DataFrame row index
        :return: Dictionary of market data
        """
        if index >= len(self.df):
            return None

        row = self.df.iloc[index]
        return {
            "close_price": row['close'],
            "Volume": row['Volume'],
            "Volume_ma": row['Volume_ma'],
            "rsi": row['rsi'],
            "macd": row['macd'],
            "signal": row['signal'],
            "upper_band": row['upper_band'],
            "lower_band": row['lower_band'],
            "timestamp": row['time']
        }

    def _trading_decision(self, market_data: Dict[str, float]) -> Tuple[str, float, str]:
        """
        Determine trading decision based on market data.

        :param market_data: Dictionary of current market indicators
        :return: Tuple of (decision, price, reason)
        """
        close_price = market_data['close_price']
        rsi = market_data['rsi']
        macd = market_data['macd']
        signal = market_data['signal']
        upper_band = market_data['upper_band']
        lower_band = market_data['lower_band']

        # Entry conditions
        if self.position is None:
            # Buy condition
            if rsi < config.RSI_OVERSOLD and macd > signal:
                reason = f"RSI={rsi:.2f} (Oversold) and MACD ({macd:.2f}) > Signal ({signal:.2f})"
                return "BUY", close_price, reason

            # Sell condition
            elif rsi > config.RSI_OVERBOUGHT and macd < signal:
                reason = f"RSI={rsi:.2f} (Overbought) and MACD ({macd:.2f}) < Signal ({signal:.2f})"
                return "SELL", close_price, reason

        # Exit conditions
        else:
            # Long position exit
            if self.position == "BUY":
                if close_price >= upper_band or rsi > config.RSI_EXIT_OVERBOUGHT:
                    reason = f"RSI={rsi:.2f} (Overbought) or Close Price={close_price:.2f} >= Upper Band ({upper_band:.2f})"
                    return "EXIT", close_price, reason

                if close_price < (self.entry_price * config.STOP_LOSS_MULTIPLIER):
                    reason = f"Close Price={close_price:.2f} < Entry Price * {config.STOP_LOSS_MULTIPLIER} (Exit at small loss)"
                    return "EXIT", close_price, reason

            # Short position exit
            elif self.position == "SELL":
                if close_price <= lower_band or rsi < config.RSI_EXIT_OVERSOLD:
                    reason = f"RSI={rsi:.2f} (Oversold) or Close Price={close_price:.2f} <= Lower Band ({lower_band:.2f})"
                    return "EXIT", close_price, reason

                if close_price > (self.entry_price * config.PROFIT_TARGET_MULTIPLIER):
                    reason = f"Close Price={close_price:.2f} > Entry Price * {config.PROFIT_TARGET_MULTIPLIER} (Exit at small profit)"
                    return "EXIT", close_price, reason

        return "HOLD", close_price, "No conditions met."

    def run_strategy(self) -> Tuple[float, List[Dict]]:
        """
        Execute the swing trading strategy.

        :return: Final balance and list of trades
        """
        logging.info(f"Starting Swing Trading Strategy with Balance: ${self.initial_balance}")

        for i in range(len(self.df)):
            market_data = self._get_market_data(i)
            if not market_data:
                break

            decision, price, reason = self._trading_decision(market_data)

            # Buy signal
            if decision == "BUY":
                self.position = "BUY"
                self.entry_price = price
                logging.info(f"BUY at {price:.2f} | Reason: {reason}")

            # Sell signal
            elif decision == "SELL":
                self.position = "SELL"
                self.entry_price = price
                logging.info(f"SELL at {price:.2f} | Reason: {reason}")

            # Exit position
            elif decision == "EXIT" and self.position is not None:
                if self.position == "BUY":
                    profit = price - self.entry_price
                elif self.position == "SELL":
                    profit = self.entry_price - price

                self.balance += profit
                trade_details = {
                    'position': self.position,
                    'entry_price': self.entry_price,
                    'exit_price': price,
                    'profit': profit,
                    'timestamp': market_data['timestamp'],
                    'reason': reason
                }
                self.trades.append(trade_details)

                logging.info(f"EXIT {self.position} at {price:.2f} | Reason: {reason}")
                logging.info(f"Profit: {profit:.2f}, Balance: {self.balance:.2f}")

                self.position = None

        # Strategy summary
        net_profit = self.balance - self.initial_balance
        logging.info(f"\nFinal Balance: ${self.balance:.2f}")
        logging.info(f"Net Profit: ${net_profit:.2f}")
        logging.info(f"Total Trades: {len(self.trades)}")

        return self.balance, self.trades


def main():
    # Example usage
    strategy = SwingTradingStrategy(
        csv_file=config.DATA_FILE_PATH,
        initial_balance=config.INITIAL_BALANCE,
        stop_loss_pct=config.STOP_LOSS_PCT,
        target_profit_pct=config.TARGET_PROFIT_PCT,
        log_file=config.LOG_FILE_PATH
    )

    final_balance, trades = strategy.run_strategy()


if __name__ == "__main__":
    main()