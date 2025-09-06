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

type IpcConfig = {
  mode: 'http' | 'uds';
  port: number;
  udsPath: string;
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

async function getIpcConfig(): Promise<IpcConfig> {
  try {
    return await ipcRenderer.invoke('get-ipc-config');
  } catch {
    return {
      mode: 'http',
      port: 8000,
      udsPath: '/tmp/zsim_api.sock',
    };
  }
}

async function httpRequest(
  method: string,
  p: string,
  opts: RequestOptions = {},
): Promise<IpcResponse> {
  const ipcConfig = await getIpcConfig();
  const headers = { 'content-type': 'application/json', ...(opts.headers || {}) };

  if (ipcConfig.mode === 'uds') {
    // UDS模式 - 通过IPC调用主进程的HTTP请求功能
    const requestConfig = {
      method,
      path: p,
      headers,
      body: opts.body,
      query: opts.query,
      udsPath: ipcConfig.udsPath,
    };

    const result = await ipcRenderer.invoke('make-uds-request', requestConfig);
    return result;
  } else {
    // HTTP模式
    const base = `http://127.0.0.1:${ipcConfig.port}`;
    const url = buildUrl(base, p, opts.query);

    const res = await fetch(url, {
      method,
      headers,
      body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
    });

    const text = await res.text();
    const outHeaders: Record<string, string> = {};
    res.headers.forEach((v, k) => (outHeaders[k] = v));

    return { status: res.status, headers: outHeaders, body: text };
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
  },
};

contextBridge.exposeInMainWorld('apiClient', apiClient);
