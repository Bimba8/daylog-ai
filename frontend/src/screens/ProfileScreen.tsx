import React, { useState, useEffect } from 'react';
import { BookOpen, Smile, Calendar, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../api/client';

const pluralizeDays = (count: number) => {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 19) return 'Дней';
  if (mod10 === 1) return 'День';
  if (mod10 >= 2 && mod10 <= 4) return 'Дня';
  return 'Дней';
};

export default function ProfileScreen() {
  const [user, setUser] = useState<any>(null);
  const [stats, setStats] = useState<any>(null); // Добавили стейт для метрик
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        // Делаем два запроса параллельно для скорости
        const [userData, statsData] = await Promise.all([
          apiClient('/profile'),
          apiClient('/stats/metrics')
        ]);
        
        setUser(userData);
        setStats(statsData);
      } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  const formatJoinDate = (dateString?: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const formatter = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
    const genitiveDate = formatter.format(date).replace(/^\d+\s/, '');
    return `В приложении с ${genitiveDate}`;
  };

  // Берем реальную тепловую карту с сервера или рисуем пустые серые квадраты пока грузится
  const heatmapCells = stats?.heatmap || Array(105).fill(false);

  // Если данные еще грузятся, показываем "Скелетон" (пульсирующие заглушки)
  if (isLoading) {
    return (
      <div className="animate-pulse flex flex-col gap-5">
        {/* Аватар и имя */}
        <div className="flex flex-col items-center mt-3 mb-2">
          <div className="w-24 h-24 rounded-full bg-gray-200 dark:bg-slate-800/80 mb-3" />
          <div className="h-6 w-32 bg-gray-200 dark:bg-slate-800/80 rounded-md mb-2" />
          <div className="h-3 w-40 bg-gray-200 dark:bg-slate-800/80 rounded-md" />
        </div>

        {/* Стрик */}
        <div className="bg-gray-100 dark:bg-slate-900 rounded-2xl p-5 border border-gray-200/40 dark:border-slate-800/40 flex flex-col items-center">
          <div className="h-3 w-24 bg-gray-200 dark:bg-slate-800/80 rounded-md mb-3" />
          <div className="h-10 w-32 bg-gray-200 dark:bg-slate-800/80 rounded-md mb-4" />
          <div className="h-3 w-48 bg-gray-200 dark:bg-slate-800/80 rounded-md" />
        </div>

        {/* Сетка аналитики */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-100 dark:bg-slate-900 rounded-xl p-4 h-[104px]" />
          <div className="bg-gray-100 dark:bg-slate-900 rounded-xl p-4 h-[104px]" />
          <div className="bg-gray-100 dark:bg-slate-900 rounded-xl p-4 h-[120px] col-span-2" />
        </div>

        {/* Календарь активности */}
        <div className="bg-gray-100 dark:bg-slate-900 rounded-xl p-4 h-[160px]" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in-up flex flex-col gap-5">
      {/* Profile Header Block */}
      <div className="flex flex-col items-center mt-3 mb-2">
        <div className="relative w-24 h-24 mb-3">
          <img
            alt={user?.first_name || 'Аватар'}
            className="w-full h-full rounded-full border-2 border-white dark:border-slate-800 object-cover shadow-md"
            src={window.Telegram?.WebApp?.initDataUnsafe?.user?.photo_url || "https://t3.ftcdn.net/jpg/05/16/27/58/360_F_516275801_f3Fsp17x6HQK0xQgDQEELoTuERO4SsWV.jpg"}
          />
          <div className="absolute bottom-0 right-0 bg-[#00418f] text-white w-6 h-6 rounded-full border-2 border-white dark:border-slate-900 flex items-center justify-center shadow-xs">
            <CheckCircle2 className="w-3.5 h-3.5 fill-[#00418f] stroke-[2.5]" />
          </div>
        </div>
        <h2 className="font-sans font-bold text-2xl text-gray-950 dark:text-white tracking-tight">
          {window.Telegram?.WebApp?.initDataUnsafe?.user?.first_name || user?.username || 'Загрузка...'}
        </h2>
        <p className="font-sans text-xs text-gray-500 dark:text-gray-400 mt-1 uppercase tracking-wider font-semibold">
          {formatJoinDate(user?.created_at)}
        </p>
      </div>

      {/* Streak Dashboard Card */}
      <div className="relative overflow-hidden bg-white dark:bg-slate-900 rounded-2xl p-5 border border-gray-200/40 dark:border-slate-800/40 shadow-xs flex flex-col items-center text-center">
        <div className="absolute top-0 right-0 w-24 h-24 bg-[#00418f]/10 dark:bg-blue-500/10 rounded-full blur-2xl -mr-8 -mt-8 pointer-events-none" />
        
        <p className="font-sans text-xs text-gray-500 dark:text-gray-400 uppercase tracking-widest font-semibold mb-2">
          🔥 Текущий стрик
        </p>
        <span className="text-4xl font-extrabold text-gray-900 dark:text-white tracking-tight">
          {stats?.streak || 0} {pluralizeDays(stats?.streak || 0)}
        </span>
        <p className="font-sans text-sm text-gray-600 dark:text-gray-300 mt-3 max-w-xs leading-relaxed">
          Отличный результат! Продолжайте вести ежедневные записи для точных ИИ-инсайтов.
        </p>
      </div>

      {/* High-Fidelity Stats Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Stat item 1 */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 mb-2 text-[#00418f] dark:text-[#adc6ff]">
            <BookOpen className="w-4.5 h-4.5" />
            <p className="font-sans text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider">
              Всего отчетов
            </p>
          </div>
          <p className="font-sans font-bold text-3xl text-gray-900 dark:text-white">
            {stats?.total_entries || 0}
          </p>
        </div>

        {/* Stat item 2 */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 mb-2 text-amber-600 dark:text-[#ffb595]">
            <Smile className="w-4.5 h-4.5" />
            <p className="font-sans text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider">
              Ср. настроение (7д)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <p className="font-sans font-bold text-3xl text-gray-900 dark:text-white flex items-baseline">
              {stats?.avg_mood || 0}
              <span className="text-xs text-gray-400 dark:text-gray-500 font-medium ml-0.5">/5</span>
            </p>
            {/* Реальный бейдж дельты настроения */}
            {stats?.mood_delta !== undefined && (
              <span className={`px-1.5 py-0.5 rounded text-[11px] font-bold shadow-sm border ${
                stats.mood_delta > 0
                  ? 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-950/20 border-green-100/50 dark:border-green-900/30'
                  : stats.mood_delta < 0
                  ? 'text-rose-600 bg-rose-50 dark:text-rose-400 dark:bg-rose-950/20 border-rose-100/50 dark:border-rose-900/30'
                  : 'text-gray-500 bg-gray-50 dark:text-gray-400 dark:bg-slate-800/50 border-gray-200/50 dark:border-slate-700/30'
              }`}>
                {stats.mood_delta > 0 ? `↑ +${stats.mood_delta}` : stats.mood_delta < 0 ? `↓ ${Math.abs(stats.mood_delta)}` : '0.0'}
              </span>
            )}
          </div>
        </div>

        {/* Stat item 3: Full Width with inline sparkline representation */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40 flex flex-col col-span-2">
          <div className="flex items-center gap-1.5 mb-3 text-[#0058bc] dark:text-blue-400">
            <Calendar className="w-4.5 h-4.5" />
            <p className="font-sans text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wider">
              Активность (30д)
            </p>
          </div>
          <div className="flex items-end justify-between">
            <p className="font-sans font-bold text-3xl text-gray-900 dark:text-white">
              {stats?.activity_percent || 0}%
            </p>
            <div className="flex items-end gap-1 h-9 mb-1">
              <div className="w-2.5 bg-[#cddefa] dark:bg-blue-900/40 rounded-t h-4" />
              <div className="w-2.5 bg-[#cddefa] dark:bg-blue-900/40 rounded-t h-7" />
              <div className="w-2.5 bg-[#cddefa] dark:bg-blue-900/40 rounded-t h-5" />
              <div className="w-2.5 bg-[#00418f] dark:bg-[#3b82f6] rounded-t h-8" />
              <div className="w-2.5 bg-[#00418f] dark:bg-[#3b82f6] rounded-t h-6" />
              <div className="w-2.5 bg-[#00418f] dark:bg-[#3b82f6] rounded-t h-9 animate-pulse" />
            </div>
          </div>
        </div>
      </div>

      {/* GitHub-style Heatmap Section */}
      <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-sans font-bold text-[15px] text-gray-950 dark:text-white">
            Календарь активности
          </h3>
          <span className="text-[11px] text-gray-400 dark:text-gray-500 font-semibold uppercase tracking-wider">
            Последние 15 недель
          </span>
        </div>
        
        <div className="overflow-x-auto pb-2 no-scrollbar">
          <div className="grid grid-rows-7 grid-flow-col gap-1.5 w-max mx-auto p-1">
            {heatmapCells.map((isActive: boolean, index: number) => (
              <div
                key={index}
                className={`w-3.5 h-3.5 rounded-xs transition-all duration-150 cursor-pointer hover:ring-2 hover:ring-[#0058bc]/40 ${isActive ? 'bg-blue-600' : 'bg-slate-800'}`}
                title={isActive ? 'Отчет сохранен' : 'Нет отчетов'}
              />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}