import { useTranslation } from 'react-i18next'

export type LocaleKeys = 'en-US' | 'zh-CN'

export const useLocales = () => {
  const { t, i18n } = useTranslation()

  const locale = i18n.language === 'en' ? 'en-US' : 'zh-CN'
  
  const setLocale = (newLocale: 'en-US' | 'zh-CN') => {
    i18n.changeLanguage(newLocale === 'en-US' ? 'en' : 'zh')
  }

  return {
    t,
    locale,
    setLocale,
  }
}