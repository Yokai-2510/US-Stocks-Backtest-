import yfinance as yf
import pandas as pd
import talib
from datetime import datetime, timedelta
from tqdm import tqdm

def get_price_metrics(data):
    #   Calculate 20-day average price
    latest_data = data.tail(20)
    avg_price = latest_data['Close'].mean()
    return avg_price

def get_volume_metrics(data):
    #   Calculate 20-day average dollar volume
    latest_data = data.tail(20)
    daily_dollar_volume = latest_data['Close'] * latest_data['Volume']
    avg_dollar_volume = daily_dollar_volume.mean()
    return avg_dollar_volume

def get_atr_metrics(data, period=10):
    #   Calculate 10-day ATR % using TA-Lib
    atr = talib.ATR(data['High'].values, data['Low'].values, 
                    data['Close'].values, timeperiod=period)
    
    # Calculate ATR as percentage of closing price
    latest_close = data['Close'].iloc[-1]
    atr_pct = (atr[-1] / latest_close) * 100
    
    return atr_pct

def get_rsi_metrics(data, periods=3):
    #   Calculate 3-day RSI using TA-Lib
    rsi = talib.RSI(data['Close'].values, timeperiod=periods)
    return rsi[-1]

def get_consecutive_close_metrics(data):
    #   Check for two consecutive higher closes
    closes = data['Close'].tail(3).values
    return (closes[1] > closes[0]) and (closes[2] > closes[1])

def get_adx_metrics(data, period=7):
    #   Calculate 7-day ADX using TA-Lib
    adx = talib.ADX(data['High'].values, data['Low'].values, 
                    data['Close'].values, timeperiod=period)
    return adx[-1]

def analyze_stocks(tickers, end_date):
    #   Main analysis function
    results = []
    error_records = []
    failed_downloads = []
    start_date = end_date - timedelta(days=40)  # Get more data for proper calculation
    
    # Clean tickers and convert to string
    tickers = [str(ticker).strip().upper() for ticker in tickers if pd.notna(ticker)]
    
    # Download all stock data at once
    print("Downloading data for all stocks...")
    try:
        data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker')
        # Check which tickers failed to download
        if len(tickers) > 1:
            available_tickers = set(data.columns.get_level_values(0).unique())
            failed_tickers = set(tickers) - available_tickers
            for ticker in failed_tickers:
                failed_downloads.append({
                    'Ticker': ticker,
                    'Error': 'Failed to download data'
                })
    except Exception as e:
        print(f"Error downloading data: {e}")
        # Extract failed tickers from the error message
        if 'YFPricesMissingError' in str(e) or 'YFTzMissingError' in str(e):
            error_parts = str(e).split("'")
            for i in range(len(error_parts)):
                if '[' in error_parts[i]:
                    tickers_str = error_parts[i].strip('[]').replace("'", "").replace(" ", "")
                    failed_tickers = tickers_str.split(',')
                    for ticker in failed_tickers:
                        failed_downloads.append({
                            'Ticker': ticker,
                            'Error': str(e)
                        })
    
    for ticker in tqdm(tickers, desc="Analyzing stocks"):
        try:
            # Skip if ticker is in failed downloads
            if any(fd['Ticker'] == ticker for fd in failed_downloads):
                continue
                
            # Extract individual stock data
            if len(tickers) == 1:
                hist = data
            else:
                hist = data[ticker].copy()
            
            if hist.empty or len(hist) < 20:
                error_records.append({
                    'Ticker': ticker,
                    'Error': 'Insufficient data (less than 20 days)'
                })
                continue
                
            result = {
                'Ticker': ticker,
                'Avg Price': round(get_price_metrics(hist), 2),
                'Avg Dollar Volume': round(get_volume_metrics(hist), 2),
                'ATR %': round(get_atr_metrics(hist), 2),
                '3-day RSI': round(get_rsi_metrics(hist), 2),
                'Higher Closes': get_consecutive_close_metrics(hist),
                '7-day ADX': round(get_adx_metrics(hist), 2)
            }
            results.append(result)
            
        except Exception as e:
            error_records.append({
                'Ticker': ticker,
                'Error': str(e)
            })
            print(f"Error processing {ticker}: {e}")
            continue
            
    # Save error records
    if error_records:
        pd.DataFrame(error_records).to_csv("data/error_stocks.csv", index=False)
        print("\nError records saved to: data/error_stocks.csv")
    
    # Save failed downloads
    if failed_downloads:
        pd.DataFrame(failed_downloads).to_csv("data/failed_downloads.csv", index=False)
        print("\nFailed downloads saved to: data/failed_downloads.csv")
            
    return pd.DataFrame(results)

    
def filter_stocks(df):
    #   Apply filtering criteria and rank stocks
    
    # Base filters 
    df['Pass Price'] = df['Avg Price'] >= 5.0
    df['Pass Volume'] = df['Avg Dollar Volume'] >= 25_000_000
    df['Pass ATR'] = df['ATR %'] >= 3.0
    base_filtered = df['Pass Price'] & df['Pass Volume'] & df['Pass ATR']
    
    # Entry conditions 
    df['Pass RSI'] = (df['3-day RSI'] >= 90) & base_filtered 
    df['Pass Higher Closes'] = df['Higher Closes'] & base_filtered
    entry_filtered = df['Pass RSI'] & df['Pass Higher Closes']
    
    # Final filtering
    df['Pass Base Filters'] = base_filtered
    df['Pass All'] = entry_filtered & base_filtered
    
    # Get top stocks ranked by ADX
    ranked_stocks = df[df['Pass All']].nlargest(10, '7-day ADX')

    # Save results
    df[df['Pass All']].to_csv("data/filtered_stocks.csv", index=False)
    print("\nResults saved to: data/filtered_stocks.csv")
    ranked_stocks.to_csv("data/ranked_stocks.csv", index=False)
    print("Ranked results saved to: data/ranked_stocks.csv")
    
    # Print statistics
    print("\n=== Screening Results ===")
    print(f"Total Stocks Analyzed: {len(df)}")
    
    print("\n--- Base Filtering Criteria ---")
    print(f"• Price >= $5.00: {df['Pass Price'].sum()} stocks")
    print(f"• Average Daily Volume >= $25M: {df['Pass Volume'].sum()} stocks")
    print(f"• ATR% >= 3.0%: {df['Pass ATR'].sum()} stocks")
    print(f"→ Stocks Passing All Base Filters: {df['Pass Base Filters'].sum()} stocks")
    
    print("\n--- Entry Criteria ---")
    print(f"• 3-day RSI >= 90: {df['Pass RSI'].sum()} stocks")
    print(f"• Two Consecutive Higher Closes: {df['Pass Higher Closes'].sum()} stocks")
    print(f"→ Stocks Passing All Criteria: {df['Pass All'].sum()} stocks")
    
    return ranked_stocks


def filtered_stocks(end_date):

    # Read tickers
    tickers = pd.read_csv("data/tickers.csv")["Ticker"].tolist()
    
    # Analyze stocks
    results_df = analyze_stocks(tickers, end_date)
    
    # Filter and rank stocks
    top_stocks = filter_stocks(results_df)

    return top_stocks

if __name__ == "__main__":
    end_date = datetime(2025, 1, 1)
    filtered_stocks(end_date)
