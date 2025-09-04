import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n';
import Providers from './providers/Providers';
import '@/styles/main.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <App />
    </Providers>
  </StrictMode>,
);
