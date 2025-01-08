import pandas as pd
import numpy as np
import logging
from scipy.stats import norm

# Set up logging
logging.basicConfig(
    filename='delta_neutral_strategy.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def calculate_implied_volatility(data, window=20):
    """Calculate historical volatility as proxy for implied volatility"""
    returns = np.log(data['close'] / data['close'].shift(1))
    hist_vol = returns.rolling(window=window).std() * np.sqrt(252)  # This should work as a pandas Series
    return hist_vol


def generate_synthetic_options_data(data):
    """Generate synthetic options data for delta-neutral strategy"""
    # Calculate basic metrics
    data['HV'] = calculate_implied_volatility(data)
    data['IV'] = data['HV'] * 1.1  # Typically IV is slightly higher than HV

    # Generate synthetic ATM strike prices
    data['ATM_Strike'] = data['close'].round(-1)  # Round to nearest 10

    # Calculate synthetic put-call ratio (based on RSI and MACD)
    data['Put_Call_Ratio'] = (100 - data['RSI']) / 100

    # Generate synthetic open interest (based on volume)
    data['Open_Interest'] = data['Volume'].rolling(window=5).mean()

    # Time to expiration (synthetic - assuming weekly options)
    data['Days_to_Expiry'] = 5  # Assuming 5 trading days

    # Risk-free rate (using typical Indian rate)
    risk_free_rate = 0.05

    # Calculate option Greeks for both calls and puts
    for idx in data.index:
        call_greeks = calculate_option_greeks(
            S=data.loc[idx, 'close'],
            K=data.loc[idx, 'ATM_Strike'],
            T=data.loc[idx, 'Days_to_Expiry'] / 252,
            r=risk_free_rate,
            sigma=data.loc[idx, 'IV']
        )

        put_greeks = calculate_option_greeks(
            S=data.loc[idx, 'close'],
            K=data.loc[idx, 'ATM_Strike'],
            T=data.loc[idx, 'Days_to_Expiry'] / 252,
            r=risk_free_rate,
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
    balance = params['initial_balance']
    initial_balance = balance
    positions = {'long': 0, 'short': 0}
    entry_prices = {'long': 0, 'short': 0}
    trades = []

    # Generate synthetic options data
    data = generate_synthetic_options_data(data)

    # Corrected rolling window application on Series
    data['IV_MA'] = data['IV'].rolling(window=20).mean()

    for i in range(1, len(data)):
        current_row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        if pd.isna(current_row['RSI']) or pd.isna(current_row['MACD']):
            continue

        current_price = current_row['close']

        # Enhanced entry signals using options data
        delta_imbalance = abs(current_row['Call_Delta'] + current_row['Put_Delta'])
        high_gamma = current_row['Gamma'] > data['Gamma'].rolling(window=20).mean().iloc[i]
        iv_spike = current_row['IV'] > current_row['IV_MA']
        put_call_signal = current_row['Put_Call_Ratio'] > 1.2

        if positions['long'] == 0 and positions['short'] == 0:
            # Entry conditions incorporating options data
            if ((delta_imbalance > 0.15 or high_gamma) and
                    (iv_spike or put_call_signal) and
                    current_row['Volume'] > current_row['Volume MA']):
                # Calculate position sizes based on delta exposure
                position_size = params['risk_per_trade_pct'] * balance / current_price
                delta_adjustment = current_row['Call_Delta'] / (current_row['Call_Delta'] - current_row['Put_Delta'])

                positions['long'] = position_size * delta_adjustment
                positions['short'] = position_size * (1 - delta_adjustment)
                entry_prices['long'] = current_price
                entry_prices['short'] = current_price
                logging.info(f"Entered position at {current_row.name} - Price: ₹{current_price:.2f}")

        else:
            # Calculate P&L
            long_pnl = positions['long'] * (current_price - entry_prices['long'])
            short_pnl = positions['short'] * (entry_prices['short'] - current_price)
            total_pnl = long_pnl + short_pnl

            # Enhanced exit conditions
            delta_neutral = delta_imbalance < 0.05
            gamma_risk = current_row['Gamma'] > params['max_gamma']
            theta_decay = current_row['Theta'] < -params['max_theta']
            iv_crush = current_row['IV'] < current_row['IV_MA'] * 0.8

            if (delta_neutral or gamma_risk or theta_decay or iv_crush or
                    total_pnl < -balance * params['max_loss_per_trade'] or
                    total_pnl > balance * params['take_profit_pct']):
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


# Updated parameters incorporating options metrics
params = {
    'initial_balance': 100000,
    'risk_per_trade_pct': 0.1,  # Increased risk per trade
    'max_loss_per_trade': 0.02,
    'take_profit_pct': 0.03,
    'max_gamma': 0.1,  # Maximum gamma exposure
    'max_theta': 50,  # Maximum theta decay
    'max_drawdown_pct': 0.15
}

try:
    sample_data = pd.read_csv('./NSE_NIFTY_Intraday.csv')
    results = delta_neutral_strategy(sample_data, params)

    print("\nDelta-Neutral Strategy Results:")
    print(f"Initial Balance: ₹{results['initial_balance']:,.2f}")
    print(f"Final Balance: ₹{results['final_balance']:,.2f}")
    print(f"Total Profit/Loss: ₹{results['total_profit']:,.2f}")
    print(f"Return: {results['return_pct']:.2f}%")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Profitable Trades: {results['profitable_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Max Drawdown: ₹{abs(results['max_drawdown']):,.2f}")

    print("\nRecent Trades:")
    for trade in results['trades'][-5:]:
        print(f"Time: {trade['time']}, Entry: ₹{trade['entry_price']:.2f}, "
              f"Exit: ₹{trade['exit_price']:.2f}, PnL: ₹{trade['pnl']:,.2f}, "
              f"Reason: {trade['exit_reason']}")

except Exception as e:
    logging.error(f"Error occurred: {str(e)}")