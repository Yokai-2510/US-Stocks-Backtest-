
# data_analysis.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_data(symbols, config):

    # Calculate lookback period for indicators (ATR period + buffer)
    lookback_days = config.get('atr_period', 10) + 15  # Adding buffer days
    
    # Adjust start date for lookback
    start_date = datetime.strptime(config["start_date"], "%Y-%m-%d") - timedelta(days=lookback_days)
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    print(f"Fetching data from {start_date_str} to include lookback period for all Stocks ")
    print(f"Actual start date : { config["start_date"]} ")
    
    try:
        df = yf.download(symbols, start=start_date_str, end=config["end_date"])
        print(f"Stocks data downloaded successfully")
    except Exception as e:
        print(f"Error downloading data: {e}")
        return {}
    
    stock_dfs = {}
    
    for symbol in symbols:
        try:
            # Extract single symbol data
            if isinstance(df.columns, pd.MultiIndex):
                symbol_data = df.xs(symbol, level=1, axis=1)
            else:
                symbol_data = df.copy()
            
            # Ensure proper data formatting
            symbol_data.index = pd.to_datetime(symbol_data.index)
            symbol_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            symbol_data.sort_index(inplace=True)
            
            # Validate data quality
            if not symbol_data.empty and not symbol_data.isnull().any().any():
                stock_dfs[symbol] = symbol_data
            else:
                print(f"Warning: Invalid or missing data for symbol {symbol}")
                
        except Exception as e:  
            print(f"Error processing {symbol}: {e}")
            continue
    
    # Verify we have sufficient lookback data
    for symbol, df in stock_dfs.items():
        data_start = df.index.min().strftime("%Y-%m-%d")
        if data_start > start_date_str:
            print(f"Warning: {symbol} data starts from {data_start}, which may not provide sufficient lookback")
    
    return stock_dfs
