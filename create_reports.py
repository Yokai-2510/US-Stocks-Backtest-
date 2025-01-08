import pandas as pd
import numpy as np

# create_reports.py
def analyze_trades(trades_df: pd.DataFrame, strategy) -> None:

    # Convert trading days to datetime if they aren't already
    strategy.trading_days = pd.to_datetime(strategy.trading_days)
    
    trades_df['TradingDays'] = trades_df['ExitBar'] - trades_df['EntryBar']
    trades_df['TradeNumber'] = range(1, len(trades_df) + 1)
    trades_df['CumulativePnL'] = trades_df['PnL'].cumsum()
    trades_df['PeakPnL'] = trades_df['CumulativePnL'].cummax()
    trades_df['Drawdown'] = trades_df['PeakPnL'] - trades_df['CumulativePnL']
    trades_df['ExitReason'] = trades_df['ExitBar'].map(strategy.exit_reasons)
    
    exit_metrics = pd.DataFrame.from_dict(strategy.exit_metrics, orient='index')
    trades_df = trades_df.join(exit_metrics, on='ExitBar')
    
    equity_curve = pd.Series(index=strategy.trading_days)
    position_sizes = pd.Series(index=strategy.trading_days, data=0.0)
    
    for idx, trade in trades_df.iterrows():
        mask = (strategy.trading_days >= trade['EntryTime']) & \
               (strategy.trading_days <= trade['ExitTime'])
        position_sizes[mask] += trade['Size']
    
    for i in range(1, len(strategy.trading_days)):
        if i < len(strategy.data.Close):
            price_change = strategy.data.Close[i] - strategy.data.Close[i-1]
            equity_curve[strategy.trading_days[i]] = price_change * position_sizes[strategy.trading_days[i-1]]
    
    daily_returns = equity_curve / strategy.INITIAL_CASH
    
    if len(daily_returns) > 0:
        overall_annual_return = daily_returns.mean() * 252
        overall_annual_vol = daily_returns.std() * np.sqrt(252)
        overall_sharpe = (overall_annual_return / overall_annual_vol 
                         if overall_annual_vol != 0 else 0)
        
        trades_df['StrategyAnnualReturn'] = overall_annual_return
        trades_df['StrategyAnnualVol'] = overall_annual_vol
        trades_df['StrategySharpe'] = overall_sharpe
        
        for idx, trade in trades_df.iterrows():
            mask = (strategy.trading_days >= trade['EntryTime']) & \
                   (strategy.trading_days <= trade['ExitTime'])
            trade_returns = daily_returns[mask]
            
            if len(trade_returns) > 0:
                trades_df.at[idx, 'TradeReturn'] = trade_returns.sum()
                trades_df.at[idx, 'TradeSharpe'] = (
                    (trade_returns.mean() * 252) / (trade_returns.std() * np.sqrt(252))
                    if trade_returns.std() != 0 else 0
                )

        # Save positions data
    positions_df = pd.DataFrame({
        'Date': strategy.trading_days,
        'Position': position_sizes,
        'PnL': equity_curve,
        'Return': daily_returns
    })
    
    # Create metrics summary
    metrics_summary = pd.DataFrame({
        'Metric': [
            'Daily Returns Mean',
            'Annual Return',
            'Annual Volatility',
            'Sharpe Ratio',
            'Avg Position Size',
            'Avg Daily PnL',
            'Total PnL'
        ],
        'Value': [
            daily_returns.mean(),
            overall_annual_return if 'overall_annual_return' in locals() else 0,
            overall_annual_vol if 'overall_annual_vol' in locals() else 0,
            overall_sharpe if 'overall_sharpe' in locals() else 0,
            position_sizes.mean(),
            equity_curve.mean(),
            equity_curve.sum()
        ]
    })
    
    # Save all data files
    trades_df.to_csv('reports/trades.csv')
    print ("All trades saved to reports/trades.csv")
    metrics_summary.to_csv('reports/metrics_debug.csv')
    print ("Metrics summary saved to reports/metrics_debug.csv")
    positions_df.to_csv('reports/positions_debug.csv')
    print ("Positions data saved to reports/positions_debug.csv")

def save_summary_report(stats: pd.Series, trades_df: pd.DataFrame, strategy_class: type) -> None:
    summary = [
        "=== Backtest Summary ===",
        f"Symbol: {strategy_class.SYMBOL}",
        f"Period: {stats['Start']} to {stats['End']}",
        f"Total Return: {stats['Return [%]']:.2f}%",
        f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}",
        f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%",
        f"Number of Trades: {stats['# Trades']}",
        f"Win Rate: {stats['Win Rate [%]']:.2f}%",
        "\n=== Trade Statistics ===",
        f"Average Trade Duration: {trades_df['TradingDays'].mean():.1f} days",
        f"Average Profit per Trade: ${trades_df['PnL'].mean():.2f}",
        f"Largest Win: ${trades_df['PnL'].max():.2f}",
        f"Largest Loss: ${trades_df['PnL'].min():.2f}"
    ]
    
    with open('reports/backtest_summary.txt', 'w') as f:
        f.write('\n'.join(summary))
    print ("Backtest summary saved to reports/backtest_summary.txt")


if __name__ == "__main__":
    analyze_trades(pd.DataFrame(), None)
    save_summary_report(pd.Series(), pd.DataFrame(), None)