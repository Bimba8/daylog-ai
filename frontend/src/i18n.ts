export type Language = 'ru' | 'en';

export const translations = {
  ru: {
    // Header
    appName: "DayLog AI",
    
    // BottomNav
    tab_profile: "Профиль",
    tab_calendar: "Календарь",
    tab_analytics: "Аналитика",
    
    // App (Settings / Network Error)
    conn_lost: "Связь потеряна",
    conn_lost_desc: "Похоже, пропал интернет или сервер сейчас недоступен. Проверь подключение.",
    retry: "Повторить попытку",
    timezone: "Часовой пояс",
    reminder_time: "Время опроса",
    digest_day: "День дайджеста",
    digest_time: "Время дайджеста",
    language: "Язык",
    lang_ru: "Русский",
    lang_en: "English",
    day_monday: "Понедельник",
    day_tuesday: "Вторник",
    day_wednesday: "Среда",
    day_thursday: "Четверг",
    day_friday: "Пятница",
    day_saturday: "Суббота",
    day_sunday: "Воскресенье",
    settings: "Настройки",
    
    // ProfileScreen
    welcome: "Привет",
    no_records_yet: "Пока нет записей. Отправь свой первый лог в бот!",
    records_count: "Записей",
    avg_mood: "Ср. настроение",
    days_in_row: "Дней подряд",
    streak_encouragement: "Отличный результат! Продолжайте вести ежедневные записи для точных ИИ-инсайтов.",
    
    // CalendarScreen
    calendar_title: "Календарь",
    
    // AnalyticsScreen
    analytics_title: "Аналитика",
    period: "Период",
    week: "Неделя",
    month: "Месяц",
    metrics: "Метрики",
    mood: "Настроение",
    energy: "Энергия",
    stress: "Стресс",
    productivity: "Продуктивность",
    avg_values: "Средние значения",
    top_resources: "Источники ресурса",
    top_leaks: "Скрытые утечки",
    loading: "Загрузка...",
    empty_data: "Пока нет данных",
    empty_data_desc: "Продолжай вести дневник, и здесь появится статистика.",
  },
  en: {
    // Header
    appName: "DayLog AI",
    
    // BottomNav
    tab_profile: "Profile",
    tab_calendar: "Calendar",
    tab_analytics: "Analytics",
    
    // App (Settings / Network Error)
    conn_lost: "Connection lost",
    conn_lost_desc: "It seems you are offline or the server is unreachable. Please check your connection.",
    retry: "Try again",
    timezone: "Timezone",
    reminder_time: "Reminder time",
    digest_day: "Digest day",
    digest_time: "Digest time",
    language: "Language",
    lang_ru: "Русский",
    lang_en: "English",
    day_monday: "Monday",
    day_tuesday: "Tuesday",
    day_wednesday: "Wednesday",
    day_thursday: "Thursday",
    day_friday: "Friday",
    day_saturday: "Saturday",
    day_sunday: "Sunday",
    settings: "Settings",
    
    // ProfileScreen
    welcome: "Hello",
    no_records_yet: "No entries yet. Send your first log to the bot!",
    records_count: "Entries",
    avg_mood: "Avg. mood",
    days_in_row: "Streak",
    streak_encouragement: "Great job! Keep making daily entries for accurate AI insights.",
    
    // CalendarScreen
    calendar_title: "Calendar",
    
    // AnalyticsScreen
    analytics_title: "Analytics",
    period: "Period",
    week: "Week",
    month: "Month",
    metrics: "Metrics",
    mood: "Mood",
    energy: "Energy",
    stress: "Stress",
    productivity: "Productivity",
    avg_values: "Averages",
    top_resources: "Energy sources",
    top_leaks: "Energy drains",
    loading: "Loading...",
    empty_data: "No data yet",
    empty_data_desc: "Keep logging your days to see statistics here.",
  }
};

export function t(key: keyof typeof translations['ru'], lang: Language): string {
  return translations[lang][key] || translations['ru'][key] || key;
}
