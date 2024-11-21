import yfinance as yf
import numpy as np
import scipy.stats as si


# Function to calculate the option's delta using the Black-Scholes formula
def black_scholes_delta(S, K, T, r, sigma, option_type='call'):
    """
    S : current stock price
    K : strike price
    T : time to expiration in years
    r : risk-free interest rate (annual)
    sigma : volatility (annual)
    option_type : 'call' for call option, 'put' for put option
    """
    # Calculate d1 in the Black-Scholes formula
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    if option_type == 'call':
        delta = si.norm.cdf(d1)  # CDF of the standard normal distribution for call
    elif option_type == 'put':
        delta = si.norm.cdf(d1) - 1  # CDF for put
    else:
        raise ValueError("Option type must be either 'call' or 'put'")

    return delta


# Function to fetch stock data using yfinance
def fetch_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data


# Function to implement delta-neutral strategy
def delta_neutral_strategy(ticker, option_type='call', strike_price=100, days_to_expiration=30, risk_free_rate=0.05,
                           volatility=0.2):
    # Fetch stock data
    stock_data = fetch_stock_data(ticker, '2024-01-01', '2024-12-31')

    # Loop through stock data and calculate delta-neutral position
    for index, row in stock_data.iterrows():
        S = row['Close']  # current stock price
        T = days_to_expiration / 365  # Convert days to expiration to years

        # Calculate the option delta using Black-Scholes
        delta = black_scholes_delta(S, strike_price, T, risk_free_rate, volatility, option_type)

        # To maintain delta-neutral, you need to hold -delta number of shares of the stock per option contract
        stock_position = -delta  # Number of shares to hold to be delta-neutral

        print(f"Date: {index.date()}")
        print(f"Stock Price: {S}")
        print(f"Delta: {delta}")
        print(f"Stock Position: {stock_position}")
        print("----")


# Call the delta-neutral strategy for Reliance Industries (RELIANCE.NS)
delta_neutral_strategy('RELIANCE.NS', option_type='call', strike_price=2500, days_to_expiration=30, risk_free_rate=0.05,
                       volatility=0.25)
