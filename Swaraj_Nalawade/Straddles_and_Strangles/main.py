# Run python main.py straddle or python main.py strangle to execute the desired strategy

# main.py

from straddle_strategy import run_straddle_strategy
from strangle_strategy import run_strangle_strategy
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py [straddle|strangle]")
        sys.exit(1)
    
    strategy = sys.argv[1].lower()
    
    if strategy == "straddle":
        run_straddle_strategy()
    elif strategy == "strangle":
        run_strangle_strategy()
    else:
        print("Invalid strategy. Choose either 'straddle' or 'strangle'")
        sys.exit(1)

if __name__ == "__main__":
    main()
