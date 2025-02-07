import pandas as pd
import numpy as np
import logging
import sys
import talib
from datetime import datetime
from config import DATA_CONFIG, TRADING_PARAMS, INDICATOR_PARAMS, REQUIRED_COLUMNS


class OptionsTradeLogger:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.trades = []
        self.trade_counter = 0

        # Setup logging to display in both console and file
        self.logger = logging.getLogger('OptionsTrading')
        self.logger.setLevel(logging.INFO)

        # Create formatters and add it to the handlers
        log_format = logging.Formatter('%(message)s')

        # Create a file handler
        file_handler = logging.FileHandler(DATA_CONFIG["log_file"], mode='w')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(log_format)

        # Create a stream handler (for console output)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(log_format)

        # Add both handlers to the logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.log_strategy_start()

    def log_strategy_start(self):
        header = "=" * 45 + " Options Trading Strategy Started " + "=" * 45
        self.logger.info(header)
        self.logger.info(f"Initial Balance: ${self.initial_balance:,.2f}")
        self.logger.info(f"Stop Loss Percentage: {TRADING_PARAMS['stop_loss'] * 100:.1f}%")
        self.logger.info(f"Target Profit Percentage: {TRADING_PARAMS['take_profit'] * 100:.1f}%")
        self.logger.info(f"IV Low Threshold: {INDICATOR_PARAMS['iv_low_threshold']}")
        self.logger.info(f"IV High Threshold: {INDICATOR_PARAMS['iv_high_threshold']}")
        self.logger.info("=" * len(header))

    def log_position_open(self, position_type, entry_price, current_time, metrics):
        self.trade_counter += 1
        trade_info = {
            'trade_number': self.trade_counter,
            'type': position_type,
            'entry_time': current_time,
            'entry_price': entry_price,
            'metrics': metrics
        }

        self.trades.append(trade_info)

        self.logger.info("=" * 45)
        self.logger.info(f"Opened {position_type} position at {entry_price:.2f}")
        self.logger.info(f"Entry Reasoning: {self._format_metrics(metrics)}")
        self.logger.info(f"Stop Loss: {entry_price * TRADING_PARAMS['stop_loss']:.2f}, "
                         f"Target Profit: {entry_price * TRADING_PARAMS['take_profit']:.2f}")
        self.logger.info(f"Entry Time: {current_time}")
        self.logger.info("=" * 45)

    def log_position_close(self, exit_price, exit_time, profit, balance, exit_reason, metrics):
        current_trade = self.trades[-1]
        current_trade.update({
            'exit_time': exit_time,
            'exit_price': exit_price,
            'profit': profit,
            'exit_reason': exit_reason,
            'final_balance': balance
        })

        self.logger.info(f"Closed {current_trade['type']} position: {exit_reason}")
        self.logger.info(f"Entry Reasoning: {self._format_metrics(metrics)}")
        self.logger.info(f"Entry Price: {current_trade['entry_price']:.2f}, Exit Price: {exit_price:.2f}")
        self.logger.info(f"Profit/Loss: ${profit:.2f}")
        self.logger.info(f"New Balance: ${balance:.2f}")
        self.logger.info(f"Exit Time: {exit_time}")
        self.logger.info("=" * 45)

    def print_trading_summary(self, final_balance):
        self.logger.info("\n" + "=" * 45 + " Trading Summary " + "=" * 45)
        self.logger.info(f"Initial Balance: ${self.initial_balance:,.2f}")
        self.logger.info(f"Final Balance: ${final_balance:,.2f}")

        total_profit = final_balance - self.initial_balance
        self.logger.info(f"Total Profit/Loss: ${total_profit:,.2f}")
        self.logger.info(f"Total Trades Executed: {len(self.trades)}")

        self.logger.info("\nDetailed Trade Analysis:")
        for trade in self.trades:
            self.logger.info(f"\nTrade #{trade['trade_number']}:")
            self.logger.info(f"Entry Time: {trade['entry_time']}")
            self.logger.info(f"Exit Time: {trade['exit_time']}")
            self.logger.info(f"Entry Price: {trade['entry_price']:.2f}")
            self.logger.info(f"Exit Price: {trade['exit_price']:.2f}")
            self.logger.info(f"Status: {trade['exit_reason']}")
            self.logger.info(f"Profit/Loss: ${trade['profit']:.2f}")
            self.logger.info(f"Entry Reasoning: {self._format_metrics(trade['metrics'])}")

        # Calculate statistics
        profitable_trades = [t for t in self.trades if t['profit'] > 0]
        loss_trades = [t for t in self.trades if t['profit'] <= 0]

        self.logger.info("\nProfit/Loss Statistics:")
        self.logger.info(f"Profitable Trades: {len(profitable_trades)}")
        self.logger.info(f"Loss-making Trades: {len(loss_trades)}")

        avg_profit = np.mean([t['profit'] for t in profitable_trades]) if profitable_trades else 0
        avg_loss = np.mean([t['profit'] for t in loss_trades]) if loss_trades else 0
        win_rate = (len(profitable_trades) / len(self.trades) * 100) if self.trades else 0

        self.logger.info(f"Average Profit per Winning Trade: ${avg_profit:.2f}")
        self.logger.info(f"Average Loss per Losing Trade: ${avg_loss:.2f}")
        self.logger.info(f"Win Rate: {win_rate:.2f}%")
        self.logger.info("=" * 45)

    def _format_metrics(self, metrics):
        return (f"IV: {metrics['iv']:.2f} | "
                f"Delta: {metrics['delta']:.2f} | "
                f"Gamma: {metrics['gamma']:.2f}")


