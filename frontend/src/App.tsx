import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { Globe, Clock, Calendar, History, Loader2, WifiOff, X } from 'lucide-react'; 
import Header from './components/Header';
import BottomNav from './components/BottomNav';
import ProfileScreen from './screens/ProfileScreen';
import CalendarScreen from './screens/CalendarScreen';
import AnalyticsScreen from './screens/AnalyticsScreen';
import { apiClient, setToken } from './api/client'; 
import { t, Language } from './i18n';

declare global {
  interface Window {
    Telegram: any;
  }
}

type TabType = 'profile' | 'calendar' | 'analytics';

function HybridSelect({ value, onChange, options, className }: {
  value: string | number;
  onChange: (val: string) => void;
  options: { val: string | number; text: string }[];
  className?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState<{ top: number | 'auto', bottom: number | 'auto', right: number, width: number }>({ top: 0, bottom: 'auto', right: 0, width: 0 });
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const platform = window.Telegram?.WebApp?.platform || 'unknown';
  const isMobile = ['android', 'android_x', 'ios'].includes(platform);

  const updatePosition = () => {
    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const spaceBelow = window.innerHeight - rect.bottom;
      const spaceAbove = rect.top;
      
      if (spaceBelow < 200 && spaceAbove > spaceBelow) {
        setCoords({
          top: 'auto',
          bottom: window.innerHeight - rect.top + 4,
          right: window.innerWidth - rect.right,
          width: rect.width
        });
      } else {
        setCoords({
          top: rect.bottom + 4,
          bottom: 'auto',
          right: window.innerWidth - rect.right,
          width: rect.width
        });
      }
    }
  };

  const openDropdown = () => {
    if (!isOpen) {
      updatePosition();
      setIsOpen(true);
    } else {
      setIsOpen(false);
    }
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const isOutsideContainer = containerRef.current && !containerRef.current.contains(e.target as Node);
      const isOutsideDropdown = dropdownRef.current && !dropdownRef.current.contains(e.target as Node);
      
      if (isOutsideContainer && isOutsideDropdown) {
        setIsOpen(false);
      }
    };

    const handleScroll = (e: Event) => {
      if (dropdownRef.current && dropdownRef.current.contains(e.target as Node)) {
        return;
      }
      if (isOpen) setIsOpen(false);
    };
    
    const handleResize = () => {
      if (isOpen) setIsOpen(false);
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      window.addEventListener('scroll', handleScroll, true);
      window.addEventListener('resize', handleResize);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleResize);
    };
  }, [isOpen]);

  if (isMobile) {
    return (
      <select 
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={className}
      >
        {options.map(opt => (
          <option key={opt.val} value={opt.val} className="text-gray-900 bg-white">
            {opt.text}
          </option>
        ))}
      </select>
    );
  }

  const selectedText = options.find(o => o.val === value)?.text || value;

  return (
    <div className="relative" ref={containerRef}>
      <div 
        className={`${className} flex items-center justify-between gap-1 min-w-[80px]`}
        onClick={openDropdown}
      >
        <span className="truncate flex-1">{selectedText}</span>
        <svg className={`w-4 h-4 opacity-50 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path></svg>
      </div>
      
      {isOpen && createPortal(
        <div 
          ref={dropdownRef}
          className="fixed max-h-48 overflow-y-auto bg-white dark:bg-slate-800 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.2)] border border-gray-100 dark:border-slate-700 z-[9999] py-1 flex flex-col" 
          style={{ top: coords.top, bottom: coords.bottom, right: coords.right, minWidth: Math.max(120, coords.width), scrollbarWidth: 'none' }}
        >
          {options.map(opt => (
            <div 
              key={opt.val}
              className={`px-4 py-2 text-sm cursor-pointer whitespace-nowrap transition-colors ${opt.val === value ? 'text-[#0058bc] dark:text-blue-400 font-bold bg-blue-50/50 dark:bg-blue-900/20' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-700'}`}
              onClick={() => {
                onChange(String(opt.val));
                setIsOpen(false);
              }}
            >
              {opt.text}
            </div>
          ))}
        </div>,
        document.body
      )}
    </div>
  );
}


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
    digest_time: 10,
    language_code: (window.Telegram?.WebApp?.initDataUnsafe?.user?.language_code === 'en' ? 'en' : 'ru') as Language
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
        setToken(data.access_token);
        const profile = await apiClient('/profile');
        setUserSettings({
          timezone: profile.timezone,
          reminder_time: profile.reminder_time,
          digest_day: profile.digest_day,
          digest_time: profile.digest_time,
          language_code: (profile.language_code || 'ru') as Language
        });
        setIsAuthLoading(false);
      } catch (error) {
        if (import.meta.env.DEV) console.error('Ошибка авторизации:', error);
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
      if (import.meta.env.DEV) console.error('Ошибка сохранения:', error);
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
          {t('conn_lost', userSettings.language_code)}
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-[280px]">
          {t('conn_lost_desc', userSettings.language_code)}
        </p>
        <button 
          onClick={() => window.location.reload()}
          className="bg-[#00418f] hover:bg-[#003370] text-white font-semibold py-3.5 px-8 rounded-2xl transition-all active:scale-95 shadow-md border border-[#00418f]"
        >
          {t('retry', userSettings.language_code)}
        </button>
      </div>
    );
  }
  
  const settingsOptions = [
    {
      id: 'language_code',
      label: t('language', userSettings.language_code),
      value: userSettings.language_code,
      type: 'select',
      icon: <Globe className="w-5 h-5 text-gray-500" />,
      options: [
        { val: 'ru', text: t('lang_ru', userSettings.language_code) },
        { val: 'en', text: t('lang_en', userSettings.language_code) }
      ]
    },
    {
      id: 'timezone',
      label: t('timezone', userSettings.language_code),
      value: userSettings.timezone,
      type: 'select',
      icon: <Globe className="w-5 h-5 text-gray-500" />,
      options: userSettings.language_code === 'en' ? [
        { val: 'Etc/GMT+12', text: 'UTC-12:00' },
        { val: 'Etc/GMT+11', text: 'UTC-11:00' },
        { val: 'Etc/GMT+10', text: 'UTC-10:00' },
        { val: 'Etc/GMT+9', text: 'UTC-09:00' },
        { val: 'Etc/GMT+8', text: 'UTC-08:00' },
        { val: 'Etc/GMT+7', text: 'UTC-07:00' },
        { val: 'Etc/GMT+6', text: 'UTC-06:00' },
        { val: 'Etc/GMT+5', text: 'UTC-05:00' },
        { val: 'Etc/GMT+4', text: 'UTC-04:00' },
        { val: 'Etc/GMT+3', text: 'UTC-03:00' },
        { val: 'Etc/GMT+2', text: 'UTC-02:00' },
        { val: 'Etc/GMT+1', text: 'UTC-01:00' },
        { val: 'UTC', text: 'UTC+00:00' },
        { val: 'Etc/GMT-1', text: 'UTC+01:00' },
        { val: 'Etc/GMT-2', text: 'UTC+02:00' },
        { val: 'Etc/GMT-3', text: 'UTC+03:00' },
        { val: 'Etc/GMT-4', text: 'UTC+04:00' },
        { val: 'Etc/GMT-5', text: 'UTC+05:00' },
        { val: 'Etc/GMT-6', text: 'UTC+06:00' },
        { val: 'Etc/GMT-7', text: 'UTC+07:00' },
        { val: 'Etc/GMT-8', text: 'UTC+08:00' },
        { val: 'Etc/GMT-9', text: 'UTC+09:00' },
        { val: 'Etc/GMT-10', text: 'UTC+10:00' },
        { val: 'Etc/GMT-11', text: 'UTC+11:00' },
        { val: 'Etc/GMT-12', text: 'UTC+12:00' },
        { val: 'Etc/GMT-13', text: 'UTC+13:00' },
        { val: 'Etc/GMT-14', text: 'UTC+14:00' },
      ] : [
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
      label: t('reminder_time', userSettings.language_code),
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
      label: t('digest_day', userSettings.language_code),
      value: userSettings.digest_day,
      type: 'select',
      icon: <Calendar className="w-5 h-5 text-gray-500" />,
      options: [
        { val: 0, text: t('day_monday', userSettings.language_code) },
        { val: 1, text: t('day_tuesday', userSettings.language_code) },
        { val: 2, text: t('day_wednesday', userSettings.language_code) },
        { val: 3, text: t('day_thursday', userSettings.language_code) },
        { val: 4, text: t('day_friday', userSettings.language_code) },
        { val: 5, text: t('day_saturday', userSettings.language_code) },
        { val: 6, text: t('day_sunday', userSettings.language_code) }
      ]
    },
    {
      id: 'digest_time',
      label: t('digest_time', userSettings.language_code),
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
        return <ProfileScreen lang={userSettings.language_code} />;
      case 'calendar':
        return <CalendarScreen lang={userSettings.language_code} />;
      case 'analytics':
        return <AnalyticsScreen lang={userSettings.language_code} />;
      default:
        return <ProfileScreen lang={userSettings.language_code} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-gray-900 dark:text-slate-100 pb-[100px] transition-colors duration-200">
      
      <Header onSettingsClick={() => setSettingsOpen(true)} lang={userSettings.language_code} />

      <main className="w-full max-w-md mx-auto pt-[72px] px-4">
        {renderScreen()}
      </main>

      <BottomNav activeTab={activeTab} onTabChange={(tab) => setActiveTab(tab)} lang={userSettings.language_code} />

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
              <div className="flex justify-between items-center mb-8">
                <h3 className="font-sans font-bold text-lg text-gray-900 dark:text-white">
                  {t('settings', userSettings.language_code)}
                </h3>
                <button 
                  onClick={closeSettings}
                  className="p-2 -mr-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors bg-gray-100 dark:bg-slate-800 rounded-full"
                >
                  <X className="w-5 h-5" />
                </button>
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
                      <HybridSelect 
                        value={opt.value}
                        options={opt.options || []}
                        onChange={(val) => {
                          const isStringValue = opt.id === 'timezone' || opt.id === 'reminder_time' || opt.id === 'language_code';
                          updateSetting(opt.id, isStringValue ? val : Number(val));
                        }}
                        className="font-sans text-sm font-semibold text-[#0058bc] dark:text-blue-400 bg-[#0058bc]/10 dark:bg-blue-900/20 px-3 py-1.5 rounded-lg outline-none cursor-pointer text-center"
                      />
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