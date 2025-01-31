import backtrader as bt
from datetime import datetime, timedelta

def exit_logic(self, current_date):
    
    # Get all active positions
    active_positions = [d for d in self.datas if self.getposition(d).size != 0]
    
    for d in active_positions:
        pos = self.getposition(d)
        
        # Get entry date and price from our stored dictionaries
        entry_date = self.entry_dates.get(d._name)
        entry_price = self.entry_prices.get(d._name)
        
        if entry_date is not None and entry_price is not None:
            # Calculate current position metrics
            current_price = d.close[0]
            profit_pct = ((entry_price - current_price) / entry_price) * 100
            days_held = (current_date - entry_date).days
            current_atr = self.atrs[d._name][0]
            
            # Calculate actual exit condition values
            time_exit_date = entry_date + timedelta(days=self.config["exit_time_days"])
            stop_loss_price = entry_price + (self.config['atr_multiplier'] * current_atr)
            profit_target_price = entry_price * (1 - self.config['profit_target_percent']/100)
            
            exit_reason = None
            exit_details = {}
            
            # 1. Time-based exit
            if days_held >= self.config["exit_time_days"]:
                exit_reason = "Time-based"
                exit_details = {
                    'criterion': 'Time-based',
                    'target_value': time_exit_date.strftime("%Y-%m-%d"),
                    'actual_value': current_date.strftime("%Y-%m-%d"),
                    'days_held': days_held,
                    'target_days': self.config["exit_time_days"]
                }
            
            # 2. Stop Loss - ATR based
            elif current_price >= stop_loss_price:
                exit_reason = "Stop Loss"
                exit_details = {
                    'criterion': 'Stop Loss',
                    'target_value': stop_loss_price,
                    'actual_value': current_price,
                    'atr_value': current_atr,
                    'atr_multiplier': self.config['atr_multiplier']
                }
            
            # 3. Profit Target
            elif profit_pct >= self.config['profit_target_percent']:
                exit_reason = "Profit Target"
                exit_details = {
                    'criterion': 'Profit Target',
                    'target_value': profit_target_price,
                    'actual_value': current_price,
                    'target_percent': self.config['profit_target_percent'],
                    'actual_percent': profit_pct
                }
            
            # Execute exit if any condition is met
            if exit_reason:
                
                self.exit_details[d._name] = exit_details   # Store exit details in strategy instance
                self.order = self.close(data=d)  # Close the position
        
        else:
            print(f"\nWarning: No entry data found for active position in {d._name}")
            self.order = self.close(data=d)