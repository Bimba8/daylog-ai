import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Sparkles, Smile, Zap, AlertTriangle, CheckSquare, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { t, Language } from '../i18n';

export default function CalendarScreen({ lang = 'ru' }: { lang?: Language }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [sheetOpen, setSheetOpen] = useState<boolean>(false);
  const [isClosing, setIsClosing] = useState<boolean>(false);
  const [dragY, setDragY] = useState<number>(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);

  const [logsMap, setLogsMap] = useState<Record<number, any>>({});
  const [digestsMap, setDigestsMap] = useState<Record<number, any>>({});
  const [isLoading, setIsLoading] = useState(false);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth(); 
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(year, month, 1).getDay();
  const startDayOffset = firstDay === 0 ? 6 : firstDay - 1; 
  const prevMonthDays = new Date(year, month, 0).getDate();
  
  const monthName = new Intl.DateTimeFormat(lang === 'en' ? 'en-US' : 'ru-RU', { month: 'long', year: 'numeric' }).format(currentDate);

  useEffect(() => {
    async function fetchCalendar() {
      setIsLoading(true);
      try {
        const data = await apiClient('/stats/calendar?limit=100');
        
        const newLogs: Record<number, any> = {};
        const newDigests: Record<number, any> = {};

        if (data.items) {
          data.items.forEach((item: any) => {
            const itemDate = new Date(item.created_at);
            if (itemDate.getFullYear() === year && itemDate.getMonth() === month) {
              const day = itemDate.getDate();
              if (item.type === 'log') {
                let parsedMetrics = { mood: 0, energy: 0, stress: 0, productivity: 0 };
                try {
                  if (item.metrics) {
                    parsedMetrics = typeof item.metrics === 'string' ? JSON.parse(item.metrics) : item.metrics;
                  }
                } catch (e) { console.error('Ошибка парсинга метрик', e); }
                
                newLogs[day] = { ...item, metricsObj: parsedMetrics };
              } else if (item.type === 'digest') {
                newDigests[day] = item;
              }
            }
          });
        }

        setLogsMap(newLogs);
        setDigestsMap(newDigests);
      } catch (error) {
        console.error('Ошибка загрузки календаря:', error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchCalendar();
  }, [year, month]);

  const closeSheet = () => {
    setIsClosing(true);
    setTimeout(() => {
      setSheetOpen(false);
      setIsClosing(false);
      setDragY(0);
    }, 300);
  };

  const onTouchStart = (e: React.TouchEvent<HTMLDivElement>) => setTouchStart(e.touches[0].clientY);
  const onTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    if (!touchStart) return;
    if (e.currentTarget.scrollTop > 0) return; 
    const currentY = e.touches[0].clientY;
    const diff = currentY - touchStart;
    if (diff > 0) setDragY(diff * 0.8);
  };
  const onTouchEnd = () => {
    if (dragY > 80) closeSheet();
    else setDragY(0);
    setTouchStart(null);
  };

  const handlePrevMonth = () => {
    setCurrentDate(new Date(year, month - 1, 1));
    setSelectedDay(null);
  };

  const handleNextMonth = () => {
    setCurrentDate(new Date(year, month + 1, 1));
    setSelectedDay(null);
  };

  const handleDayClick = (day: number) => {
    setSelectedDay(day);
    setSheetOpen(true);
  };

  const prevMonthEmptyCells = Array.from({ length: startDayOffset }, (_, i) => {
    return prevMonthDays - startDayOffset + i + 1;
  });

  const monthDayNumbers = Array.from({ length: daysInMonth }, (_, i) => i + 1);

  const todayDate = new Date();
  const todayDayNum = (todayDate.getFullYear() === year && todayDate.getMonth() === month) 
    ? todayDate.getDate() 
    : null;

  const hasLog = selectedDay !== null && !!logsMap[selectedDay];
  const hasDigest = selectedDay !== null && !!digestsMap[selectedDay];
  const logDetails = selectedDay !== null ? logsMap[selectedDay] : null;
  const digestDetails = selectedDay !== null ? digestsMap[selectedDay] : null;

  return (
    <>
      <div className="animate-fade-in-up flex flex-col gap-4">
        <div className="flex items-center justify-between mb-1">
          <h2 className="font-sans font-bold text-2xl text-gray-950 dark:text-white tracking-tight capitalize">
            {monthName}
          </h2>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handlePrevMonth}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-slate-900 border border-gray-200/40 dark:border-slate-800/40 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            >
              <ChevronLeft className="w-5 h-5 stroke-[2.5]" />
            </button>
            <button
              onClick={handleNextMonth}
              disabled={year === todayDate.getFullYear() && month === todayDate.getMonth()}
              className="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-slate-900 border border-gray-200/40 dark:border-slate-800/40 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors disabled:opacity-30"
            >
              <ChevronRight className="w-5 h-5 stroke-[2.5]" />
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-slate-900 rounded-3xl border border-gray-200/40 dark:border-slate-800/40 p-4 shadow-xs relative">
          
          {isLoading && (
            <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm rounded-3xl">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          )}

          <div className="grid grid-cols-7 mb-2 text-center text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider py-1">
            {lang === 'en' ? (
              <><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div><div>Sun</div></>
            ) : (
              <><div>Пн</div><div>Вт</div><div>Ср</div><div>Чт</div><div>Пт</div><div>Сб</div><div>Вс</div></>
            )}
          </div>

          <div className="grid grid-cols-7 gap-y-2 gap-x-1.5 justify-items-center">
            {prevMonthEmptyCells.map((dayNum, idx) => (
              <div key={`prev-${idx}`} className="w-11 h-11 flex items-center justify-center text-gray-300 dark:text-gray-700 text-sm font-medium">
                {dayNum}
              </div>
            ))}

            {monthDayNumbers.map((day) => {
              const isToday = todayDayNum === day;
              const isLogDay = !!logsMap[day];
              const isDigestDay = !!digestsMap[day];

              let dayBtnStyle = "w-9 h-9 rounded-full flex items-center justify-center text-sm font-medium transition-transform active:scale-95 ";
              
              if (isToday) {
                dayBtnStyle += "bg-[#00418f] text-white shadow-xs font-bold";
              } else if (isDigestDay) {
                dayBtnStyle += "bg-[#00418f]/10 dark:bg-blue-900/30 text-[#00418f] dark:text-[#adc6ff] font-bold ring-1 ring-[#00418f]/25";
              } else if (isLogDay) {
                dayBtnStyle += "text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-slate-800 font-semibold";
              } else {
                dayBtnStyle += "text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800";
              }

              return (
                <div key={day} className="w-11 h-11 relative flex flex-col items-center justify-center">
                  <button onClick={() => handleDayClick(day)} className={dayBtnStyle}>
                    {day}
                  </button>
                  {isDigestDay && (
                    <div className="absolute bottom-1 flex items-center gap-0.5 scale-90">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#00418f]" />
                      <span className="text-[9px] leading-none mb-0.5">✨</span>
                    </div>
                  )}
                  {!isDigestDay && isLogDay && (
                    <div className="absolute bottom-1.5 w-1.5 h-1.5 rounded-full bg-[#00418f]/70" />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {sheetOpen && selectedDay !== null && (
        <div 
          className={`fixed inset-0 z-50 flex justify-center items-end bg-black/60 backdrop-blur-xs transition-opacity duration-300 ${isClosing ? 'opacity-0' : 'opacity-100'}`}
          onClick={closeSheet}
        >
          <div 
            className="w-full max-h-[85vh] bg-[#1a1d29] rounded-t-3xl overflow-y-auto px-4 pb-8 flex flex-col shadow-2xl border-t border-slate-800 animate-fade-in-up" 
            onClick={(e) => e.stopPropagation()}
            onTouchStart={onTouchStart}
            onTouchMove={onTouchMove}
            onTouchEnd={onTouchEnd}
            style={{ 
              transform: `translateY(${isClosing ? '100%' : dragY + 'px'})`, 
              transition: dragY > 0 ? 'none' : 'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)' 
            }}
          >
            <div className="w-full pt-2 flex justify-center cursor-pointer" onClick={closeSheet}>
              <div className="w-12 h-1.5 bg-gray-600 rounded-full mx-auto mt-4 mb-6 shrink-0" />
            </div>

            <div className="flex flex-col gap-5">
              <div className="flex justify-center border-b border-gray-100 dark:border-slate-800/60 pb-3">
                <h3 className="font-sans font-bold text-xl text-gray-900 dark:text-white text-center">
                  {lang === 'en' ? 'Log for ' : 'Отчет за '}{new Intl.DateTimeFormat(lang === 'en' ? 'en-US' : 'ru-RU', { day: 'numeric', month: 'long' }).format(new Date(year, month, selectedDay))}
                </h3>
              </div>

              {!hasLog && !hasDigest && (
                <div className="py-12 text-center flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-slate-800 flex items-center justify-center text-gray-400">
                    <CheckSquare className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <p className="text-gray-500 dark:text-gray-400 font-sans text-sm font-medium">
                    {lang === 'en' ? 'No logs recorded for this day.' : 'Нет записанных логов за этот день.'}
                  </p>
                </div>
              )}

              {(hasLog || hasDigest) && (
                <div className="flex flex-col gap-6">
                  
                  {logDetails && logDetails.metricsObj && (
                    <div className="flex flex-col gap-3">
                      <span className="font-sans text-xs text-gray-400 dark:text-gray-500 uppercase tracking-widest font-bold">
                        {lang === 'en' ? 'Daily Metrics' : 'Показатели дня'}
                      </span>
                      <div className="flex flex-wrap gap-2.5">
                        {logDetails.metricsObj.mood > 0 && (
                          <div className="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-950/20 px-3 py-1.5 rounded-full border border-blue-100/50 dark:border-blue-900/30">
                            <Smile className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                            <span className="text-xs text-blue-900 dark:text-blue-300 font-semibold">
                              {t('mood', lang)}: {logDetails.metricsObj.mood}
                            </span>
                          </div>
                        )}
                        {logDetails.metricsObj.energy > 0 && (
                          <div className="flex items-center gap-1.5 bg-cyan-50 dark:bg-cyan-950/20 px-3 py-1.5 rounded-full border border-cyan-100/50 dark:border-cyan-900/30">
                            <Zap className="w-3.5 h-3.5 text-cyan-500 dark:text-cyan-400" />
                            <span className="text-xs text-cyan-900 dark:text-cyan-300 font-semibold">
                              {t('energy', lang)}: {logDetails.metricsObj.energy}
                            </span>
                          </div>
                        )}
                        {logDetails.metricsObj.stress > 0 && (() => {
                          const stress = logDetails.metricsObj.stress;
                          let stressColorClass = "bg-red-50 dark:bg-red-950/20 border-red-100/50 dark:border-red-900/30";
                          let stressTextClass = "text-red-900 dark:text-red-300";
                          let stressIconClass = "text-red-500 dark:text-red-400";
                          
                          if (stress >= 1 && stress <= 2) {
                            stressColorClass = "bg-green-50 dark:bg-green-950/20 border-green-100/50 dark:border-green-900/30";
                            stressTextClass = "text-green-900 dark:text-green-300";
                            stressIconClass = "text-green-500 dark:text-green-400";
                          } else if (stress > 2 && stress <= 4) {
                            stressColorClass = "bg-amber-50 dark:bg-amber-950/20 border-amber-100/50 dark:border-amber-900/30";
                            stressTextClass = "text-amber-900 dark:text-amber-300";
                            stressIconClass = "text-amber-500 dark:text-amber-400";
                          }
                          
                          return (
                            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border ${stressColorClass}`}>
                              <AlertTriangle className={`w-3.5 h-3.5 ${stressIconClass}`} />
                              <span className={`text-xs font-semibold ${stressTextClass}`}>
                                {t('stress', lang)}: {stress}
                              </span>
                            </div>
                          );
                        })()}
                        {logDetails.metricsObj.productivity > 0 && (
                          <div className="flex items-center gap-1.5 bg-indigo-50 dark:bg-indigo-950/20 px-3 py-1.5 rounded-full border border-indigo-100/50 dark:border-indigo-900/30">
                            <Sparkles className="w-3.5 h-3.5 text-indigo-500 dark:text-indigo-400" />
                            <span className="text-xs text-indigo-900 dark:text-indigo-300 font-semibold">
                              {t('productivity', lang)}: {logDetails.metricsObj.productivity}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {logDetails && logDetails.conversation_log && (
                    <div className="flex flex-col gap-2">
                      <span className="font-sans text-xs text-gray-400 dark:text-gray-500 uppercase tracking-widest font-bold">
                        📝 {lang === 'en' ? 'Your Log' : 'Твоя запись'}
                      </span>
                      <div className="bg-slate-50 dark:bg-slate-800/40 rounded-2xl p-4 border border-gray-100 dark:border-slate-800/50 max-h-64 overflow-y-auto">
                        <p className="font-sans text-sm text-gray-700 dark:text-gray-300 leading-relaxed font-normal whitespace-pre-wrap">
                          {logDetails.conversation_log}
                        </p>
                      </div>
                    </div>
                  )}

                  {hasDigest && digestDetails && (
                    <div className="bg-gradient-to-br from-[#0058bc]/5 to-[#00418f]/10 dark:from-blue-950/15 dark:to-slate-900 rounded-2xl p-5 border border-[#cddefa]/40 dark:border-blue-900/30 shadow-xs relative overflow-hidden">
                      <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl -mr-12 -mt-12 pointer-events-none" />
                      
                      <div className="flex items-center gap-2 mb-3">
                        <Sparkles className="w-5 h-5 text-[#0058bc] dark:text-blue-400" />
                        <h4 className="font-sans font-bold text-[#00418f] dark:text-[#adc6ff] text-base">
                          ✨ {lang === 'en' ? 'Weekly Summary (AI Digest)' : 'Итоги недели (AI Digest)'}
                        </h4>
                      </div>

                      <div className="text-sm mt-4 text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap relative z-10">
                        {digestDetails.content}
                      </div>
                    </div>
                  )}

                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}