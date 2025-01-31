import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import talib
import pandas as pd

# --- Indicator Calculation ---

def calculate_price_average(data: pd.DataFrame, period: int = 20) -> float:
    """Calculates the average closing price over a specified period."""
    return data['Close'].tail(period).mean()

def calculate_dollar_volume(data: pd.DataFrame, period: int = 20) -> float:
    """Calculates the average dollar volume over a specified period."""
    latest_data = data.tail(period)
    return (latest_data['Close'] * latest_data['Volume']).mean()

def calculate_atr_percentage(data: pd.DataFrame, period: int = 10) -> float:
    """Calculates the ATR as a percentage of the closing price."""
    atr = talib.ATR(data['High'].values, data['Low'].values,
                    data['Close'].values, timeperiod=period)
    return (atr[-1] / data['Close'].iloc[-1]) * 100 if len(atr) > 0 and data['Close'].iloc[-1] != 0 else 0

def calculate_rsi(data: pd.DataFrame, period: int = 3) -> float:
    """Calculates the RSI for a specified period."""
    rsi_values = talib.RSI(data['Close'].values, timeperiod=period)
    return rsi_values[-1] if len(rsi_values) > 0 else 0

def check_consecutive_closes(data: pd.DataFrame) -> bool:
    """Checks for two consecutive higher closes."""
    closes = data['Close'].tail(3).values
    return (closes[1] > closes[0]) and (closes[2] > closes[1]) if len(closes) >= 3 else False

def calculate_adx(data: pd.DataFrame, period: int = 7) -> float:
    """Calculates the ADX for a specified period."""
    adx_values = talib.ADX(data['High'].values, data['Low'].values,
                    data['Close'].values, timeperiod=period)
    return adx_values[-1] if len(adx_values) > 0 else 0

def calculate_indicators(data: pd.DataFrame) -> dict:
    """Calculates all technical indicators for a given stock's data."""
    if len(data) < 20:
        return {}
    return {
        'Avg Price': calculate_price_average(data),
        'Avg Dollar Volume': calculate_dollar_volume(data),
        'ATR %': calculate_atr_percentage(data),
        '3-day RSI': calculate_rsi(data),
        'Higher Closes': check_consecutive_closes(data),
        '7-day ADX': calculate_adx(data)
    }


# --- Constants ---
DATE_FORMAT = "%Y-%m-%d"
LOOKBACK_PERIOD = 50  # Lookback period for indicator calculations (in calendar days)



# --- Data Fetching ---

def download_stock_data(tickers: list, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Downloads historical stock data for all tickers, considering the lookback period."""
    print("Downloading stock data...")
    
    # Calculate the actual start date for data download
    actual_start_date = start_date - timedelta(days=LOOKBACK_PERIOD)
    
    tickers = [str(ticker).strip().upper() for ticker in tickers if pd.notna(ticker)]
    try:
        data = yf.download(tickers, start=actual_start_date, end=end_date, group_by='ticker')
        if data.empty:
            print("No data found from yfinance.")
        return data
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()



# --- Filtering ---

def apply_base_filters(row: pd.Series) -> bool:
    """Applies the base filtering criteria to a single row of data."""
    return (
        row['Avg Price'] >= 5.0 and
        row['Avg Dollar Volume'] >= 25_000_000 and
        row['ATR %'] >= 3.0
    )

def apply_entry_filters(row: pd.Series) -> bool:
    """Applies the entry filtering criteria to a single row of data."""
    return (
        row['Pass Base'] and
        row['3-day RSI'] >= 90 and
        row['Higher Closes']
    )



# --- Processing and Saving ---

def process_stock_data(tickers: list, start_date: datetime, end_date: datetime, all_data_path: str, ranked_data_path: str, data: pd.DataFrame):

    all_data_df = pd.DataFrame(columns=['Date', 'Ticker', 'Avg Price', 'Avg Dollar Volume', 'ATR %', '3-day RSI', 'Higher Closes', '7-day ADX', 'Pass Base', 'Pass All'])
    ranked_data_df = pd.DataFrame(columns=['Date', 'Ticker', 'Avg Price', 'Avg Dollar Volume', 'ATR %', '3-day RSI', 'Higher Closes', '7-day ADX', 'Pass Base', 'Pass All'])

    for current_date in tqdm(pd.date_range(start=start_date, end=end_date), desc="Processing Dates"):
        current_date_str = current_date.strftime(DATE_FORMAT)

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    hist = data.loc[:current_date_str]
                else:
                    hist = data[ticker].loc[:current_date_str]

                # Check for sufficient data, considering the lookback period
                if len(hist) < 20:  # 20 is the minimum for some indicators
                    print(f"Insufficient data for {ticker} on {current_date_str} (less than 20 rows)")
                    continue

                indicators = calculate_indicators(hist)
                if not indicators:
                    continue

                row = {
                    'Date': current_date_str,
                    'Ticker': ticker,
                    **indicators
                }
                row_df = pd.DataFrame([row])
                row_df['Pass Base'] = row_df.apply(apply_base_filters, axis=1)
                row_df['Pass All'] = row_df.apply(apply_entry_filters, axis=1)

                all_data_df = pd.concat([all_data_df, row_df], ignore_index=True)

                if row_df['Pass All'].iloc[0]:
                    ranked_data_df = pd.concat([ranked_data_df, row_df], ignore_index=True)

            except Exception as e:
                print(f"Error processing {ticker} on {current_date_str}: {e}")

    if not ranked_data_df.empty:
        ranked_data_df = ranked_data_df.groupby('Date').apply(
            lambda x: x.nlargest(10, '7-day ADX')
        ).reset_index(drop=True)

    all_data_df.to_csv(all_data_path, index=False)
    ranked_data_df.to_csv(ranked_data_path, index=False)

    print(f"All data saved to {all_data_path}")
    print(f"Ranked data saved to {ranked_data_path}")



# --- Main Execution ---

if __name__ == "__main__" : 
    
    # Example usage
    tickers = pd.read_csv("source/tickers.csv")["Ticker"].head(100).tolist()
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 1, 1)
    all_data_path = "data/all_stocks_data_final_1.csv"
    ranked_data_path = "data/ranked_stocks_final_1.csv"

    # Download data with lookback period
    all_data = download_stock_data(tickers, start_date, end_date)

    if not all_data.empty:
        # Process the downloaded data
        process_stock_data(tickers, start_date, end_date, all_data_path, ranked_data_path, all_data)