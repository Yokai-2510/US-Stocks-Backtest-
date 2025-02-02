## Installation

#### 1. Download the Entire Repo 
  - Set Up Virtual Environment (Optional but Strongly recommended)

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```


In case installing TA-lib throws an error , use this to install TA -lib library .
Link to Download : https://github.com/cgohlke/talib-build/release
```bash
cd source
```
```bash
pip install .\ta_lib-0.5.1-cp312-cp312-win_amd64.whl
```


## Execution

- Run the `filter_stocks.py` script to generate reports for ADX-ranked filtered stocks. It will contain the list of ADX ranked stocks for the date mnetioned in the script .
- To backtest a single stock , run the  `backtest_stock.py` . It will automatically generate and save reports and also open up a browser tab with the reports. 
- All the reports will be saved in the `reports` folder for both the `backtest_stock.py` and `filter_stocks.py` script .
- Both the scripts will have easily editable configurations like start data , end date etc .
  
## Reports include:
  - **HTML report**  
  - **backtest_summary.txt** (Summary of trade statistics; note: Sharpe ratio has a bug)
  - **metrics_debug.csv** (Accurate trade stats with fixed Sharpe ratio)
  - **positions_debug.csv** (Records all trade activity for each trading day)
  - **trades.csv** (Records all trades and their stats; main file for reports along with the HTML report)
