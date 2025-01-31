import pandas as pd
import os
from datetime import datetime
import backtrader as bt

def create_reports(results, ranked_stocks):
    
    os.makedirs('reports', exist_ok=True)   # Ensure reports directory exists
    strategy = results[0]   # Get the strategy instance
    
    # Calculate actual P&L
    initial_capital = strategy.broker.startingcash
    final_value = strategy.broker.getvalue()
    total_pnl = final_value - initial_capital
    
    # Collect and log all trades
    trades_data = []
    for trade in strategy.trades:
        if trade.isclosed:
            
            # Calculate trade metrics
            entry_price = trade.price
            exit_price = trade.history[1].price if len(trade.history) > 1 else trade.price
            days_held = (bt.num2date(trade.barclose).date() - bt.num2date(trade.baropen).date()).days
            profit_pct = ((entry_price - exit_price) / entry_price) * 100  # For shorts
            
            # Get stored exit details
            exit_details = strategy.exit_details.get(trade.data._name, {})
            exit_reason = exit_details.get('criterion', 'Unknown')
            
            trade_info = {
                'Symbol': trade.data._name,
                'Entry Date': bt.num2date(trade.baropen).date(),
                'Exit Date': bt.num2date(trade.barclose).date(),
                'Entry Price': entry_price,
                'Exit Price': exit_price,
                'Shares': abs(trade.size),
                'Gross P/L': trade.pnl,
                'Net P/L': trade.pnlcomm,
                'Commission': trade.commission,
                'Duration (Days)': days_held,
                'Profit %': profit_pct,
                'Exit Reason': exit_reason,
            }
            
            # Add exit condition specific details
            if exit_details:
                if exit_reason == 'Time-based':
                    trade_info.update({
                        'Target Exit Date': exit_details['target_value'],
                        'Actual Exit Date': exit_details['actual_value'],
                        'Target Hold Days': exit_details['target_days'],
                        'Actual Hold Days': exit_details['days_held']
                    })
                elif exit_reason == 'Stop Loss':
                    trade_info.update({
                        'Stop Loss Price': exit_details['target_value'],
                        'Exit Price': exit_details['actual_value'],
                        'ATR Value': exit_details['atr_value'],
                        'ATR Multiplier': exit_details['atr_multiplier']
                    })
                elif exit_reason == 'Profit Target':
                    trade_info.update({
                        'Target Price': exit_details['target_value'],
                        'Exit Price': exit_details['actual_value'],
                        'Target Profit %': exit_details['target_percent'],
                        'Actual Profit %': exit_details['actual_percent']
                    })
            
            trades_data.append(trade_info)

    # Create trades DataFrame
    trades_df = pd.DataFrame(trades_data)
    
    if trades_df.empty:
        print("\nNo trades were completed during the backtest period")
        return
        
    # Save detailed trades log to CSV
    trades_csv_path = 'reports/trades_log.csv'
    trades_df.to_csv(trades_csv_path, index=False)
    print(f"\nTrades log saved to {trades_csv_path}")

    # Print performance metrics
    print("\nPerformance Metrics:")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    print(f"Total Portfolio P/L: ${total_pnl:,.2f}")
    print(f"Number of Trades: {len(trades_data)}")
    
    if not trades_df.empty:

        # Profitability analysis
        profitable_trades = trades_df[trades_df['Net P/L'] > 0]
        win_rate = len(profitable_trades) / len(trades_df) * 100
        avg_profit_pct = trades_df['Profit %'].mean()
        
        print("\nProfitability Analysis:")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Average Profit per Trade: {avg_profit_pct:.2f}%")
        print(f"Best Trade: {trades_df['Profit %'].max():.2f}%")
        print(f"Worst Trade: {trades_df['Profit %'].min():.2f}%")
    
    return trades_df