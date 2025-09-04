import React, { createContext, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { TFunction } from 'i18next';

export type Language = 'en' | 'zh';
export type LocaleKeys = 'en-US' | 'zh-CN';

interface LanguageContextType {
  language: Language;
  locale: LocaleKeys;
  setLanguage: (lang: Language) => void;
  setLocale: (locale: LocaleKeys) => void;
  t: TFunction;
}

const isValidLanguage = (lang: string): lang is Language => {
  return ['en', 'zh'].includes(lang);
};

const languageToLocale = (lang: Language): LocaleKeys => {
  return lang === 'en' ? 'en-US' : 'zh-CN';
};

const localeToLanguage = (locale: LocaleKeys): Language => {
  return locale === 'en-US' ? 'en' : 'zh';
};

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export interface LanguageProviderProps {
  children: React.ReactNode;
}

export const LanguageProvider: React.FC<LanguageProviderProps> = ({ children }) => {
  const { i18n, t } = useTranslation();

  const currentLang = (i18n.language || 'zh').split('-')[0];
  const language = isValidLanguage(currentLang) ? currentLang : 'zh';
  const locale = languageToLocale(language);

  const setLanguage = (lang: Language) => {
    i18n.changeLanguage(lang);
    localStorage.setItem('language', lang);
  };

  const setLocale = (newLocale: LocaleKeys) => {
    const lang = localeToLanguage(newLocale);
    setLanguage(lang);
  };

  useEffect(() => {
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage && isValidLanguage(savedLanguage)) {
      i18n.changeLanguage(savedLanguage);
    }
  }, [i18n]);

  return React.createElement(
    LanguageContext.Provider,
    { value: { language, locale, setLanguage, setLocale, t } },
    children,
  );
};

export { LanguageProvider as default };
