import pandas as pd
import numpy as np
import logging
import talib
from scipy.stats import norm
import config

# Set up logging to capture strategy details in the required format
logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format=config.LOG_FORMAT
)


def calculate_option_greeks(S, K, T, r, sigma, option_type='call'):
    """Calculate option Greeks using Black-Scholes model"""
    T = max(T, 0.01)  # Ensure T is not zero

    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        delta = norm.cdf(d1)
        theta = -(S * sigma * np.exp(-d1 ** 2 / 2)) / (2 * np.sqrt(2 * np.pi * T)) - r * K * np.exp(-r * T) * norm.cdf(
            d2)
    else:
        delta = norm.cdf(d1) - 1
        theta = -(S * sigma * np.exp(-d1 ** 2 / 2)) / (2 * np.sqrt(2 * np.pi * T)) + r * K * np.exp(-r * T) * norm.cdf(
            -d2)

    gamma = np.exp(-d1 ** 2 / 2) / (S * sigma * np.sqrt(2 * np.pi * T))
    vega = S * np.sqrt(T) * np.exp(-d1 ** 2 / 2) / np.sqrt(2 * np.pi)

    return {
        'delta': delta,
        'gamma': gamma,
        'theta': theta,
        'vega': vega
    }


def calculate_implied_volatility(data, window=None):
    """Calculate historical volatility as proxy for implied volatility"""
    if window is None:
        window = config.HV_WINDOW

    returns = np.log(data['close'] / data['close'].shift(1))
    hist_vol = returns.rolling(window=window).std() * np.sqrt(config.TRADING_DAYS)
    return hist_vol


def calculate_indicators(data):
    """Calculate technical indicators using TA-Lib"""
    # RSI
    data['RSI'] = talib.RSI(data['close'], timeperiod=config.RSI_PERIOD)

    # MACD
    macd, signal, hist = talib.MACD(
        data['close'],
        fastperiod=12,
        slowperiod=26,
        signalperiod=9
    )
    data['MACD'] = macd
    data['MACD_Signal'] = signal
    data['MACD_Hist'] = hist

    # Volume Moving Average
    data['Volume MA'] = talib.SMA(data['Volume'], timeperiod=config.VOLUME_MA_PERIOD)

    return data


def generate_synthetic_options_data(data):
    """Generate synthetic options data for delta-neutral strategy"""
    # Calculate basic metrics
    data = calculate_indicators(data)
    data['HV'] = calculate_implied_volatility(data)
    data['IV'] = data['HV'] * config.IV_HV_RATIO  # Typically IV is slightly higher than HV

    # Generate synthetic ATM strike prices
    data['ATM_Strike'] = data['close'].round(-1)  # Round to nearest 10

    # Calculate synthetic put-call ratio (based on RSI and MACD)
    data['Put_Call_Ratio'] = (100 - data['RSI']) / 100

    # Generate synthetic open interest (based on volume)
    data['Open_Interest'] = data['Volume'].rolling(window=5).mean()

    # Time to expiration (synthetic - assuming weekly options)
    data['Days_to_Expiry'] = config.DAYS_TO_EXPIRY

    # Calculate option Greeks for both calls and puts
    for idx in data.index:
        call_greeks = calculate_option_greeks(
            S=data.loc[idx, 'close'],
            K=data.loc[idx, 'ATM_Strike'],
            T=data.loc[idx, 'Days_to_Expiry'] / config.TRADING_DAYS,
            r=config.RISK_FREE_RATE,
            sigma=data.loc[idx, 'IV']
        )

        put_greeks = calculate_option_greeks(
            S=data.loc[idx, 'close'],
            K=data.loc[idx, 'ATM_Strike'],
            T=data.loc[idx, 'Days_to_Expiry'] / config.TRADING_DAYS,
            r=config.RISK_FREE_RATE,
            sigma=data.loc[idx, 'IV'],
            option_type='put'
        )

        data.loc[idx, 'Call_Delta'] = call_greeks['delta']
        data.loc[idx, 'Put_Delta'] = put_greeks['delta']
        data.loc[idx, 'Gamma'] = call_greeks['gamma']
        data.loc[idx, 'Theta'] = call_greeks['theta']
        data.loc[idx, 'Vega'] = call_greeks['vega']

    return data


