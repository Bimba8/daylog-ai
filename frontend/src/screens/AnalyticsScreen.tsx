import React, { useState, useEffect } from 'react';
import { Smile, Zap, TrendingUp, AlertTriangle, Sparkles, Sliders, Check } from 'lucide-react';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import { apiClient } from '../api/client';
import EmptyState from '../components/EmptyState';
import { t, Language } from '../i18n';

type MetricType = 'mood' | 'energy' | 'stress' | 'productivity';

export default function AnalyticsScreen({ lang = 'ru' }: { lang?: Language }) {
  const [timePeriod, setTimePeriod] = useState<'7days' | '30days'>('30days');
  const [activeMetric, setActiveMetric] = useState<MetricType>('mood');
  
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setIsLoading(true);
      try {
        const data = await apiClient(`/stats/analytics?period=${timePeriod}`);
        setAnalyticsData(data);
      } catch (error) {
        console.error('Ошибка загрузки аналитики:', error);
      } finally {
        setIsLoading(false);
      }
    }
    loadData();
  }, [timePeriod]);

  if (isLoading && !analyticsData) {
    return (
      <div className="animate-pulse flex flex-col gap-5">
        <div className="flex justify-center"><div className="h-9 w-[240px] bg-gray-200 dark:bg-slate-800/80 rounded-full" /></div>
        <div className="flex gap-2 overflow-hidden">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-8 w-28 shrink-0 bg-gray-200 dark:bg-slate-800/80 rounded-full" />)}
        </div>
        <div className="bg-gray-100 dark:bg-slate-900 rounded-2xl h-[250px]" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-100 dark:bg-slate-900 rounded-xl h-[200px]" />
          <div className="flex flex-col gap-4">
            <div className="bg-gray-100 dark:bg-slate-900 rounded-xl h-[90px]" />
            <div className="bg-gray-100 dark:bg-slate-900 rounded-xl h-[90px]" />
          </div>
        </div>
      </div>
    );
  }

  if (!isLoading && analyticsData?.total_entries === 0) {
    return <EmptyState lang={lang} />;
  }

  const avgs = analyticsData?.averages || {
    mood: { value: 4.2, diff: '+0.4' }, energy: { value: 3.8, diff: '+0.2' },
    stress: { value: 2.1, diff: '-0.5' }, productivity: { value: 4.3, diff: '+0.6' }
  };

  const insights = analyticsData?.insights || { resources: ['Спорт', 'Код', 'Сон', 'Прогулка'], energy_leaks: ['Дедлайны', 'Недосып', 'Алкоголь'] };

  const stressValue = avgs.stress.value;
  let stressIcon = <AlertTriangle className="w-5 h-5" />;
  let stressColorClass = 'text-red-500 bg-red-100 dark:bg-red-950/40';
  let stressStrokeColor = '#EF4444';
  let stressProgressBarColor = 'bg-red-500';

  if (stressValue >= 1.0 && stressValue <= 2.0) {
    stressIcon = <Check className="w-5 h-5" />;
    stressColorClass = 'text-green-600 bg-green-100 dark:bg-green-950/40';
    stressStrokeColor = '#10B981';
    stressProgressBarColor = 'bg-green-500';
  } else if (stressValue > 2.0 && stressValue <= 4.0) {
    stressIcon = <AlertTriangle className="w-5 h-5 text-amber-500" />;
    stressColorClass = 'text-amber-500 bg-amber-100 dark:bg-amber-950/40';
    stressStrokeColor = '#F59E0B';
    stressProgressBarColor = 'bg-amber-500';
  }

  const balanceMetrics = [
    { name: t('mood', lang), value: avgs.mood.value, percentage: (avgs.mood.value / 5) * 100, color: 'bg-blue-500' },
    { name: t('energy', lang), value: avgs.energy.value, percentage: (avgs.energy.value / 5) * 100, color: 'bg-cyan-500' },
    { name: t('stress', lang), value: stressValue, percentage: (stressValue / 5) * 100, color: stressProgressBarColor },
    { name: t('productivity', lang), value: avgs.productivity.value, percentage: (avgs.productivity.value / 5) * 100, color: 'bg-indigo-500' },
  ];

  const metricTabsData = [
    {
      id: 'mood' as MetricType, label: t('mood', lang), title: lang === 'en' ? 'AVERAGE MOOD' : 'СРЕДНЕЕ НАСТРОЕНИЕ',
      value: String(avgs.mood.value), diff: avgs.mood.diff,
      icon: <Smile className="w-5 h-5" />,
      colorClass: 'text-blue-600 bg-blue-100 dark:bg-blue-950/40', strokeColor: '#3B82F6'
    },
    {
      id: 'energy' as MetricType, label: t('energy', lang), title: lang === 'en' ? 'AVERAGE ENERGY' : 'СРЕДНЯЯ ЭНЕРГИЯ',
      value: String(avgs.energy.value), diff: avgs.energy.diff,
      icon: <Zap className="w-5 h-5" />,
      colorClass: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-950/40', strokeColor: '#06b6d4'
    },
    {
      id: 'stress' as MetricType, label: t('stress', lang), title: lang === 'en' ? 'STRESS LEVEL' : 'УРОВЕНЬ СТРЕССА',
      value: String(stressValue), diff: avgs.stress.diff,
      icon: stressIcon,
      colorClass: stressColorClass, strokeColor: stressStrokeColor
    },
    {
      id: 'productivity' as MetricType, label: t('productivity', lang), title: lang === 'en' ? 'PRODUCTIVITY' : 'ПРОДУКТИВНОСТЬ',
      value: String(avgs.productivity.value), diff: avgs.productivity.diff,
      icon: <TrendingUp className="w-5 h-5" />,
      colorClass: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/40', strokeColor: '#6366F1'
    }
  ];

  const currentTab = metricTabsData.find(t => t.id === activeMetric) || metricTabsData[0];
  const chartData = analyticsData?.chart || [];

  return (
    <div className={`animate-fade-in-up flex flex-col gap-5 transition-opacity duration-300 ${isLoading ? 'opacity-50 pointer-events-none' : 'opacity-100'}`}>
      <div className="w-full flex justify-center">
        <div className="bg-gray-100 dark:bg-slate-800/80 rounded-full p-1 flex w-full max-w-[240px] relative border border-gray-200/20">
          <button
            onClick={() => setTimePeriod('7days')}
            className={`flex-1 py-1.5 z-10 font-sans text-xs font-semibold text-center rounded-full transition-all ${
              timePeriod === '7days' ? 'bg-[#00418f] text-white shadow-xs' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            {lang === 'en' ? '7 Days' : '7 Дней'}
          </button>
          <button
            onClick={() => setTimePeriod('30days')}
            className={`flex-1 py-1.5 z-10 font-sans text-xs font-semibold text-center rounded-full transition-all ${
              timePeriod === '30days' ? 'bg-[#00418f] text-white shadow-xs' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            {lang === 'en' ? '30 Days' : '30 Дней'}
          </button>
        </div>
      </div>

      <div className="flex overflow-x-auto whitespace-nowrap gap-2 pb-2 px-1 -mx-4 shrink-0 no-scrollbar" style={{ scrollbarWidth: 'none' }}>
        <div className="flex gap-2 px-4 whitespace-nowrap">
          {metricTabsData.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveMetric(tab.id)}
              className={`snap-start shrink-0 px-4 py-2 rounded-full font-sans text-xs font-semibold transition-all ${
                activeMetric === tab.id
                  ? 'bg-[#00418f] text-white shadow-sm'
                  : 'bg-white dark:bg-slate-900 text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800 border border-gray-100 dark:border-slate-800/60'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <section className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-gray-200/40 dark:border-slate-800/40 shadow-xs flex flex-col gap-4">
        <div className="flex justify-between items-end">
          <div>
            <p className="font-sans text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-widest font-bold">
              {currentTab.title} ({timePeriod === '7days' ? (lang === 'en' ? '7 Days' : '7 Дней') : (lang === 'en' ? '30 Days' : '30 Дней')})
            </p>
            <div className="flex items-baseline gap-1.5 mt-0.5">
              <h2 className="font-sans font-bold text-3xl text-gray-900 dark:text-white">
                {currentTab.value}
              </h2>
              <span className={`font-sans text-xs font-bold leading-none px-1.5 py-0.5 rounded ${
                currentTab.id === 'stress' 
                  ? 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/20' 
                  : 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-950/20'
              }`}>
                {currentTab.diff}
              </span>
            </div>
          </div>
          <div className={`p-2 rounded-full flex items-center justify-center ${currentTab.colorClass}`}>
            {currentTab.icon}
          </div>
        </div>

        <div className="w-full h-[180px] relative mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 12, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id={`areaGradient-${activeMetric}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={currentTab.strokeColor} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={currentTab.strokeColor} stopOpacity="0" />
                </linearGradient>
              </defs>
              <XAxis 
                dataKey="day" 
                tickLine={false} 
                axisLine={false}
                interval={0}
                tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'sans-serif' }}
                tickFormatter={(value, index) => {
                  // Смотрим на реальные данные, а не на кнопку
                  if (chartData.length <= 7) return value; 
                  if (index === 0 || index === 4 || index === 9 || index === 14 || index === 19 || index === 24 || index === 29) return value;
                  return '';
                }}
              />
              <YAxis domain={[1, 5]} tickLine={false} axisLine={false} tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'sans-serif' }} />
              <Tooltip 
                cursor={{ stroke: '#4B5563', strokeWidth: 1, strokeDasharray: '4 4' }}
                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '0.5rem', color: '#f8fafc' }}
                itemStyle={{ color: '#f8fafc', fontWeight: '500' }}
                labelStyle={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}
              />
              <Area
                isAnimationActive={true}
                type="monotone"
                dataKey={activeMetric}
                stroke={currentTab.strokeColor}
                strokeWidth={3}
                fillOpacity={1}
                fill={`url(#areaGradient-${activeMetric})`}
                activeDot={{ r: 6, fill: '#ffffff', stroke: currentTab.strokeColor, strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <section className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-gray-200/40 dark:border-slate-800/40 flex flex-col gap-4">
          <div className="flex items-center gap-1.5">
            <Sliders className="w-4.5 h-4.5 text-[#00418f] dark:text-[#adc6ff]" />
            <h3 className="font-sans font-bold text-[15px] text-gray-950 dark:text-white">
              {lang === 'en' ? 'State Balance' : 'Баланс состояния'}
            </h3>
          </div>
          <div className="flex flex-col gap-4 mt-2">
            {balanceMetrics.map((met) => (
              <div key={met.name} className="flex flex-col gap-1.5">
                <div className="flex justify-between items-center text-xs font-semibold text-gray-800 dark:text-gray-300">
                  <span>{met.name}</span>
                  <span className="text-gray-500 dark:text-gray-400 font-bold">{met.value} / 5</span>
                </div>
                <div className="w-full h-2 bg-gray-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full ${met.color} rounded-full transition-all duration-500`} style={{ width: `${met.percentage}%` }} />
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="flex flex-col gap-4">
          <section className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">🚀</span>
              <h3 className="font-sans font-bold text-sm text-gray-950 dark:text-white">
                {t('top_resources', lang)}
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {insights.resources.length === 0 ? (
                <span className="text-gray-400 dark:text-slate-500 text-xs italic font-sans">
                  {lang === 'en' ? 'None found yet. Take some time to rest! 🍵' : 'Пока не обнаружено. Пора уделить время себе и отдохнуть! 🍵'}
                </span>
              ) : (
                insights.resources.map((tag: string) => (
                  <span key={tag} className="px-3 py-1 bg-green-50 dark:bg-green-950/20 text-green-700 dark:text-green-300 rounded-full font-sans text-xs font-semibold border border-green-100/50 dark:border-green-900/30">
                    {tag}
                  </span>
                ))
              )}
            </div>
          </section>

          <section className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-gray-200/40 dark:border-slate-800/40 flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span className="text-lg">🪫</span>
              <h3 className="font-sans font-bold text-sm text-gray-950 dark:text-white">
                {t('top_leaks', lang)}
              </h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {insights.energy_leaks.length === 0 ? (
                <span className="text-gray-400 dark:text-slate-500 text-xs italic font-sans">
                  {lang === 'en' ? 'Everything is perfect, no leaks found! ✨' : 'Всё идеально, утечек не обнаружено! ✨'}
                </span>
              ) : (
                insights.energy_leaks.map((tag: string) => (
                  <span key={tag} className="px-3 py-1 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300 rounded-full font-sans text-xs font-semibold border border-red-100/50 dark:border-red-900/30">
                    {tag}
                  </span>
                ))
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}