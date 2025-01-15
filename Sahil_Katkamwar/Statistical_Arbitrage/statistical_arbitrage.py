import pandas as pd
import numpy as np
import logging
import config

# Enhanced logging setup
logging.basicConfig(
    filename=config.LOG_CONFIG['filename'],
    level=getattr(logging, config.LOG_CONFIG['level']),
    format=config.LOG_CONFIG['format']
)


def calculate_zscore(spread):
    """Calculate z-score of the spread"""
    mean = spread.rolling(window=config.ZSCORE_WINDOW).mean()
    std = spread.rolling(window=config.ZSCORE_WINDOW).std()
    return (spread - mean) / std


def calculate_position_size(balance, price_a, price_b):
    """Calculate larger position sizes with proper scaling"""
    total_exposure = balance * config.LEVERAGE * config.RISK_PER_TRADE_PCT

    # Ensure minimum position sizes for profitability
    total_exposure = max(total_exposure, config.MIN_NOTIONAL_VALUE)

    # Calculate sizes based on price ratio
    price_ratio = price_a / price_b
    size_a = total_exposure / (price_a + price_b * price_ratio)
    size_b = size_a * price_ratio

    # Round to 2 decimals for more realistic position sizes
    return round(size_a, 2), round(size_b, 2)


def check_entry_conditions(zscore, volume_active, rsi_stable, trend_direction):
    """Enhanced entry conditions"""
    if volume_active and rsi_stable:
        if zscore < -config.ZSCORE_ENTRY_THRESHOLD and trend_direction > 0:  # Long entry
            return True, 'long'
        elif zscore > config.ZSCORE_ENTRY_THRESHOLD and trend_direction < 0:  # Short entry
            return True, 'short'
    return False, None


def check_exit_conditions(zscore, position_type, entry_time, current_time, entry_zscore):
    """Improved exit conditions"""
    # Profit target reached
    if position_type == 'long':
        if zscore >= -config.ZSCORE_EXIT_THRESHOLD or zscore >= (entry_zscore + config.ZSCORE_STOP_LOSS):  # Take profit on mean reversion or improvement
            return True, 'profit_target'
        if zscore < entry_zscore - config.ZSCORE_STOP_LOSS:  # Stop loss on further divergence
            return True, 'stop_loss'
    else:  # Short position
        if zscore <= config.ZSCORE_EXIT_THRESHOLD or zscore <= (entry_zscore - config.ZSCORE_STOP_LOSS):
            return True, 'profit_target'
        if zscore > entry_zscore + config.ZSCORE_STOP_LOSS:
            return True, 'stop_loss'

    # Trade timeout
    if (current_time - entry_time).total_seconds() > (config.POSITION_HOLD_MINUTES * 60):
        return True, 'timeout'

    return False, None


def statistical_arbitrage_strategy(nifty_data, bank_data):
    """Execute improved statistical arbitrage strategy"""
    balance = config.INITIAL_BALANCE
    initial_balance = balance
    trades = []
    position = None

    # Calculate spread and indicators
    spread = nifty_data['close'] / bank_data['close']
    zscore = calculate_zscore(spread)

    for i in range(config.ZSCORE_WINDOW, len(nifty_data)):
        current_time = nifty_data.index[i]

        # Market conditions with stronger filters
        volume_active = (nifty_data['Volume'].iloc[i] > nifty_data['Volume MA'].iloc[i] * config.VOLUME_THRESHOLD)
        rsi_stable = (config.RSI_LOWER < nifty_data['RSI'].iloc[i] < config.RSI_UPPER)
        trend_direction = np.sign(nifty_data['close'].iloc[i] - nifty_data['close'].iloc[i - config.TREND_PERIODS])

        current_zscore = zscore.iloc[i]

        if position is None:
            entry_signal, trade_type = check_entry_conditions(
                current_zscore,
                volume_active,
                rsi_stable,
                trend_direction
            )

            if entry_signal:
                size_nifty, size_bank = calculate_position_size(
                    balance,
                    nifty_data['close'].iloc[i],
                    bank_data['close'].iloc[i]
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
                New Trade Entry:
                Time: {current_time}
                Strategy: {trade_type.upper()} NIFTY vs BANK
                Z-Score: {current_zscore:.2f}
                Entry Prices: NIFTY={position['nifty_entry']:.2f}, BANK={position['bank_entry']:.2f}
                Position Sizes: NIFTY={position['nifty_size']:.2f}, BANK={position['bank_size']:.2f}
                Notional Value: ${(position['nifty_size'] * position['nifty_entry'] + position['bank_size'] * position['bank_entry']):,.2f}
                """)

        else:
            exit_signal, exit_reason = check_exit_conditions(
                current_zscore,
                position['type'],
                position['entry_time'],
                current_time,
                position['entry_zscore']
            )

            if exit_signal:
                # Calculate PnL with improved position sizes
                if position['type'] == 'long':
                    nifty_pnl = position['nifty_size'] * (nifty_data['close'].iloc[i] - position['nifty_entry'])
                    bank_pnl = position['bank_size'] * (position['bank_entry'] - bank_data['close'].iloc[i])
                else:
                    nifty_pnl = position['nifty_size'] * (position['nifty_entry'] - nifty_data['close'].iloc[i])
                    bank_pnl = position['bank_size'] * (bank_data['close'].iloc[i] - position['bank_entry'])

                total_pnl = nifty_pnl + bank_pnl

                # Apply reduced transaction costs for larger sizes
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
                Strategy: {position['type'].upper()}
                Exit Reason: {exit_reason}
                Z-Score Movement: {position['entry_zscore']:.2f} -> {current_zscore:.2f}
                PnL: ${total_pnl:.2f}
                Current Balance: ${balance:.2f}
                Trade Duration: {(current_time - position['entry_time']).total_seconds() / 60:.1f} minutes
                """)

                position = None

                # Implement cooling-off period after losses
                if total_pnl < 0:
                    cooling_off_end = current_time + pd.Timedelta(minutes=config.COOLING_OFF_MINUTES)
                    logging.info(f"Entering cooling-off period until {cooling_off_end}")

    # Calculate final metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['pnl'] for t in trades)
        max_drawdown = abs(min(0, min(t['balance'] - initial_balance for t in trades)))
        avg_profit_per_trade = total_profit / total_trades

        # Calculate Sharpe Ratio (assuming risk-free rate of 2%)
        returns = pd.Series([t['pnl'] for t in trades])
        sharpe_ratio = (returns.mean() * 252 - 0.02) / (returns.std() * np.sqrt(252)) if len(returns) > 1 else 0
    else:
        profitable_trades = win_rate = total_profit = max_drawdown = avg_profit_per_trade = sharpe_ratio = 0

    logging.info(f"""
    Strategy Performance Summary:
    ===========================
    Initial Capital: ${initial_balance:,.2f}
    Final Capital: ${balance:,.2f}
    Net Profit: ${total_profit:,.2f}
    Return on Investment: {((balance - initial_balance) / initial_balance) * 100:.2f}%

    Trade Statistics:
    ----------------
    Total Trades: {total_trades}
    Winning Trades: {profitable_trades}
    Win Rate: {win_rate:.2f}%
    Average Profit per Trade: ${avg_profit_per_trade:,.2f}
    Sharpe Ratio: {sharpe_ratio:.2f}
    Maximum Drawdown: ${max_drawdown:,.2f}
    """)

    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio
    }


