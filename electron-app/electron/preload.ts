import { electronAPI } from '@electron-toolkit/preload';
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electron', electronAPI);

type RequestOptions = {
  headers?: Record<string, string>;
  query?: Record<string, unknown>;
  body?: unknown;
};

type IpcResponse = {
  status: number;
  headers: Record<string, string>;
  body: string;
};

function buildUrl(base: string, p: string, query?: Record<string, unknown>): string {
  const url = new URL(p, base);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

async function getApiPort(): Promise<number> {
  try {
    return await ipcRenderer.invoke('get-api-port');
  } catch (error) {
    console.warn('Failed to get API port from main process, using default:', error);
    return 8000;
  }
}

async function httpRequest(method: string, p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
  const port = await getApiPort();
  const base = `http://127.0.0.1:${port}`;
  const url = buildUrl(base, p, opts.query);
  const headers = { 'content-type': 'application/json', ...(opts.headers || {}) } as Record<string, string>;
  
  console.log(`[HTTP] Attempting ${method} request to ${url}`);
  
  try {
    const res = await fetch(url, {
      method,
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body)
    });
    
    const text = await res.text();
    const outHeaders: Record<string, string> = {};
    res.headers.forEach((v, k) => (outHeaders[k] = v));
    
    console.log(`[HTTP] Response received: ${res.status} ${res.status < 400 ? 'OK' : 'ERROR'}`);
    
    return { status: res.status, headers: outHeaders, body: text };
  } catch (error) {
    console.error(`[HTTP] Request failed:`, error);
    throw error;
  }
}

const apiClient = {
  async request(method: string, p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
    return await httpRequest(method, p, opts);
  },
  async get(p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
    return await this.request('GET', p, opts);
  },
  async post(p: string, body?: unknown, opts: RequestOptions = {}): Promise<IpcResponse> {
    return await this.request('POST', p, { ...opts, body });
  },
  async put(p: string, body?: unknown, opts: RequestOptions = {}): Promise<IpcResponse> {
    return await this.request('PUT', p, { ...opts, body });
  },
  async delete(p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
    return await this.request('DELETE', p, opts);
  }
};

contextBridge.exposeInMainWorld('apiClient', apiClient);
console.log('[Preload] apiClient exposed to window.apiClient');