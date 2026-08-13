from aiogram.fsm.state import State, StatesGroup

class BookingState(StatesGroup):
    choosing_rent_type = State()   # выбор почасово/посуточно
    entering_start_datetime = State()
    entering_end_datetime = State()
    confirming = State()           # показ итогов и договора
