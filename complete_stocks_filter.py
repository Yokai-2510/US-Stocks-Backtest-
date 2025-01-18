import yfinance as yf
import pandas as pd
import talib
from datetime import datetime, timedelta
from tqdm import tqdm


def fetch_stock_data(tickers, start_date, end_date):
    """Fetch historical stock data for a list of tickers."""
    print("Downloading data for all stocks...")
    try:
        return yf.download(tickers, start=start_date, end=end_date, group_by='ticker')
    except Exception as e:
        print(f"Error downloading data: {e}")
        return pd.DataFrame()


def get_metrics_for_date(data, date):

    def calculate_avg_price(data):
        """Calculate 20-day average price."""
        latest_data = data.tail(20)
        return latest_data['Close'].mean()

    def calculate_avg_dollar_volume(data):
        """Calculate 20-day average dollar volume."""
        latest_data = data.tail(20)
        daily_dollar_volume = latest_data['Close'] * latest_data['Volume']
        return daily_dollar_volume.mean()

    def calculate_atr_percentage(data, period=10):
        """Calculate ATR percentage."""
        atr = talib.ATR(data['High'].values, data['Low'].values, data['Close'].values, timeperiod=period)
        latest_close = data['Close'].iloc[-1]
        return (atr[-1] / latest_close) * 100

    def calculate_rsi(data, period=3):
        """Calculate RSI."""
        rsi = talib.RSI(data['Close'].values, timeperiod=period)
        return rsi[-1]

    def check_consecutive_higher_closes(data):
        """Check for two consecutive higher closes."""
        closes = data['Close'].tail(3).values
        return (closes[1] > closes[0]) and (closes[2] > closes[1])

    def calculate_adx(data, period=7):
        """Calculate ADX."""
        adx = talib.ADX(data['High'].values, data['Low'].values, data['Close'].values, timeperiod=period)
        return adx[-1]

    mask = data.index <= pd.Timestamp(date).normalize()
    historical_data = data[mask].copy()

    if len(historical_data) < 20:
        return None

    metrics = {
        'Avg Price': round(calculate_avg_price(historical_data), 2),
        'Avg Dollar Volume': round(calculate_avg_dollar_volume(historical_data), 2),
        'ATR %': round(calculate_atr_percentage(historical_data), 2),
        '3-day RSI': round(calculate_rsi(historical_data), 2),
        'Higher Closes': check_consecutive_higher_closes(historical_data),
        '7-day ADX': round(calculate_adx(historical_data), 2)
    }

    return metrics

def filter_stocks_for_date(metrics_df):
    """Apply filtering criteria and return top ranked stocks."""
    base_filters = (
        (metrics_df['Avg Price'] >= 5.0) &
        (metrics_df['Avg Dollar Volume'] >= 25_000_000) &
        (metrics_df['ATR %'] >= 3.0)
    )

    entry_filters = (
        (metrics_df['3-day RSI'] >= 90) &
        metrics_df['Higher Closes']
    )

    final_filter = base_filters & entry_filters
    return metrics_df[final_filter].nlargest(10, '7-day ADX')


def process_historical_data(start_date, end_date):
    """Process historical data for the given date range."""
    start_date = pd.Timestamp(start_date).normalize()
    end_date = pd.Timestamp(end_date).normalize()

    print(f"Processing data from {start_date} to {end_date}")

    tickers = pd.read_csv("data/tickers.csv")["Ticker"].tolist()
    tickers = [str(ticker).strip().upper() for ticker in tickers if pd.notna(ticker)]

    download_start = start_date - timedelta(days=40)
    all_data = fetch_stock_data(tickers, download_start, end_date)

    results = []

    for current_date in tqdm(pd.date_range(start_date, end_date), desc="Processing dates"):
        daily_results = []

        for ticker in tickers:
            try:
                if len(tickers) == 1:
                    stock_data = all_data
                else:
                    stock_data = all_data[ticker].copy()

                if stock_data.empty:
                    continue

                metrics = get_metrics_for_date(stock_data, current_date)
                if metrics:
                    metrics['Ticker'] = ticker
                    daily_results.append(metrics)

            except Exception as e:
                print(f"Error processing {ticker} for {current_date}: {e}")
                continue

        if daily_results:
            daily_df = pd.DataFrame(daily_results)
            top_stocks = filter_stocks_for_date(daily_df)
            if not top_stocks.empty:
                top_stocks['Date'] = current_date.strftime('%Y-%m-%d')
                results.append(top_stocks)

    if results:
        final_df = pd.concat(results, ignore_index=True)
        final_df.to_csv("data/historical_ranked_stocks.csv", index=False)
        print("\nResults saved to: data/historical_ranked_stocks.csv")
        print(f"Total days processed: {len(final_df['Date'].unique())}")
        print(f"Total stock entries: {len(final_df)}")
        return final_df

    return pd.DataFrame()


if __name__ == "__main__":
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2025, 1, 1)
    process_historical_data(start_date, end_date)
