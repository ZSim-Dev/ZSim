import './assets/main.css'
import '@douyinfe/semi-ui/dist/css/semi.min.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { ConfigProvider } from '@douyinfe/semi-ui'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider>
      <App />
    </ConfigProvider>
  </StrictMode>
)
