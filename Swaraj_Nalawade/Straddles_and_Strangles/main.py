# Run python main.py straddle or python main.py strangle to execute the desired strategy

# main.py

from market_data import MarketDataManager
from straddle_strategy import run_straddle_strategy
from strangle_strategy import run_strangle_strategy
import config
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py [straddle|strangle]")
        sys.exit(1)
    
    strategy = sys.argv[1].lower()
    
    # Initialize market data manager
    try:
        market_data_manager = MarketDataManager(config.DATA_FILE)
    except Exception as e:
        print(f"Error loading market data: {e}")
        sys.exit(1)
    
    # Run selected strategy
    if strategy == "straddle":
        final_balance = run_straddle_strategy(market_data_manager)
    elif strategy == "strangle":
        final_balance = run_strangle_strategy(market_data_manager)
    else:
        print("Invalid strategy. Choose either 'straddle' or 'strangle'")
        sys.exit(1)
    
    # Print final results
    print("\nStrategy Completed!")
    print(f"Initial Balance: ${config.INITIAL_BALANCE:,.2f}")
    print(f"Final Balance: ${final_balance:,.2f}")
    print(f"Total P&L: ${(final_balance - config.INITIAL_BALANCE):,.2f}")
    print(f"Return: {((final_balance - config.INITIAL_BALANCE) / config.INITIAL_BALANCE * 100):,.2f}%")

if __name__ == "__main__":
    main()
