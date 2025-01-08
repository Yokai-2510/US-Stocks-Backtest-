# backtest_stock.py


from backtesting import Strategy
import pandas as pd
import numpy as np
from typing import Optional

from entry_conditions import (_handle_entry, _reset_entry_tracking, 
                            _cancel_old_orders, _can_place_new_order, _place_limit_order)
from exit_conditions import (_handle_exit, _is_new_position, _record_entry_details,
                           _should_exit, _execute_exit, _reset_tracking_variables,
                           _store_exit_metrics)
from module import download_data, run_backtest
from create_reports import save_summary_report

class SimpleShortStrategy(Strategy):
    SYMBOL = "ALGN"
    START_DATE = "2020-01-01"
    END_DATE = "2025-01-01"
    INITIAL_CASH = 100000
    POSITION_SIZE = 0.1
    ENTRY_LIMIT_PCT = 0.04
    EXIT_DAYS = 2
    COMMISSION = 0.002
    PROFIT_TARGET_PCT = 0.04
    ATR_PERIOD = 14
    ATR_MULTIPLIER = 3.0

    def init(self):
        self.limit_order_day: Optional[int] = None
        self.entry_bar: Optional[int] = None
        self.entry_price: Optional[float] = None
        self.exit_reasons = {}
        self.exit_metrics = {}
        self.stop_loss_orders = {}
        self.trading_days = []
        self.daily_returns = []
        
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        
        def calc_tr():
            tr = high - low
            prev_close = pd.Series(close).shift(1).values
            tr1 = abs(high - prev_close)
            tr2 = abs(low - prev_close)
            return np.maximum.reduce([tr, tr1, tr2])
        
        tr = self.I(calc_tr)
        self.atr = self.I(lambda x: pd.Series(tr).rolling(self.ATR_PERIOD).mean(), tr)

    def next(self):
        current_bar = len(self.data) - 1
        self.trading_days.append(self.data.index[current_bar])
        
        if current_bar > 0:
            daily_return = (self.data.Close[current_bar] - self.data.Close[current_bar - 1]) / self.data.Close[current_bar - 1]
            self.daily_returns.append(daily_return)
        
        if not self.position:
            self._handle_entry(current_bar)
        else:
            self._handle_exit(current_bar)

    # Import entry methods
    _handle_entry = _handle_entry
    _reset_entry_tracking = _reset_entry_tracking
    _cancel_old_orders = _cancel_old_orders
    _can_place_new_order = _can_place_new_order
    _place_limit_order = _place_limit_order

    # Import exit methods
    _handle_exit = _handle_exit
    _is_new_position = _is_new_position
    _record_entry_details = _record_entry_details
    _should_exit = _should_exit
    _execute_exit = _execute_exit
    _reset_tracking_variables = _reset_tracking_variables
    _store_exit_metrics = _store_exit_metrics

def main():
    data = download_data(SimpleShortStrategy)
    stats, trades = run_backtest(data, SimpleShortStrategy)
    save_summary_report(stats, trades, SimpleShortStrategy)

if __name__ == "__main__":
    main()