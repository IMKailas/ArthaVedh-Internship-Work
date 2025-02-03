import pandas as pd
import numpy as np
import talib
import logging
import config

logging.basicConfig(
    filename=config.LOG_CONFIG['filename'],
    level=getattr(logging, config.LOG_CONFIG['level']),
    format=config.LOG_CONFIG['format']
)


def prepare_data(df):
    """Calculate technical indicators using TA-Lib"""
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)
    df['Volume MA'] = talib.SMA(df['Volume'], timeperiod=20)

    # Additional indicators for trend confirmation
    df['EMA20'] = talib.EMA(df['close'], timeperiod=20)
    df['ATR'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)

    # MACD for trend direction
    df['MACD'], df['MACD_signal'], df['MACD_hist'] = talib.MACD(
        df['close'],
        fastperiod=12,
        slowperiod=26,
        signalperiod=9
    )

    return df


def calculate_zscore(spread):
    """Calculate z-score of the spread"""
    mean = talib.SMA(spread, timeperiod=config.ZSCORE_WINDOW)
    std = talib.STDDEV(spread, timeperiod=config.ZSCORE_WINDOW)
    return (spread - mean) / std


def calculate_position_size(balance, price_a, price_b, atr_a, atr_b):
    """Calculate position sizes with ATR-based risk adjustment"""
    total_exposure = balance * config.LEVERAGE * config.RISK_PER_TRADE_PCT
    total_exposure = max(total_exposure, config.MIN_NOTIONAL_VALUE)

    # Adjust position sizes based on ATR ratio
    volatility_ratio = atr_a / atr_b
    price_ratio = price_a / price_b

    # Calculate base position sizes
    size_a = total_exposure / (price_a + price_b * price_ratio)
    size_b = size_a * price_ratio

    # Adjust for relative volatility
    size_a = size_a * (1 / volatility_ratio)
    size_b = size_b * volatility_ratio

    return round(size_a, 2), round(size_b, 2)


def check_entry_conditions(row_a, row_b, zscore):
    """Enhanced entry conditions using TA-Lib indicators"""
    volume_active = (row_a['Volume'] > row_a['Volume MA'] * config.VOLUME_THRESHOLD and
                     row_b['Volume'] > row_b['Volume MA'] * config.VOLUME_THRESHOLD)

    rsi_stable = (config.RSI_LOWER < row_a['RSI'] < config.RSI_UPPER and
                  config.RSI_LOWER < row_b['RSI'] < config.RSI_UPPER)

    trend_aligned = (
            (row_a['MACD'] > row_a['MACD_signal']) == (row_b['MACD'] > row_b['MACD_signal'])
    )

    if volume_active and rsi_stable and trend_aligned:
        if zscore < -config.ZSCORE_ENTRY_THRESHOLD:
            return True, 'long'
        elif zscore > config.ZSCORE_ENTRY_THRESHOLD:
            return True, 'short'
    return False, None


def check_exit_conditions(zscore, position, current_time, row_a, row_b):
    """Exit conditions with technical indicator confirmation"""
    # Trend reversal check using MACD
    trend_reversal = False
    if position['type'] == 'long':
        trend_reversal = (row_a['MACD'] < row_a['MACD_signal'] and
                          row_b['MACD'] < row_b['MACD_signal'])
    else:
        trend_reversal = (row_a['MACD'] > row_a['MACD_signal'] and
                          row_b['MACD'] > row_b['MACD_signal'])

    # Profit target or stop loss based on zscore
    if position['type'] == 'long':
        if zscore >= -config.ZSCORE_EXIT_THRESHOLD or zscore >= (position['entry_zscore'] + config.ZSCORE_STOP_LOSS):
            return True, 'profit_target'
        if zscore < position['entry_zscore'] - config.ZSCORE_STOP_LOSS:
            return True, 'stop_loss'
    else:
        if zscore <= config.ZSCORE_EXIT_THRESHOLD or zscore <= (position['entry_zscore'] - config.ZSCORE_STOP_LOSS):
            return True, 'profit_target'
        if zscore > position['entry_zscore'] + config.ZSCORE_STOP_LOSS:
            return True, 'stop_loss'

    # Exit on trend reversal
    if trend_reversal:
        return True, 'trend_reversal'

    # Time-based exit
    if (current_time - position['entry_time']).total_seconds() > (config.POSITION_HOLD_MINUTES * 60):
        return True, 'timeout'

    return False, None


