# exit_conditions.py

from typing import Optional, Tuple

def _handle_exit(self, current_bar: int) -> None:
    if self._is_new_position():
        self._record_entry_details(current_bar)
        return
    
    should_exit, exit_reason = self._should_exit(current_bar)
    if should_exit:
        self.exit_reasons[current_bar + 1] = exit_reason
        self._store_exit_metrics(current_bar)
        self._execute_exit(current_bar)

def _is_new_position(self) -> bool:
    return self.entry_bar is None

def _record_entry_details(self, current_bar: int) -> None:
    self.entry_bar = current_bar
    self.entry_price = self.data.Close[current_bar]
    
    # Calculate stop loss level but don't place order
    stop_price = self.entry_price + (self.ATR_MULTIPLIER * self.atr[current_bar])
    self.stop_loss_orders[current_bar] = {
        'price': stop_price
    }

def _should_exit(self, current_bar: int) -> Tuple[bool, str]:
    if self.entry_bar is None:
        return False, ""
        
    trading_days_held = current_bar - self.entry_bar
    current_price = self.data.Close[current_bar]
    profit_pct = (self.entry_price - current_price) / self.entry_price
    
    # Check stop loss condition
    if current_price >= self.stop_loss_orders[self.entry_bar]['price']:
        return True, "Stop Loss"

    if profit_pct >= self.PROFIT_TARGET_PCT:
        return True, "Profit Target"
        
    if trading_days_held >= self.EXIT_DAYS:
        return True, "Time Exit"
    
    return False, ""

def _execute_exit(self, current_bar: int) -> None:
    self.position.close()
    self._reset_tracking_variables()

def _reset_tracking_variables(self) -> None:
    self.entry_bar = None
    self.entry_price = None
    self.limit_order_day = None

def _store_exit_metrics(self, current_bar: int) -> None:
    current_price = self.data.Close[current_bar]
    profit_pct = (self.entry_price - current_price) / self.entry_price
    stop_loss_price = self.stop_loss_orders[self.entry_bar]['price'] if self.entry_bar in self.stop_loss_orders else None
    trading_days_held = current_bar - self.entry_bar
    
    self.exit_metrics[current_bar + 1] = {
        'ProfitTargetPrice': self.entry_price * (1 - self.PROFIT_TARGET_PCT),
        'StopLossPrice': stop_loss_price,
        'DaysHeld': trading_days_held,
        'CurrentProfitPct': profit_pct * 100,
        'ATRValue': self.atr[self.entry_bar],
        'ExitType': self.exit_reasons.get(current_bar + 1, 'Unknown')
    }

if __name__ == "__main__":
    _handle_exit()
    _is_new_position()
    _record_entry_details()
    _should_exit()
    _execute_exit()
    _reset_tracking_variables()
    _store_exit_metrics()
