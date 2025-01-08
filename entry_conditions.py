# entry_conditions.py
def _handle_entry(self, current_bar: int) -> None:
    self._reset_entry_tracking()
    self._cancel_old_orders(current_bar)
    
    if self._can_place_new_order(current_bar):
        self._place_limit_order(current_bar)

def _reset_entry_tracking(self) -> None:
    self.entry_bar = None
    self.entry_price = None

def _cancel_old_orders(self, current_bar: int) -> None:
    if self.limit_order_day is not None and self.limit_order_day != current_bar:
        self.orders.cancel()
        self.limit_order_day = None

def _can_place_new_order(self, current_bar: int) -> bool:
    return self.limit_order_day is None and current_bar >= 1

def _place_limit_order(self, current_bar: int) -> None:
    prev_close = self.data.Close[current_bar - 1]
    limit_price = prev_close * (1 + self.ENTRY_LIMIT_PCT)
    self.sell(size=self.POSITION_SIZE, limit=limit_price)
    self.limit_order_day = current_bar


if __name__ == '__main__':
    _handle_entry()
    _reset_entry_tracking()
    _cancel_old_orders()
    _can_place_new_order()
    _place_limit_order()
    