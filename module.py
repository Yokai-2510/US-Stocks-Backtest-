from backtesting import Backtest, Strategy
import yfinance as yf
import pandas as pd
import webbrowser
import os
from typing import Optional, Tuple
from create_reports import analyze_trades



# module.py
def download_data(strategy_class: type) -> pd.DataFrame:
    data = yf.download(strategy_class.SYMBOL, start=strategy_class.START_DATE, end=strategy_class.END_DATE)
    df = data.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df = df.xs(strategy_class.SYMBOL, axis=1, level=1, drop_level=True)
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    return df[required_columns]

def run_backtest(data: pd.DataFrame, strategy_class: type) -> Tuple[pd.Series, pd.DataFrame]:
    bt = Backtest(data, strategy_class, 
                  cash=strategy_class.INITIAL_CASH, 
                  commission=strategy_class.COMMISSION)
    stats = bt.run()
    
    trades_df = stats._trades.copy()
    analyze_trades(trades_df, stats._strategy)
    
    html_output = f"reports/backtest_report_{strategy_class.SYMBOL}.html"
    try:
        import backtesting._plotting
        original_formatter = backtesting._plotting.DatetimeTickFormatter
        
        def patched_formatter(*args, **kwargs):
            if 'days' in kwargs and isinstance(kwargs['days'], list):
                kwargs['days'] = kwargs['days'][0]
            if 'hours' in kwargs and isinstance(kwargs['hours'], list):
                kwargs['hours'] = kwargs['hours'][0]
            if 'months' in kwargs and isinstance(kwargs['months'], list):
                kwargs['months'] = kwargs['months'][0]
            if 'years' in kwargs and isinstance(kwargs['years'], list):
                kwargs['years'] = kwargs['years'][0]
            return original_formatter(*args, **kwargs)
        
        backtesting._plotting.DatetimeTickFormatter = patched_formatter
        
        bt.plot(filename=html_output, open_browser=False, superimpose=False, resample=False)
        
        backtesting._plotting.DatetimeTickFormatter = original_formatter
        
        abs_path = os.path.abspath(html_output)
        webbrowser.open('file://' + abs_path)
        
    except Exception as plot_error:
        print(f"Warning: Could not generate plot due to: {str(plot_error)}")
    
    return stats, trades_df

if __name__ == '__main__':
    data = download_data ()
    stats, trades_df = run_backtest()
