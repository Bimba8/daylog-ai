import React, { useState, useEffect } from 'react';
import { Globe, Clock, Calendar, History, Loader2, WifiOff } from 'lucide-react'; 
import Header from './components/Header';
import BottomNav from './components/BottomNav';
import ProfileScreen from './screens/ProfileScreen';
import CalendarScreen from './screens/CalendarScreen';
import AnalyticsScreen from './screens/AnalyticsScreen';
import { apiClient } from './api/client'; 

declare global {
  interface Window {
    Telegram: any;
  }
}

type TabType = 'profile' | 'calendar' | 'analytics';

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>('profile');
  const [settingsOpen, setSettingsOpen] = useState<boolean>(false);
  const [isClosing, setIsClosing] = useState<boolean>(false);
  const [dragY, setDragY] = useState<number>(0);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  
  const [userSettings, setUserSettings] = useState({ 
    timezone: 'Europe/Moscow', 
    reminder_time: '21:00', 
    digest_day: 6, 
    digest_time: 10 
  });

  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isError, setIsError] = useState(false); 

  useEffect(() => {
    async function authenticate() {
      const initData = window.Telegram?.WebApp?.initData;
      
      if (!initData) {
        setIsAuthLoading(false);
        return;
      }

      try {
        const data = await apiClient('/auth', { 
          method: 'POST', 
          body: JSON.stringify({ initData }) 
        });
        localStorage.setItem('access_token', data.access_token);
        const profile = await apiClient('/profile');
        setUserSettings({
          timezone: profile.timezone,
          reminder_time: profile.reminder_time,
          digest_day: profile.digest_day,
          digest_time: profile.digest_time
        });
        setIsAuthLoading(false);
      } catch (error) {
        console.error('Ошибка авторизации:', error);
        setIsError(true);
        setIsAuthLoading(false);
      }
    }

    authenticate();
  }, []);

  const updateSetting = async (key: string, value: string | number) => {
    setUserSettings(prev => ({ ...prev, [key]: value }));
    try {
      await apiClient('/profile/settings', {
        method: 'POST',
        body: JSON.stringify({ [key]: value })
      });
    } catch (error) {
      console.error('Ошибка сохранения:', error);
    }
  };

  const closeSettings = () => {
    setIsClosing(true);
    setTimeout(() => {
      setSettingsOpen(false);
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
    if (dragY > 80) closeSettings();
    else setDragY(0);
    setTouchStart(null);
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col items-center justify-center p-6 text-center animate-fade-in-up">
        <div className="w-24 h-24 bg-red-50 dark:bg-red-900/20 rounded-full flex items-center justify-center mb-6">
          <WifiOff className="w-12 h-12 text-red-500 dark:text-red-400" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
          Связь потеряна
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-[280px]">
          Похоже, пропал интернет или сервер сейчас недоступен. Проверь подключение.
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="bg-[#00418f] hover:bg-[#003370] text-white font-semibold py-3.5 px-8 rounded-2xl transition-all active:scale-95 shadow-md border border-[#00418f]"
        >
          Повторить попытку
        </button>
      </div>
    );
  }
  
  const settingsOptions = [
    {
      id: 'timezone',
      label: 'Часовой пояс',
      value: userSettings.timezone,
      type: 'select',
      icon: <Globe className="w-5 h-5 text-gray-500" />,
      options: [
        { val: 'Europe/Moscow', text: 'Москва (MSK)' },
        { val: 'Europe/Samara', text: 'Самара (SAMT)' },
        { val: 'Asia/Yekaterinburg', text: 'Екатеринбург (YEKT)' },
        { val: 'Asia/Omsk', text: 'Омск (OMST)' },
        { val: 'Asia/Krasnoyarsk', text: 'Красноярск (KRAT)' },
        { val: 'Asia/Irkutsk', text: 'Иркутск (IRKT)' },
        { val: 'Asia/Yakutsk', text: 'Якутск (YAKT)' },
        { val: 'Asia/Vladivostok', text: 'Владивосток (VLAT)' },
      ]
    },
    {
      id: 'reminder_time',
      label: 'Время опроса',
      value: userSettings.reminder_time,
      type: 'select', 
      icon: <Clock className="w-5 h-5 text-gray-500" />,
      options: Array.from({ length: 12 }, (_, i) => {
        const hour = i * 2;
        return { val: `${hour.toString().padStart(2, '0')}:00`, text: `${hour}:00` };
      })
    },
    {
      id: 'digest_day',
      label: 'День дайджеста',
      value: userSettings.digest_day,
      type: 'select',
      icon: <Calendar className="w-5 h-5 text-gray-500" />,
      options: [
        { val: 0, text: 'Понедельник' },
        { val: 1, text: 'Вторник' },
        { val: 2, text: 'Среда' },
        { val: 3, text: 'Четверг' },
        { val: 4, text: 'Пятница' },
        { val: 5, text: 'Суббота' },
        { val: 6, text: 'Воскресенье' }
      ]
    },
    {
      id: 'digest_time',
      label: 'Время дайджеста',
      value: userSettings.digest_time,
      type: 'select',
      icon: <History className="w-5 h-5 text-gray-500" />,
      options: Array.from({ length: 12 }, (_, i) => {
        const hour = i * 2;
        return { val: hour, text: `${hour}:00` };
      })
    }
  ];

  const renderScreen = () => {
    switch (activeTab) {
      case 'profile':
        return <ProfileScreen />;
      case 'calendar':
        return <CalendarScreen />;
      case 'analytics':
        return <AnalyticsScreen />;
      default:
        return <ProfileScreen />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-gray-900 dark:text-slate-100 pb-[100px] transition-colors duration-200">
      
      <Header onSettingsClick={() => setSettingsOpen(true)} />

      <main className="w-full max-w-md mx-auto pt-[72px] px-4">
        {renderScreen()}
      </main>

      <BottomNav activeTab={activeTab} onTabChange={(tab) => setActiveTab(tab)} />

      {settingsOpen && (
        <div 
          className={`fixed inset-0 z-50 flex justify-center items-end bg-black/50 backdrop-blur-xs transition-opacity duration-300 ${isClosing ? 'opacity-0' : 'opacity-100'}`}
          onClick={closeSettings}
        >
          <div 
            onClick={(e) => e.stopPropagation()}
            onTouchStart={onTouchStart}
            onTouchMove={onTouchMove}
            onTouchEnd={onTouchEnd}
            style={{ 
              transform: `translateY(${isClosing ? '100%' : dragY + 'px'})`, 
              transition: dragY > 0 ? 'none' : 'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)' 
            }}
            className="w-full max-w-md bg-white dark:bg-slate-900 rounded-t-3xl rounded-b-none border-t border-gray-200/40 dark:border-slate-800/40 shadow-2xl max-h-[90vh] overflow-y-auto pb-8 flex flex-col pt-3 animate-fade-in-up"
          >
            <div className="w-full pt-2 flex justify-center cursor-pointer" onClick={closeSettings}>
              <div className="w-12 h-1.5 bg-gray-300 dark:bg-gray-600 rounded-full mx-auto shrink-0 mb-4" />
            </div>

            <div className="px-6 pb-2">
              <div className="flex justify-center mb-4 pb-2 border-b border-gray-100 dark:border-slate-800/60">
                <h3 className="font-sans font-bold text-lg text-gray-900 dark:text-white text-center">
                  Настройки приложения
                </h3>
              </div>

              <div className="flex flex-col gap-2 mt-2">
                {settingsOptions.map((opt) => (
                  <div
                    key={opt.id}
                    className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800/40 rounded-xl flex items-center justify-between border border-transparent"
                  >
                    <div className="flex items-center gap-3">
                      {opt.icon}
                      <span className="font-sans text-sm font-semibold text-gray-800 dark:text-gray-200">
                        {opt.label}
                      </span>
                    </div>
                    
                    {opt.type === 'select' && (
                      <select 
                        value={opt.value}
                        onChange={(e) => {
                          const isStringValue = opt.id === 'timezone' || opt.id === 'reminder_time';
                          updateSetting(opt.id, isStringValue ? e.target.value : Number(e.target.value));
                        }}
                        className="font-sans text-sm font-semibold text-[#0058bc] dark:text-blue-400 bg-[#0058bc]/10 dark:bg-blue-900/20 px-3 py-1.5 rounded-lg outline-none cursor-pointer text-center"
                      >
                        {opt.options?.map(choice => (
                          <option key={choice.val} value={choice.val} className="text-gray-900 bg-white">
                            {choice.text}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}