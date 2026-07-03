import React from 'react';
import { User, Calendar, LineChart } from 'lucide-react';
import { t, Language } from '../i18n';

interface BottomNavProps {
  activeTab: 'profile' | 'calendar' | 'analytics';
  onTabChange: (tab: 'profile' | 'calendar' | 'analytics') => void;
  lang?: Language;
}

export default function BottomNav({ activeTab, onTabChange, lang = 'ru' }: BottomNavProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-t border-gray-200/30 dark:border-slate-800/30 pb-[env(safe-area-inset-bottom,16px)]">
      <div className="flex justify-around items-center h-16 w-full max-w-md mx-auto px-2">
        {/* Profile Tab */}
        <button
          onClick={() => onTabChange('profile')}
          className={`flex flex-col items-center justify-center flex-1 h-12 transition-all relative group ${
            activeTab === 'profile'
              ? 'text-[#00418f] dark:text-[#adc6ff]'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <div
            className={`px-5 py-1 rounded-full transition-all flex items-center justify-center mb-0.5 ${
              activeTab === 'profile'
                ? 'bg-[#00418f]/10 dark:bg-[#00418f]/20 scale-100'
                : 'bg-transparent scale-90 group-hover:scale-95'
            }`}
          >
            <User className="w-5 h-5 stroke-[2]" />
          </div>
          <span className="text-[11px] font-semibold tracking-tight">{t('tab_profile', lang)}</span>
        </button>

        {/* Calendar Tab */}
        <button
          onClick={() => onTabChange('calendar')}
          className={`flex flex-col items-center justify-center flex-1 h-12 transition-all relative group ${
            activeTab === 'calendar'
              ? 'text-[#00418f] dark:text-[#adc6ff]'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <div
            className={`px-5 py-1 rounded-full transition-all flex items-center justify-center mb-0.5 ${
              activeTab === 'calendar'
                ? 'bg-[#00418f]/10 dark:bg-[#00418f]/20 scale-100'
                : 'bg-transparent scale-90 group-hover:scale-95'
            }`}
          >
            <Calendar className="w-5 h-5 stroke-[2]" />
          </div>
          <span className="text-[11px] font-semibold tracking-tight">{t('tab_calendar', lang)}</span>
        </button>

        {/* Analytics Tab */}
        <button
          onClick={() => onTabChange('analytics')}
          className={`flex flex-col items-center justify-center flex-1 h-12 transition-all relative group ${
            activeTab === 'analytics'
              ? 'text-[#00418f] dark:text-[#adc6ff]'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
          }`}
        >
          <div
            className={`px-5 py-1 rounded-full transition-all flex items-center justify-center mb-0.5 ${
              activeTab === 'analytics'
                ? 'bg-[#00418f]/10 dark:bg-[#00418f]/20 scale-100'
                : 'bg-transparent scale-90 group-hover:scale-95'
            }`}
          >
            <LineChart className="w-5 h-5 stroke-[2]" />
          </div>
          <span className="text-[11px] font-semibold tracking-tight">{t('tab_analytics', lang)}</span>
        </button>
      </div>
    </nav>
  );
}