def statistical_arbitrage_strategy(nifty_data, bank_data):
    """Execute statistical arbitrage strategy with TA-Lib indicators"""
    nifty_data = prepare_data(nifty_data.copy())
    bank_data = prepare_data(bank_data.copy())

    balance = config.INITIAL_BALANCE
    initial_balance = balance
    trades = []
    position = None
    cooling_off_until = None

    spread = nifty_data['close'] / bank_data['close']
    zscore = calculate_zscore(spread)

    for i in range(config.ZSCORE_WINDOW, len(nifty_data)):
        current_time = nifty_data.index[i]

        # Skip if in cooling-off period
        if cooling_off_until and current_time < cooling_off_until:
            continue

        current_zscore = zscore.iloc[i]

        if position is None:
            entry_signal, trade_type = check_entry_conditions(
                nifty_data.iloc[i],
                bank_data.iloc[i],
                current_zscore
            )

            if entry_signal:
                size_nifty, size_bank = calculate_position_size(
                    balance,
                    nifty_data['close'].iloc[i],
                    bank_data['close'].iloc[i],
                    nifty_data['ATR'].iloc[i],
                    bank_data['ATR'].iloc[i]
                )

                position = {
                    'type': trade_type,
                    'entry_zscore': current_zscore,
                    'entry_time': current_time,
                    'nifty_entry': nifty_data['close'].iloc[i],
                    'bank_entry': bank_data['close'].iloc[i],
                    'nifty_size': size_nifty,
                    'bank_size': size_bank
                }

                logging.info(f"""
                Trade Entry:
                Time: {current_time}
                Type: {trade_type.upper()}
                Z-Score: {current_zscore:.2f}
                Prices: NIFTY={position['nifty_entry']:.2f}, BANK={position['bank_entry']:.2f}
                Sizes: NIFTY={size_nifty:.2f}, BANK={size_bank:.2f}
                """)

        else:
            exit_signal, exit_reason = check_exit_conditions(
                current_zscore,
                position,
                current_time,
                nifty_data.iloc[i],
                bank_data.iloc[i]
            )

            if exit_signal:
                # Calculate PnL
                if position['type'] == 'long':
                    nifty_pnl = position['nifty_size'] * (nifty_data['close'].iloc[i] - position['nifty_entry'])
                    bank_pnl = position['bank_size'] * (position['bank_entry'] - bank_data['close'].iloc[i])
                else:
                    nifty_pnl = position['nifty_size'] * (position['nifty_entry'] - nifty_data['close'].iloc[i])
                    bank_pnl = position['bank_size'] * (bank_data['close'].iloc[i] - position['bank_entry'])

                total_pnl = nifty_pnl + bank_pnl

                # Apply transaction costs
                transaction_cost = config.TRANSACTION_COST * (0.8 if position['nifty_size'] > 1 else 1)
                total_pnl -= (position['nifty_size'] * position['nifty_entry'] +
                              position['bank_size'] * position['bank_entry']) * transaction_cost * 2

                balance += total_pnl
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': current_time,
                    'type': position['type'],
                    'entry_zscore': position['entry_zscore'],
                    'exit_zscore': current_zscore,
                    'pnl': total_pnl,
                    'exit_reason': exit_reason,
                    'balance': balance
                })

                logging.info(f"""
                Trade Exit:
                Time: {current_time}
                Type: {position['type'].upper()}
                Reason: {exit_reason}
                Z-Score: {position['entry_zscore']:.2f} -> {current_zscore:.2f}
                PnL: ${total_pnl:.2f}
                Balance: ${balance:.2f}
                """)

                position = None

                if total_pnl < 0:
                    cooling_off_until = current_time + pd.Timedelta(minutes=config.COOLING_OFF_MINUTES)

    # Calculate performance metrics
    return calculate_performance_metrics(trades, initial_balance, balance)


