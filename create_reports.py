import pandas as pd
import os
import numpy as np
from datetime import datetime
import backtrader as bt
import json

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    # Check if returns is empty or None
    if returns is None or (isinstance(returns, pd.Series) and returns.empty):
        return 0.0
    
    try:
        # Ensure returns is a numpy array or series of numeric values
        if isinstance(returns, pd.Series):
            returns = returns.dropna().values
        
        # Check again after dropping NA values
        if len(returns) == 0:
            return 0.0
        
        returns_mean = np.mean(returns)
        returns_std = np.std(returns)
        
        # Prevent division by zero
        if returns_std == 0:
            return 0.0
        
        # Annualized Sharpe Ratio calculation
        sharpe_ratio = (returns_mean - risk_free_rate/252) / (returns_std * np.sqrt(252)) 
        return sharpe_ratio
    except Exception as e:
        print(f"Error calculating Sharpe Ratio: {e}")
        return 0.0

def create_reports(config, results, ranked_stocks):
    # Ensure reports directory exists
    os.makedirs('reports', exist_ok=True)
    
    # Create report filename with date range
    report_suffix = f"{config['start_date']}_to_{config['end_date']}"
    
    # Get strategy instance
    strategy = results[0]
    
    # Collect and process trade data
    trades_data = []
    for trade in strategy.trades:
        # Get tracking and exit details
        tracking_info = getattr(strategy, 'trade_tracking', {}).get(trade.data._name, {})
        exit_details = getattr(strategy, 'exit_details', {}).get(trade.data._name, {})
        
        if not tracking_info:
            continue
        
        # Comprehensive trade information
        trade_info = {
            'Symbol': tracking_info.get('symbol', trade.data._name),
            'Entry Date': tracking_info.get('entry_date', datetime.min).strftime("%Y-%m-%d"),
            'Exit Date': tracking_info.get('exit_date', datetime.min).strftime("%Y-%m-%d"),
            'Entry Price': tracking_info.get('entry_price', 0),
            'Exit Price': tracking_info.get('exit_price', 0),
            'Shares': abs(tracking_info.get('shares', trade.size)),  # Use tracking info shares or trade size
            'Net P/L': trade.pnlcomm,
            
            # Profit calculation with safety checks
            'Profit %': (
                ((tracking_info.get('exit_price', 0) - tracking_info.get('entry_price', 0)) / 
                 max(tracking_info.get('entry_price', 1), 0.0001)) * 100 if tracking_info.get('exit_price') else 0
            ),
            
            # Exit Criteria Details
            'Exit Reason': exit_details.get('exit_criterion', 'Unknown'),
            'Target Exit Date': exit_details.get('time_exit_date', 'N/A'),
            'Target Exit Days': exit_details.get('target_exit_days', 'N/A'),
            
            # Stop Loss Details
            'Stop Loss Price': exit_details.get('stop_loss_price', 'N/A'),
            'Stop Loss ATR Multiplier': exit_details.get('atr_multiplier', 'N/A'),
            
            # Profit Target Details
            'Profit Target Price': exit_details.get('profit_target_price', 'N/A'),
            'Profit Target %': exit_details.get('profit_target_percent', 'N/A')
        }
        trades_data.append(trade_info)

    # Convert to DataFrame
    trades_df = pd.DataFrame(trades_data)
    
    # Handle empty trades scenario
    if trades_df.empty:
        print("\nNo trades were completed during the backtest period")
        return None, {}

    # Save trades log
    trades_csv_path = f'reports/trades_{report_suffix}.csv'
    trades_df.to_csv(trades_csv_path, index=False)
    print(f"\nTrades log saved to {trades_csv_path}")

    # Calculate portfolio metrics
    initial_capital = config["capital"]
    final_value = strategy.broker.getvalue()
    total_pnl = final_value - initial_capital
    
    # Convert Profit % to numeric and handle potential conversion issues
    trade_returns = pd.to_numeric(trades_df['Profit %'], errors='coerce') / 100

    # Performance Metrics Calculation
    performance_metrics = {
        "Initial Capital": f"${initial_capital:,.2f}",
        "Final Portfolio Value": f"${final_value:,.2f}",
        "Total Portfolio P/L": f"${total_pnl:,.2f}",
        "Number of Trades": len(trades_data),
        "Total Gross Profit": f"${trades_df['Net P/L'].sum():,.2f}",
        
        # Profitability Metrics
        "Win Rate": f"{(trades_df['Net P/L'] > 0).mean() * 100:.1f}%",
        "Profit Factor": (
            trades_df[trades_df['Net P/L'] > 0]['Net P/L'].sum() / 
            max(abs(trades_df[trades_df['Net P/L'] < 0]['Net P/L'].sum()), 1)
        ),
        
        # Trade Performance
        "Average Profit per Trade": f"{trade_returns.mean() * 100:.2f}%" if not trade_returns.empty else "0.00%",
        "Best Trade": f"{trade_returns.max() * 100:.2f}%" if not trade_returns.empty else "0.00%",
        "Worst Trade": f"{trade_returns.min() * 100:.2f}%" if not trade_returns.empty else "0.00%",
        
        # Risk-Adjusted Metrics
        "Sharpe Ratio": f"{calculate_sharpe_ratio(trade_returns):.2f}",
        "Maximum Drawdown": f"{(max(np.cumsum(trade_returns)) - min(np.cumsum(trade_returns))):.2%}"
    }

    # Write detailed performance report
    report_path = f'reports/performance_report_{report_suffix}.txt'
    with open(report_path, 'w') as report_file:
        report_file.write("Trading Strategy Performance Report\n")
        report_file.write("---------------------------------------\n\n")
        for metric, value in performance_metrics.items():
            report_file.write(f"{metric}: {value}\n")

    print(f"\nPerformance report saved to {report_path}")

    # Print metrics to console
    print("\nPerformance Metrics:")
    for metric, value in performance_metrics.items():
        print(f"{metric}: {value}")

    return trades_df, performance_metrics
