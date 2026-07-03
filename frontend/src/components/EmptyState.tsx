import React from 'react';
import { Sparkles } from 'lucide-react';
import { t, Language } from '../i18n';

export default function EmptyState({ lang = 'ru' }: { lang?: Language }) {
  const handleClose = () => {
    if (window.Telegram?.WebApp?.close) {
      window.Telegram.WebApp.close();
    } else {
      console.log('Telegram WebApp close triggered');
    }
  };

  return (
    <div className="animate-fade-in-up flex flex-col items-center justify-center p-6 bg-white dark:bg-slate-900 rounded-2xl border border-gray-200/40 dark:border-slate-800/40 shadow-xs text-center min-h-[320px] relative overflow-hidden">
      {/* Декоративный фоновый градиент */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-[#00418f]/10 dark:bg-blue-500/10 rounded-full blur-2xl -mr-12 -mt-12 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-32 h-32 bg-blue-500/10 dark:bg-purple-500/10 rounded-full blur-2xl -ml-12 -mb-12 pointer-events-none" />

      {/* Иконка в круглой плашке */}
      <div className="w-16 h-16 bg-blue-50 dark:bg-blue-950/40 border border-blue-100 dark:border-blue-900/40 rounded-full flex items-center justify-center mb-4 shadow-inner">
        <Sparkles className="w-8 h-8 text-[#00418f] dark:text-[#adc6ff] animate-pulse" />
      </div>

      {/* Текст */}
      <h3 className="font-sans font-bold text-xl text-gray-900 dark:text-white mb-2 tracking-tight">
        {t('empty_data', lang)}
      </h3>
      <p className="font-sans text-sm text-gray-500 dark:text-gray-400 mb-6 max-w-xs leading-relaxed">
        {t('empty_data_desc', lang)}
      </p>

      {/* Кнопка CTA */}
      <button
        onClick={handleClose}
        className="w-full max-w-[240px] py-3 bg-[#00418f] hover:bg-[#00316e] text-white font-sans text-sm font-semibold rounded-xl shadow-md hover:shadow-lg transition-all active:scale-[0.98] flex items-center justify-center gap-2"
      >
        <span>📝 {t('no_records_yet', lang).split('.')[0]}</span>
      </button>
    </div>
  );
}