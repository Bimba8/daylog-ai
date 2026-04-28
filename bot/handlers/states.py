from aiogram.fsm.state import StatesGroup, State

class DiaryState(StatesGroup):
    waiting_for_story = State()
    waiting_for_answer = State()

class SettingState(StatesGroup):
    waiting_for_tz = State()
    waiting_for_time = State()
    
class OnboardingState(StatesGroup):
    waiting_for_tz = State()
    waiting_for_time = State()