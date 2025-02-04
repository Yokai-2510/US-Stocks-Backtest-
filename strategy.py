import backtrader as bt
import pandas as pd
from entry_conditions import entry_logic
from exit_conditions import exit_logic
from datetime import datetime, date

class ShortRSIStrategy(bt.Strategy):
    params = (("ranked_stocks", None), ("config", None))

    def __init__(self):
        self.order = None
        self.ranked_stocks = self.params.ranked_stocks
        self.config = self.params.config
        self.trades = []
        self.exit_details = {} 
        
        # Enhanced trade tracking with more robust tracking
        self.trade_tracking = {}
        
        # Validate required parameters
        required_params = [
            'exit_time_days',
            'atr_period',
            'atr_multiplier',
            'profit_target_percent'
        ]
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required parameter in config: {param}")
        
        # Dictionaries for position management
        self.entry_dates = {}
        self.entry_prices = {}
        
        # ATR indicators
        self.atrs = {}
        for data in self.datas:
            self.atrs[data._name] = bt.indicators.ATR(
                data, 
                period=self.config['atr_period']
            )
        
        # Ensure Date column is properly converted
        self.ranked_stocks['Date'] = pd.to_datetime(self.ranked_stocks['Date']).dt.date

    def next(self):
        current_date = bt.num2date(self.data.datetime[0]).date()
        start_date = datetime.strptime(self.config["start_date"], "%Y-%m-%d").date()
        
        if current_date < start_date:
            return
            
        entry_logic(self, current_date)
        exit_logic(self, current_date)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed, order.Canceled, order.Margin, order.Rejected]:
            current_date = bt.num2date(self.data.datetime[0]).date()
            
            if order.status == order.Completed:
                if not order.isbuy():  # Short entry
                    self.entry_dates[order.data._name] = current_date
                    self.entry_prices[order.data._name] = order.executed.price
                    
                    # Enhanced tracking with more details
                    self.trade_tracking[order.data._name] = {
                        'entry_date': current_date,
                        'entry_price': order.executed.price,
                        'symbol': order.data._name,
                        'shares': abs(order.executed.size),  # Ensure positive share count
                        'size': abs(order.executed.size)  # Duplicate to ensure backup
                    }
                else:  # Buy to cover (exit)
                    if order.data._name in self.trade_tracking:
                        trade_info = self.trade_tracking[order.data._name]
                        trade_info.update({
                            'exit_date': current_date,
                            'exit_price': order.executed.price
                        })

    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append(trade)
            
            # Store comprehensive trade information
            if trade.data._name in self.trade_tracking:
                trade_info = self.trade_tracking.get(trade.data._name, {})
                trade_info['net_pnl'] = trade.pnlcomm
                trade_info['symbol'] = trade.data._name
                
                # Ensure all trades have complete information
                if 'exit_date' not in trade_info:
                    trade_info['exit_date'] = bt.num2date(trade.dtclose).date()
                if 'exit_price' not in trade_info:
                    trade_info['exit_price'] = trade.price

    def stop(self):
        if self.trades:
            total_net_profit = sum(trade.pnlcomm for trade in self.trades)
            print(f"Total Net Profit: ${total_net_profit:.2f}")
            win_rate = len([t for t in self.trades if t.pnlcomm > 0]) / len(self.trades) * 100
            print(f"Win Rate: {win_rate:.1f}%")
