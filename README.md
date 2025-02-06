# ArthaVedh-Internship-Work

# ArthaVedh Internship Work

This repository contains a Python-based trading strategy simulation that uses various technical indicators such as RSI, Moving Averages, MACD, and Volume for stock market analysis. The strategy is designed for backtesting stock market data and generating insights.

---

## **Prerequisites**

Before running this project, ensure you have the following installed on your system:

### **1. Python**
- **Version:** Python 3.7 or higher.
- Download and install Python from the [official Python website](https://www.python.org/downloads/).

### **2. Git**
- Install Git to clone this repository.
- Download Git from the [official Git website](https://git-scm.com/).

### **3. TA-Lib Library**

The project uses the TA-Lib library for calculating technical indicators. Follow the steps below to install it:

#### **Windows**
1. Download the appropriate **TA-Lib .whl** file (binary) from the [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib).
    - Choose the file that matches your Python version and architecture (e.g., `TA_Lib‑0.4.0‑cp310‑cp310‑win_amd64.whl` for Python 3.10 on a 64-bit machine).
2. Use `pip` to install the downloaded `.whl` file:

   ```bash
   pip install <path_to_downloaded_whl_file>
   ```

#### **Linux**
1. Install the **TA-Lib C library**:

   For Ubuntu/Debian:
   ```bash
   sudo apt-get install libta-lib0-dev
   ```

   For RedHat/CentOS:
   ```bash
   sudo yum install ta-lib
   ```

2. Install the Python wrapper using pip:

   ```bash
   pip install TA-Lib
   ```

#### **macOS**
1. Install the **TA-Lib C library** using Homebrew:

   ```bash
   brew install ta-lib
   ```

2. Install the Python wrapper using pip:

   ```bash
   pip install TA-Lib
   ```

#### **Verify Installation**
To confirm that TA-Lib is installed correctly, run the following command in Python:

```python
import talib
print(talib.get_functions())
```

If installed successfully, you will see a list of available TA-Lib functions.

---

## **Installation Instructions**

Follow these steps to set up the project locally:

1. Clone the repository:

   ```bash
   git clone https://github.com/Swarajhere/ArthaVedh-Internship-Work.git
   cd ArthaVedh-Internship-Work
   ```

2. Create and activate a virtual environment (optional but recommended):

   For Windows:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

   For Linux/macOS:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:

   ```bash
   pip install numpy pandas
   ```

4. Place your data file (e.g., `NSE_NIFTY_1_Intraday.csv`) in the `data` directory. Ensure the file matches the required structure (columns: `open`, `high`, `low`, `close`, `Volume`).

5. Update the `config.py` file if necessary to match your data and configuration preferences.

---

## **Usage Instructions**

To run the trading strategy simulation:

1. Run the main script:

   ```bash
   python strategy_name.py
   ```

2. Monitor the console and log file for results and performance metrics. Key outputs include:
   - Total trades
   - Successful trades
   - Win rate
   - Final balance
   - Total profit or loss (P&L)

---

## **Project Structure**

```plaintext
Arthaved-internship-work/
├── /four folders of each member           
    ├── strategy1                   
    ├── strategy2   
    ├── ................         
    ├── strategyn   

```

```plaintext
Strategy_example/
├── .csv file                 
├── logs/                  # Directory for log files
├── main.py                # Main script to run the strategy
├── config.py              # Configuration file
└── ...                    # Other project files
```


