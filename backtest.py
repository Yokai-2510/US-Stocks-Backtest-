# backtest.py


import backtrader as bt
import pandas as pd
import json
from datetime import datetime
from data_analysis import fetch_data
from create_reports import create_reports
from strategy import ShortRSIStrategy

def run_backtest(cerebro, stock_dfs, ranked_stocks, config):

    # Set exact dates for backtest period
    fromdate = datetime.strptime(config["start_date"], "%Y-%m-%d")
    todate = datetime.strptime(config["end_date"], "%Y-%m-%d")
    
    # Add data feeds to Cerebro with explicit date range
    for symbol, stock_df in stock_dfs.items():
        if stock_df is not None:
            data = bt.feeds.PandasData(
                dataname=stock_df,
                name=symbol,
                fromdate=fromdate,  
                todate=todate   )
            cerebro.adddata(data)
    
    # Add strategy and pass ranked_stocks data and config
    cerebro.addstrategy(ShortRSIStrategy, ranked_stocks=ranked_stocks, config=config)
    cerebro.broker.setcash(config["capital"])
    cerebro.broker.setcommission(commission=config["commission"])
    
    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    
    return cerebro.run()

if __name__ == "__main__"   :

    print("\nRunning backtest...\n")
    # Load configuration from config.json
    with open("source/config.json") as f:
        config = json.load(f)

    cerebro = bt.Cerebro()  # Initialize Cerebro engine

    # Load ranked stocks data
    ranked_stocks = pd.read_csv("data/stocks_ranked.csv")
    ranked_stocks['Date'] = pd.to_datetime(ranked_stocks['Date']).dt.date    # Convert Date column to datetime
    symbols = ranked_stocks['Ticker'].unique().tolist()     # Get unique tickers from ranked_stocks 
    
    # Fetch data for all symbols
    stock_dfs = fetch_data(symbols, config)

    # Run backtest with explicit date handling
    print("\nRunning backtest ...\n")
    results = run_backtest(cerebro, stock_dfs, ranked_stocks, config)

    # Create reports
    create_reports(config,results, ranked_stocks)

    print("\nBacktest completed successfully!\n")
    # cerebro.plot()  # Plot the strategy
