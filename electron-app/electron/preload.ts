import { electronAPI } from '@electron-toolkit/preload';
import { contextBridge } from 'electron';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';

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

const isDev = process.env.NODE_ENV === 'development' || !!process.env.VITE_DEV_SERVER_URL;

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

async function httpRequest(method: string, p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
  const base = 'http://127.0.0.1:8000';
  const url = buildUrl(base, p, opts.query);
  const headers = { 'content-type': 'application/json', ...(opts.headers || {}) } as Record<string, string>;
  const res = await fetch(url, {
    method,
    headers,
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body)
  });
  const text = await res.text();
  const outHeaders: Record<string, string> = {};
  res.headers.forEach((v, k) => (outHeaders[k] = v));
  return { status: res.status, headers: outHeaders, body: text };
}

function toFrame(data: Buffer): Buffer {
  const header = Buffer.allocUnsafe(4);
  header.writeUInt32BE(data.length, 0);
  return Buffer.concat([header, data]);
}

function fromFrames(stream: net.Socket, onMessage: (buf: Buffer) => void): void {
  let buffer = Buffer.alloc(0);
  let needed = -1;
  stream.on('data', (chunk) => {
    buffer = Buffer.concat([buffer, chunk]);
    // eslint-disable-next-line no-constant-condition
    while (true) {
      if (needed < 0) {
        if (buffer.length < 4) break;
        needed = buffer.readUInt32BE(0);
        buffer = buffer.subarray(4);
      }
      if (buffer.length < needed) break;
      const frame = buffer.subarray(0, needed);
      buffer = buffer.subarray(needed);
      needed = -1;
      onMessage(frame);
    }
  });
}

async function ipcRequest(method: string, p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
  const pipeName = process.env.ZSIM_IPC_PIPE_NAME || 'zsim_api';
  const udsPath = process.env.ZSIM_IPC_UDS_PATH || path.join(os.tmpdir(), 'zsim_api.sock');
  const socketPath = process.platform === 'win32' ? `\\.\\pipe\\${pipeName}` : udsPath;

  const payload = Buffer.from(
    JSON.stringify({
      method,
      path: p,
      query: opts.query || {},
      headers: opts.headers || {},
      body:
        opts.body === undefined
          ? undefined
          : typeof opts.body === 'string'
            ? opts.body
            : JSON.stringify(opts.body)
    })
  );

  return await new Promise<IpcResponse>((resolve, reject) => {
    const client = net.createConnection(socketPath, () => {
      client.write(toFrame(payload));
    });
    client.setNoDelay(true);
    client.on('error', (err) => {
      client.destroy();
      reject(err);
    });
    fromFrames(client, (buf) => {
      try {
        const resp = JSON.parse(buf.toString('utf-8')) as IpcResponse;
        resolve(resp);
      } catch (e) {
        reject(e);
      } finally {
        client.end();
        client.destroy();
      }
    });
  });
}

const apiClient = {
  async request(method: string, p: string, opts: RequestOptions = {}): Promise<IpcResponse> {
    if (isDev) return await httpRequest(method, p, opts);
    return await ipcRequest(method, p, opts);
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
