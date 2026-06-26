import React from 'react';
import { Settings } from 'lucide-react';

interface HeaderProps {
  onSettingsClick?: () => void;
}

export default function Header({ onSettingsClick }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-40 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl border-b border-gray-200/30 dark:border-slate-800/30 transition-all">
      <div className="flex items-center justify-between px-4 h-14 max-w-md mx-auto relative">
        <div className="flex items-center">
          <img
            alt="DayLog AI Logo"
            className="w-8 h-8 rounded-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuC5Sk8wHtAWkDYeOS1M1Ge2I2gewHf-D2yYy5YZXYzgNcm5b0Cu8bM_pjQ8h_6N1BhSdZ95JkYS-R8yRaQ9NRK2seCztL4Qe8fCD-k0Ywqx9XWc74NJM8O_NQD6R_nR9RMvI0R7lFy15Nw1GfmE8WAfpfWB9tpgQ7kndVUQdCXDOjMPWtaDwc3LCKkArNcgbmH2kJi9MeCskC2pHDtES9lMpbegTLt-Ozx83Y6OCSIC1FHBRNFHjx7GVLb-C0GlKSAb9w"
          />
        </div>
        <div className="absolute left-1/2 -translate-x-1/2 flex items-center">
          <h1 className="font-sans font-bold text-lg text-[#00418f] dark:text-[#adc6ff] tracking-tight">
            DayLog AI
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