def calculate_options_metrics(df):
    """Calculate additional options trading metrics using TA-Lib"""
    # Convert to numpy arrays for TA-Lib
    close_prices = df['close'].values
    volume = df['Volume'].values

    # Bollinger Bands
    upper_band, middle_band, lower_band = talib.BBANDS(
        close_prices,
        timeperiod=INDICATOR_PARAMS["bollinger_window"],
        nbdevup=INDICATOR_PARAMS["bollinger_std"],
        nbdevdn=INDICATOR_PARAMS["bollinger_std"],
        matype=0
    )

    # Implied Volatility Proxy (using ATR as a volatility indicator)
    volatility = talib.ATR(
        df['high'].values,
        df['low'].values,
        close_prices,
        timeperiod=INDICATOR_PARAMS["iv_window"]
    )

    # Normalize volatility
    iv_proxy = volatility / close_prices * 100

    # Calculate custom delta and gamma using Bollinger Bands
    delta = np.where(
        close_prices > upper_band, INDICATOR_PARAMS["delta_threshold"],
        np.where(
            close_prices < lower_band, -INDICATOR_PARAMS["delta_threshold"],
            0.5
        )
    )

    gamma = np.abs(delta) * INDICATOR_PARAMS["gamma_multiplier"]

    # Create strategy signals
    strategy_signal = np.where(
        (iv_proxy < INDICATOR_PARAMS["iv_low_threshold"]) & (delta > 0.5),
        'CALL_BUY',
        np.where(
            (iv_proxy < INDICATOR_PARAMS["iv_low_threshold"]) & (delta < -0.5),
            'PUT_BUY',
            np.where(
                (iv_proxy > INDICATOR_PARAMS["iv_high_threshold"]) & (delta > 0.5),
                'CALL_SELL',
                np.where(
                    (iv_proxy > INDICATOR_PARAMS["iv_high_threshold"]) & (delta < -0.5),
                    'PUT_SELL',
                    'HOLD'
                )
            )
        )
    )

    # Add new columns to DataFrame
    df['Middle Band'] = middle_band
    df['Upper Bollinger Band'] = upper_band
    df['Lower Bollinger Band'] = lower_band
    df['IV_proxy'] = iv_proxy
    df['delta'] = delta
    df['gamma'] = gamma
    df['strategy_signal'] = strategy_signal

    return df


def run_options_trading_strategy():
    # Load and prepare data
    df = pd.read_csv(DATA_CONFIG["data_path"])
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time')

    numeric_columns = [col for col in REQUIRED_COLUMNS if col != 'time']
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # Calculate options metrics
    df = calculate_options_metrics(df)

    # Initialize logger and trading variables
    balance = TRADING_PARAMS["initial_balance"]
    trade_logger = OptionsTradeLogger(balance)
    position = None
    entry_price = None

    # Main trading loop
    for i in range(1, len(df)):
        current_row = df.iloc[i]

        metrics = {
            'iv': current_row['IV_proxy'],
            'delta': current_row['delta'],
            'gamma': current_row['gamma']
        }

        if position is None:
            if current_row['strategy_signal'] == 'CALL_BUY':
                trade_size = balance * TRADING_PARAMS["risk_per_trade"]
                position = 'CALL_LONG'
                entry_price = current_row['close']
                shares = trade_size / entry_price

                trade_logger.log_position_open(position, entry_price, current_row['time'], metrics)

            elif current_row['strategy_signal'] == 'PUT_BUY':
                trade_size = balance * TRADING_PARAMS["risk_per_trade"]
                position = 'PUT_LONG'
                entry_price = current_row['close']
                shares = trade_size / entry_price

                trade_logger.log_position_open(position, entry_price, current_row['time'], metrics)

        else:
            current_price = current_row['close']

            if position == 'CALL_LONG':
                if (current_row['strategy_signal'] in ['PUT_BUY', 'PUT_SELL'] or
                        current_price < entry_price * TRADING_PARAMS["stop_loss"]):
                    profit = (current_price - entry_price) * shares
                    balance += profit

                    exit_reason = "Stop Loss" if current_price < entry_price * TRADING_PARAMS[
                        "stop_loss"] else "Signal Change"
                    trade_logger.log_position_close(current_price, current_row['time'],
                                                    profit, balance, exit_reason, metrics)
                    position = None

            elif position == 'PUT_LONG':
                if (current_row['strategy_signal'] in ['CALL_BUY', 'CALL_SELL'] or
                        current_price > entry_price * TRADING_PARAMS["take_profit"]):
                    profit = (entry_price - current_price) * shares
                    balance += profit

                    exit_reason = "Take Profit" if current_price > entry_price * TRADING_PARAMS[
                        "take_profit"] else "Signal Change"
                    trade_logger.log_position_close(current_price, current_row['time'],
                                                    profit, balance, exit_reason, metrics)
                    position = None

    # Close any remaining positions at the end
    if position is not None:
        current_price = df['close'].iloc[-1]
        if position == 'CALL_LONG':
            profit = (current_price - entry_price) * shares
        else:
            profit = (entry_price - current_price) * shares

        balance += profit
        trade_logger.log_position_close(current_price, df['time'].iloc[-1],
                                        profit, balance, "Market Close", metrics)

    # Print final summary
    trade_logger.print_trading_summary(balance)

    return balance, trade_logger.trades


if __name__ == "__main__":
    final_balance, trades = run_options_trading_strategy()