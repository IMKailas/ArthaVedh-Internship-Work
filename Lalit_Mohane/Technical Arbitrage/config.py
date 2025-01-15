# config.py

import logging

# Configuration object for strategy parameters and logging
class Config:
    # Strategy Parameters
    LOWER_BAND_MULTIPLIER = 1.02
    UPPER_BAND_MULTIPLIER = 0.98
    RSI_BUY_THRESHOLD = 45
    RSI_SELL_THRESHOLD = 55
    VWAP_VOLUME_THRESHOLD = 500000

    # File paths
    CSV_FILE = "NSE_NIFTY, 1 Intraday.csv"
    LOG_FILE = "trading_strategy.log"

    # Logging Configuration
    LOGGING = {
        "level": logging.DEBUG,
        "format": "%(asctime)s - %(levelname)s - %(message)s",
        "filemode": "w"
    }

    @staticmethod
    def setup_logging():
        """Sets up logging configuration."""
        logging.basicConfig(
            filename=Config.LOG_FILE,
            level=Config.LOGGING["level"],
            format=Config.LOGGING["format"],
            filemode=Config.LOGGING["filemode"]
        )
