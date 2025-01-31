import backtrader as bt
import pandas as pd
from entry_conditions import entry_logic
from exit_conditions import exit_logic
from datetime import datetime

class ShortRSIStrategy(bt.Strategy):
    params = (("ranked_stocks", None), ("config", None))

    def __init__(self):
        self.order = None
        self.ranked_stocks = self.params.ranked_stocks
        self.config = self.params.config
        self.trades = []
        self.exit_details = {} 
        
        # Validate required exit parameters
        required_params = [
            'exit_time_days',
            'atr_period',
            'atr_multiplier',
            'profit_target_percent'
        ]
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter in config: {param}")
        
        # Dictionary to store entry dates and prices for active positions
        self.entry_dates = {}
        self.entry_prices = {}
        
        # Add ATR indicator for each data feed
        self.atrs = {}
        for data in self.datas:
            self.atrs[data._name] = bt.indicators.ATR(
                data, 
                period=self.config['atr_period']
            )
        
        # Convert ranked_stocks Date to datetime for easier comparison
        self.ranked_stocks['Date'] = pd.to_datetime(self.ranked_stocks['Date']).dt.date
        

    def next(self):
        # Get current date
        current_date = bt.num2date(self.data.datetime[0]).date()
        start_date = datetime.strptime(self.config["start_date"], "%Y-%m-%d").date()
        
        if current_date < start_date:
            return
            
        # Entry logic
        entry_logic(self, current_date)
        
        # Exit logic
        exit_logic(self, current_date)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            current_date = bt.num2date(self.data.datetime[0]).date()
            
            if order.status == order.Completed:
                
                # For entry orders (shorts in this case), store the entry date and price
                if not order.isbuy():  # Short entry
                    self.entry_dates[order.data._name] = current_date
                    self.entry_prices[order.data._name] = order.executed.price

                # For exit orders (buys to cover), remove the stored data
                else:  # Buy to cover (exit)
                    if order.data._name in self.entry_dates:
                        del self.entry_dates[order.data._name]
                        del self.entry_prices[order.data._name]

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append(trade)

    def stop(self):

        if self.trades:
            total_net_profit = sum(trade.pnlcomm for trade in self.trades)
            print(f"Total Net Profit: ${total_net_profit:.2f}")
            win_rate = len([t for t in self.trades if t.pnlcomm > 0]) / len(self.trades) * 100
            print(f"Win Rate: {win_rate:.1f}%")