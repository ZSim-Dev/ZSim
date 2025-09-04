import React from 'react';
import { useLanguage } from '../hooks';

interface LanguageSwitchProps {
  className?: string;
}

export const LanguageSwitch: React.FC<LanguageSwitchProps> = ({ className = '' }) => {
  const { language, setLanguage } = useLanguage();

  return (
    <div className={`flex gap-[4px] ${className}`}>
      <div
        className={`
          px-[10px] h-[32px] rounded-[8px] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80
          ${language === 'zh' ? 'bg-[#FA7319]' : 'bg-[#333]'}
        `}
        onClick={() => setLanguage('zh')}
      >
        中文
      </div>
      <div
        className={`
          px-[10px] h-[32px] rounded-[8px] flex items-center text-[14px] text-white cursor-pointer select-none hover:brightness-90 active:brightness-80
          ${language === 'en' ? 'bg-[#FA7319]' : 'bg-[#333]'}
        `}
        onClick={() => setLanguage('en')}
      >
        English
      </div>
    </div>
  );
};

export default LanguageSwitch;