def delta_neutral_strategy(data, params):
    """Enhanced delta-neutral strategy with options parameters"""
    balance = params.get('initial_balance', config.INITIAL_BALANCE)
    initial_balance = balance
    positions = {'long': 0, 'short': 0}
    entry_prices = {'long': 0, 'short': 0}
    trades = []

    # Generate synthetic options data
    data = generate_synthetic_options_data(data)

    # Corrected rolling window application on Series
    data['IV_MA'] = data['IV'].rolling(window=config.IV_MA_PERIOD).mean()

    for i in range(1, len(data)):
        current_row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        if pd.isna(current_row['RSI']) or pd.isna(current_row['MACD']):
            continue

        current_price = current_row['close']

        # Enhanced entry signals using options data
        delta_imbalance = abs(current_row['Call_Delta'] + current_row['Put_Delta'])
        high_gamma = current_row['Gamma'] > data['Gamma'].rolling(window=config.GAMMA_MA_PERIOD).mean().iloc[i]
        iv_spike = current_row['IV'] > current_row['IV_MA']
        put_call_signal = current_row['Put_Call_Ratio'] > config.PUT_CALL_RATIO_THRESHOLD

        if positions['long'] == 0 and positions['short'] == 0:
            # Entry conditions incorporating options data
            if ((delta_imbalance > config.DELTA_IMBALANCE_THRESHOLD or high_gamma) and
                    (iv_spike or put_call_signal) and
                    current_row['Volume'] > current_row['Volume MA']):
                # Calculate position sizes based on delta exposure
                position_size = params.get('risk_per_trade_pct', config.RISK_PER_TRADE_PCT) * balance / current_price
                delta_adjustment = current_row['Call_Delta'] / (current_row['Call_Delta'] - current_row['Put_Delta'])

                positions['long'] = position_size * delta_adjustment
                positions['short'] = position_size * (1 - delta_adjustment)
                entry_prices['long'] = current_price
                entry_prices['short'] = current_price
                logging.info(
                    f"Short Entry - Price: {current_price:.2f}, Size: {positions['short']:.2f}, Balance: {balance:.2f}, Reason: RSI overbought or MACD crossunder")

        else:
            # Calculate P&L
            long_pnl = positions['long'] * (current_price - entry_prices['long'])
            short_pnl = positions['short'] * (entry_prices['short'] - current_price)
            total_pnl = long_pnl + short_pnl

            # Enhanced exit conditions
            delta_neutral = delta_imbalance < config.DELTA_NEUTRAL_THRESHOLD
            gamma_risk = current_row['Gamma'] > params.get('max_gamma', config.MAX_GAMMA)
            theta_decay = current_row['Theta'] < -params.get('max_theta', config.MAX_THETA)
            iv_crush = current_row['IV'] < current_row['IV_MA'] * config.IV_CRUSH_THRESHOLD

            if (delta_neutral or gamma_risk or theta_decay or iv_crush or
                    total_pnl < -balance * params.get('max_loss_per_trade', config.MAX_LOSS_PER_TRADE) or
                    total_pnl > balance * params.get('take_profit_pct', config.TAKE_PROFIT_PCT)):
                balance += total_pnl

                trades.append({
                    'time': current_row.name,
                    'entry_price': entry_prices['long'],
                    'exit_price': current_price,
                    'long_size': positions['long'],
                    'short_size': positions['short'],
                    'pnl': total_pnl,
                    'balance': balance,
                    'exit_reason': ('Delta Neutral' if delta_neutral
                                    else 'Gamma Risk' if gamma_risk
                    else 'Theta Decay' if theta_decay
                    else 'IV Crush' if iv_crush
                    else 'Stop Loss/Take Profit')
                })

                logging.info(
                    f"Short Exit - Price: {current_price:.2f}, PnL: {total_pnl:.2f}, Balance: {balance:.2f}, Reason: {trades[-1]['exit_reason']}")

                positions = {'long': 0, 'short': 0}
                entry_prices = {'long': 0, 'short': 0}

    # Calculate metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['pnl'] for t in trades)
        max_drawdown = min(t['balance'] for t in trades) - initial_balance if trades else 0
    else:
        profitable_trades = win_rate = total_profit = max_drawdown = 0

    # Log final strategy results
    logging.info("Strategy results:")
    logging.info(f"Initial Balance: Rs.{initial_balance:.2f}")
    logging.info(f"Final Balance: Rs.{balance:.2f}")
    logging.info(f"Total Profit/Loss: Rs.{total_profit:.2f}")
    logging.info(f"Return: {((balance - initial_balance) / initial_balance) * 100:.2f}%")
    logging.info(f"Total Trades: {total_trades}")
    logging.info(f"Profitable Trades: {profitable_trades}")
    logging.info(f"Win Rate: {win_rate:.2f}%")
    logging.info(f"Max Drawdown: Rs.{abs(max_drawdown):,.2f}")

    return {
        'initial_balance': initial_balance,
        'final_balance': balance,
        'total_trades': total_trades,
        'profitable_trades': profitable_trades,
        'win_rate': win_rate,
        'total_profit': total_profit,
        'max_drawdown': max_drawdown,
        'return_pct': ((balance - initial_balance) / initial_balance) * 100,
        'trades': trades
    }


# Parameters with config values
params = {
    'initial_balance': config.INITIAL_BALANCE,
    'risk_per_trade_pct': config.RISK_PER_TRADE_PCT,
    'max_loss_per_trade': config.MAX_LOSS_PER_TRADE,
    'take_profit_pct': config.TAKE_PROFIT_PCT,
    'max_gamma': config.MAX_GAMMA,
    'max_theta': config.MAX_THETA,
    'max_drawdown_pct': config.MAX_DRAWDOWN_PCT
}

try:
    sample_data = pd.read_csv(config.DATA_FILE)
    logging.info(f"Market data loaded from {config.DATA_FILE}")
    results = delta_neutral_strategy(sample_data, params)
except Exception as e:
    logging.error(f"Error occurred: {str(e)}")