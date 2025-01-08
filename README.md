## Installation

### 1. Set Up Virtual Environment (Optional)
- **Windows:**
  ```bash
  python -m venv .venv
  .\.venv\Scripts\activate
  ```
- **macOS/Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
cd source
pip install .\ta_lib-0.5.1-cp312-cp312-win_amd64.whl
```

## Execution

- Run the `filter_stocks.py` script to generate reports for ADX-ranked filtered stocks.
- Use the filtered stocks in the `backtest_stock.py` script to backtest a single stock.
- The results will be saved in the `reports` folder.
- Reports include:
  - **HTML report**  
  - **backtest_summary.txt** (Summary of trade statistics; note: Sharpe ratio has a bug)
  - **metrics_debug.csv** (Accurate trade stats with fixed Sharpe ratio)
  - **positions_debug.csv** (Records all trade activity for each trading day)
  - **trades.csv** (Records all trades and their stats; main file for reports along with the HTML report)
