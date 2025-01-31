import backtrader as bt
import datetime

def entry_logic(self, current_date):

    # Check current number of positions
    current_positions = len([d for d in self.datas if self.getposition(d).size != 0])
    if current_positions >= self.config["active_positions_cap"]:
        return

    # Get stocks for current date that passed all filters
    todays_stocks = self.ranked_stocks[self.ranked_stocks['Date'] == current_date]
    
    # Sort by ADX (7-day ADX column) and get top stocks
    if not todays_stocks.empty:
        top_stocks = todays_stocks.nlargest(self.config["daily_tickers_entry"], '7-day ADX')['Ticker'].tolist()
    else:
        return  # No stocks for today

    # Calculate positions available
    positions_available = min(self.config["active_positions_cap"] - current_positions,len(top_stocks))

    if positions_available <= 0:
        return

    # Place orders for available positions
    for i, d in enumerate(self.datas):
        if d._name in top_stocks and not self.getposition(d).size:
            if positions_available <= 0:
                break
                
            # Calculate position size (10% of portfolio)
            portfolio_value = self.broker.getvalue()
            position_size = portfolio_value * 0.10

            # Calculate entry price (4% above previous close)
            entry_price = d.close[0] * (1 + self.config["limit_order_percent"]/100)
            
            # Calculate number of shares based on position size
            num_shares = int(position_size / entry_price)
            
            if num_shares > 0:
                # Place limit order valid for 1 day
                self.order = self.sell(
                    data=d,
                    size=num_shares,
                    exectype=bt.Order.Limit,
                    price=entry_price,
                    valid=datetime.datetime.combine(
                        current_date + datetime.timedelta(days=1),
                        datetime.time(23, 59, 59)
                    )
                )
                
                positions_available -= 1