def generate_correlated_data(nifty_data):
    """Generate synthetic NIFTY BANK data correlated with NIFTY"""
    nifty_returns = nifty_data['close'].pct_change()

    np.random.seed(42)
    random_component = np.random.normal(0, nifty_returns.std(), len(nifty_returns))

    bank_returns = (config.SYNTHETIC_DATA['correlation'] * nifty_returns +
                    np.sqrt(1 - config.SYNTHETIC_DATA['correlation'] ** 2) * random_component *
                    config.SYNTHETIC_DATA['volatility_factor'])

    initial_bank_price = nifty_data['close'].iloc[0] * config.SYNTHETIC_DATA['bank_nifty_multiplier']
    bank_prices = initial_bank_price * (1 + bank_returns).cumprod()

    bank_data = pd.DataFrame(index=nifty_data.index)

    # Generate OHLC data
    bank_data['close'] = bank_prices
    volatility = nifty_data['close'].std() * config.SYNTHETIC_DATA['volatility_factor']
    bank_data['high'] = bank_data['close'] + np.abs(np.random.normal(0, volatility, len(bank_data)))
    bank_data['low'] = bank_data['close'] - np.abs(np.random.normal(0, volatility, len(bank_data)))
    bank_data['open'] = bank_data['close'].shift(1).fillna(bank_data['close'])

    # Generate volume data
    volume_correlation = config.SYNTHETIC_DATA['volume_correlation']
    random_volume = np.random.normal(0, nifty_data['Volume'].std(), len(nifty_data))
    bank_data['Volume'] = (nifty_data['Volume'] * volume_correlation +
                           random_volume * np.sqrt(1 - volume_correlation ** 2))
    bank_data['Volume'] = np.abs(bank_data['Volume'])

    # Clean up data
    bank_data['close'] = bank_data['close'].round(2)
    bank_data['high'] = bank_data['high'].round(2)
    bank_data['low'] = bank_data['low'].round(2)
    bank_data['open'] = bank_data['open'].round(2)
    bank_data['Volume'] = bank_data['Volume'].round().astype(int)

    return bank_data


def calculate_performance_metrics(trades, initial_balance, final_balance):
    """Calculate comprehensive performance metrics"""
    if not trades:
        return {
            'initial_balance': initial_balance,
            'final_balance': final_balance,
            'total_trades': 0,
            'profitable_trades': 0,
            'win_rate': 0,
            'total_profit': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'profit_factor': 0
        }

    total_trades = len(trades)
    profitable_trades = len([t for t in trades if t['pnl'] > 0])
    win_rate = (profitable_trades / total_trades) * 100
    total_profit = sum(t['pnl'] for t in trades)

    # Calculate drawdown
    running_balance = pd.Series([t['balance'] for t in trades])
    running_max = running_balance.expanding().max()
    drawdowns = (running_balance - running_max) / running_max * 100
    max_drawdown = abs(min(0, drawdowns.min()))

    # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
    returns = pd.Series([t['pnl'] for t in trades])
    sharpe_ratio = (returns.mean() * 252 - 0.02) / (returns.std() * np.sqrt(252)) if len(returns) > 1 else 0

    # Calculate Profit Factor
    gross_profits = sum(t['pnl'] for t in trades if t['pnl'] > 0)
    gross_losses = abs(sum(t['pnl'] for t in trades if t['pnl'] < 0))
    profit_factor = gross_profits / gross_losses if gross_losses != 0 else float('inf')

    return {
        'initial_balance': initial_balance,
        'final_balance': final_balance,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'profit_factor': profit_factor
    }


if __name__ == "__main__":
    try:
        # Load data
        nifty_data = pd.read_csv(config.DATA_FILE_PATH, parse_dates=['time'])
        nifty_data.set_index('time', inplace=True)

        # Generate synthetic bank data
        bank_data = generate_correlated_data(nifty_data)

        # Run strategy
        results = statistical_arbitrage_strategy(nifty_data, bank_data)

        logging.info(f"""
        Strategy Results:
        Total Trades: {results['total_trades']}
        Win Rate: {results['win_rate']:.2f}%
        Total Profit: ${results['total_profit']:,.2f}
        Sharpe Ratio: {results['sharpe_ratio']:.2f}
        Profit Factor: {results['profit_factor']:.2f}
        Max Drawdown: {results['max_drawdown']:.2f}%
        """)

    except Exception as e:
        logging.error(f"Strategy execution error: {str(e)}")
        raise