def generate_correlated_data(nifty_data):
    """
    Generate synthetic NIFTY BANK data correlated with NIFTY
    """
    # Calculate NIFTY returns
    nifty_returns = nifty_data['close'].pct_change()

    # Generate random component for BANK returns
    np.random.seed(42)  # For reproducibility
    random_component = np.random.normal(0, nifty_returns.std(), len(nifty_returns))

    # Create correlated returns using correlation coefficient
    bank_returns = (config.SYNTHETIC_DATA['correlation'] * nifty_returns +
                    np.sqrt(1 - config.SYNTHETIC_DATA['correlation'] ** 2) * random_component *
                    config.SYNTHETIC_DATA['volatility_factor'])

    # Start BANK prices at a realistic level
    initial_bank_price = nifty_data['close'].iloc[0] * config.SYNTHETIC_DATA['bank_nifty_multiplier']
    bank_prices = initial_bank_price * (1 + bank_returns).cumprod()

    # Create BANK dataframe
    bank_data = pd.DataFrame(index=nifty_data.index)

    # Generate synthetic price data
    bank_data['close'] = bank_prices

    # Generate correlated volume data
    volume_correlation = config.SYNTHETIC_DATA['volume_correlation']
    random_volume = np.random.normal(0, nifty_data['Volume'].std(), len(nifty_data))
    bank_data['Volume'] = (nifty_data['Volume'] * volume_correlation +
                           random_volume * np.sqrt(1 - volume_correlation ** 2))
    bank_data['Volume'] = np.abs(bank_data['Volume'])  # Ensure positive volume

    # Generate correlated RSI data
    rsi_correlation = config.SYNTHETIC_DATA['rsi_correlation']
    random_rsi = np.random.normal(0, nifty_data['RSI'].std(), len(nifty_data))
    bank_data['RSI'] = (nifty_data['RSI'] * rsi_correlation +
                        random_rsi * np.sqrt(1 - rsi_correlation ** 2))

    # Ensure RSI stays within bounds (0-100)
    bank_data['RSI'] = bank_data['RSI'].clip(0, 100)

    # Add realistic market microstructure effects
    bank_data['close'] = bank_data['close'].round(2)  # Round to 2 decimals
    bank_data['Volume'] = bank_data['Volume'].round().astype(int)  # Integer volume

    # Generate additional required columns if they exist in NIFTY data
    if 'Volume MA' in nifty_data.columns:
        bank_data['Volume MA'] = bank_data['Volume'].rolling(window=20).mean()

    logging.info(f"""
    Generated synthetic BANK data:
    Correlation with NIFTY: {config.SYNTHETIC_DATA['correlation']:.2f}
    Initial BANK price: {initial_bank_price:.2f}
    Final BANK price: {bank_data['close'].iloc[-1]:.2f}
    Average daily volume: {bank_data['Volume'].mean():.0f}
    """)

    return bank_data

if __name__ == "__main__":
    try:
        # Initialize logging
        logging.basicConfig(
            filename=config.LOG_CONFIG['filename'],
            level=getattr(logging, config.LOG_CONFIG['level']),
            format=config.LOG_CONFIG['format']
        )

        # Load and process data
        nifty_data = pd.read_csv(config.DATA_FILE_PATH, parse_dates=['time'])
        nifty_data.set_index('time', inplace=True)
        bank_data = generate_correlated_data(nifty_data)

        # Execute strategy without params argument
        results = statistical_arbitrage_strategy(nifty_data, bank_data)

        # Log strategy results
        logging.info(f"""
        Strategy Execution Completed Successfully:
        Total Trades: {results['total_trades']}
        Win Rate: {results['win_rate']:.2f}%
        Total Profit: ${results['total_profit']:,.2f}
        Sharpe Ratio: {results['sharpe_ratio']:.2f}
        """)

    except Exception as e:
        logging.error(f"Error in strategy execution: {str(e)}")
        raise  # Re-raise the exception for debugging