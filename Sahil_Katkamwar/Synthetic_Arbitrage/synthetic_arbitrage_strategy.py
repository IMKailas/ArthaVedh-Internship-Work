import pandas as pd
import numpy as np
import logging
import talib
import config

# Set up logging
logging.basicConfig(
    filename=config.LOG_FILE,
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT
)


def calculate_technical_indicators(data):
    """
    Calculate technical indicators using TA-Lib

    Args:
        data (pd.DataFrame): Input price data

    Returns:
        pd.DataFrame: DataFrame with added technical indicators
    """
    df = data.copy()

    # Mandatory Indicators
    df['Volume MA'] = talib.SMA(df['Volume'], timeperiod=config.VOLUME_MA_PERIOD)
    df['RSI'] = talib.RSI(df['close'], timeperiod=14)

    return df


def generate_synthetic_prices(real_price, volatility=config.PRICE_VOLATILITY):
    """Generate synthetic prices for arbitrage opportunities"""
    synthetic_a = real_price * (1 + np.random.normal(0, volatility))
    synthetic_b = real_price * (1 + np.random.normal(0, volatility))
    return synthetic_a, synthetic_b


def calculate_arbitrage_opportunity(price_a, price_b, transaction_cost_pct=config.TRANSACTION_COST):
    """Calculate potential arbitrage opportunity"""
    spread = abs(price_a - price_b)
    transaction_costs = (price_a + price_b) * transaction_cost_pct
    net_profit = spread - transaction_costs
    return net_profit > 0, net_profit


def calculate_position_size(balance, price, leverage, risk_per_trade_pct):
    """Calculate safe position size for arbitrage"""
    max_position_value = balance * leverage * risk_per_trade_pct
    return max_position_value / price


def synthetic_arbitrage_strategy(data, params):
    """Execute synthetic arbitrage strategy"""
    balance = params['initial_balance']
    initial_balance = balance
    leverage = params['leverage']
    trades = []
    position = None

    logging.info(f"Starting synthetic arbitrage strategy with balance: ${balance}")

    for i in range(1, len(data)):
        current_row = data.iloc[i]

        # Generate synthetic prices
        real_price = current_row['close']
        synthetic_a, synthetic_b = generate_synthetic_prices(real_price)

        # Market conditions check
        volume_active = current_row['Volume'] > current_row['Volume MA']
        rsi_stable = (config.RSI_LOWER_BOUND < current_row['RSI'] < config.RSI_UPPER_BOUND
                      if not pd.isna(current_row['RSI']) else False)

        if position is None:
            # Check for arbitrage opportunity
            arb_exists, profit_potential = calculate_arbitrage_opportunity(synthetic_a, synthetic_b)

            if arb_exists and volume_active and rsi_stable:
                # Calculate position sizes for both legs
                position_size = calculate_position_size(
                    balance,
                    max(synthetic_a, synthetic_b),
                    leverage,
                    params['risk_per_trade_pct']
                )

                if synthetic_a > synthetic_b:
                    position = {
                        'type': 'A-B',
                        'short_price': synthetic_a,
                        'long_price': synthetic_b,
                        'size': position_size,
                        'entry_time': current_row.name
                    }
                else:
                    position = {
                        'type': 'B-A',
                        'short_price': synthetic_b,
                        'long_price': synthetic_a,
                        'size': position_size,
                        'entry_time': current_row.name
                    }

                logging.info(f"""
                Arbitrage Entry:
                Time: {current_row.name}
                Type: {position['type']}
                Short Price: {position['short_price']:.2f}
                Long Price: {position['long_price']:.2f}
                Size: {position['size']:.2f}
                Potential Profit: {profit_potential:.2f}
                """)

        else:
            # Check exit conditions
            current_spread = abs(synthetic_a - synthetic_b)
            original_spread = abs(position['short_price'] - position['long_price'])

            # Exit if spread has narrowed significantly or timeout
            if (current_spread < original_spread * config.SPREAD_CLOSURE_THRESHOLD or
                    (current_row.name - position['entry_time']).total_seconds() > config.POSITION_TIMEOUT):

                # Calculate PnL
                if position['type'] == 'A-B':
                    pnl = position['size'] * ((position['short_price'] - synthetic_a) +
                                              (synthetic_b - position['long_price']))
                else:
                    pnl = position['size'] * ((position['short_price'] - synthetic_b) +
                                              (synthetic_a - position['long_price']))

                # Apply transaction costs
                pnl -= position['size'] * (position['short_price'] + position['long_price']) * params[
                    'transaction_cost']

                balance += pnl
                trades.append({
                    'entry_time': position['entry_time'],
                    'exit_time': current_row.name,
                    'type': position['type'],
                    'pnl': pnl,
                    'balance': balance
                })

                logging.info(f"""
                Arbitrage Exit:
                Time: {current_row.name}
                Type: {position['type']}
                PnL: ${pnl:.2f}
                New Balance: ${balance:.2f}
                """)

                position = None

                # Risk management stop
                if balance < initial_balance * (1 - config.MAX_DRAWDOWN_PCT):
                    logging.warning(f"Strategy stopped - Significant losses. Balance: ${balance:.2f}")
                    break

    # Calculate performance metrics
    total_trades = len(trades)
    if total_trades > 0:
        profitable_trades = len([t for t in trades if t['pnl'] > 0])
        win_rate = (profitable_trades / total_trades) * 100
        total_profit = sum(t['pnl'] for t in trades)
        max_drawdown = min(t['balance'] for t in trades) - initial_balance if trades else 0
    else:
        profitable_trades = win_rate = total_profit = max_drawdown = 0

    # Log final performance metrics
    logging.info(f"""
    Final Results:
    Initial Balance: ${initial_balance:,.2f}
    Final Balance: ${balance:,.2f}
    Total Profit/Loss: ${total_profit:,.2f}
    Return: {((balance - initial_balance) / initial_balance) * 100:.2f}%
    Total Trades: {total_trades}
    Win Rate: {win_rate:.2f}%
    Max Drawdown: ${abs(max_drawdown):,.2f}
    """)

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


# Strategy parameters from config
params = {
    'initial_balance': config.INITIAL_BALANCE,
    'leverage': config.LEVERAGE,
    'risk_per_trade_pct': config.RISK_PER_TRADE_PCT,
    'transaction_cost': config.TRANSACTION_COST,
}

if __name__ == "__main__":
    try:
        # Load data
        data = pd.read_csv(config.DATA_FILE, parse_dates=[config.DATE_COLUMN])
        data.set_index(config.DATE_COLUMN, inplace=True)

        # Calculate technical indicators using TA-Lib
        data_with_indicators = calculate_technical_indicators(data)

        # Run strategy
        results = synthetic_arbitrage_strategy(data_with_indicators, params)

    except Exception as e:
        logging.error(f"Error in strategy execution: {str(e)}")