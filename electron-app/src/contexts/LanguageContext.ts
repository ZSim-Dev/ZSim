import React, { createContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { TFunction } from 'i18next';

export type Language = 'en' | 'zh';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: TFunction;
}

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export interface LanguageProviderProps {
  children: React.ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const { i18n, t } = useTranslation();

  const language = (i18n.language || 'zh').split('-')[0] as Language;

  const setLanguage = (lang: Language) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('language', lang);
  };

  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as Language;
    if (savedLanguage && ['en', 'zh'].includes(savedLanguage)) {
      i18n.changeLanguage(savedLanguage);
    }
  }, [i18n]);

  return React.createElement(
    LanguageContext.Provider,
    { value: { language, setLanguage, t } },
    children,
  );
};

export { LanguageProvider as default };
