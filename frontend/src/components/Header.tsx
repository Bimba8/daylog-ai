import React from 'react';
import { Settings, Brain } from 'lucide-react';
import { t, Language } from '../i18n';

interface HeaderProps {
  onSettingsClick?: () => void;
  lang?: Language;
}

export default function Header({ onSettingsClick, lang = 'ru' }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-gray-200/30 dark:border-slate-800/30 transition-all">
      <div className="flex items-center justify-between px-4 h-14 max-w-md mx-auto relative">
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#00418f]/10 dark:bg-blue-500/20 text-[#00418f] dark:text-[#adc6ff]">
          <Brain className="w-5 h-5" />
        </div>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center">
          <h1 className="font-sans font-bold text-lg text-[#00418f] dark:text-[#adc6ff] tracking-tight">
            {t('appName', lang)}
          </h1>
        </div>
        <div className="flex items-center">
          <button
            onClick={onSettingsClick}
            className="text-gray-500 hover:text-[#00418f] dark:text-gray-300 dark:hover:text-white transition-colors p-1.5 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full flex items-center justify-center focus:outline-none"
            aria-label="Settings"
          >
            <Settings className="w-5 h-5 stroke-[2]" />
          </button>
        </div>
      </div>
    </header>
  );
}
