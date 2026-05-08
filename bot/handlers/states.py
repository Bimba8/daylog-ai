from aiogram.fsm.state import StatesGroup, State

class DiaryState(StatesGroup):
    waiting_for_story = State()
    waiting_for_answer = State()

# SettingState и OnboardingState имеют одинаковые поля (waiting_for_tz, waiting_for_time),
# но это осознанный выбор: онбординг — это первичная настройка нового юзера,
# а SettingState — изменение настроек существующим юзером.
# Разделение на две StatesGroup гарантирует, что хендлеры одного флоу
# не перехватят callback'и другого (aiogram фильтрует по классу стейта).

class SettingState(StatesGroup):
    waiting_for_tz = State()
    waiting_for_time = State()
    
class OnboardingState(StatesGroup):
    waiting_for_tz = State()
    waiting_for_time = State()