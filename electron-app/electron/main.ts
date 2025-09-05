import { app, BrowserWindow, shell, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { electronApp, optimizer } from '@electron-toolkit/utils';
import { spawn, ChildProcess } from 'node:child_process';
import net from 'node:net';
import http from 'node:http';
import { URLSearchParams } from 'node:url';
import { existsSync } from 'node:fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// The built directory structure
//
// ├─┬─┬ dist
// │ │ └── index.html
// │ │
// │ ├─┬ dist-electron
// │ │ ├── main.js
// │ │ └── preload.mjs
// │
process.env.APP_ROOT = path.join(__dirname, '..');

// 🚧 Use ['ENV_NAME'] avoid vite:define plugin - Vite@2.x
export const VITE_DEV_SERVER_URL = process.env['VITE_DEV_SERVER_URL'];
export const MAIN_DIST = path.join(process.env.APP_ROOT, 'dist-electron');
export const RENDERER_DIST = path.join(process.env.APP_ROOT, 'dist');

process.env.VITE_PUBLIC = VITE_DEV_SERVER_URL
  ? path.join(process.env.APP_ROOT, 'public')
  : RENDERER_DIST;

let win: BrowserWindow | null;
let backendProcess: ChildProcess | null;
let backendPort: number = 8000; // 存储后端端口
let backendIpcMode: 'http' | 'uds' = 'http'; // 存储后端IPC模式
const backendUdsPath: string = '/tmp/zsim_api.sock'; // 存储后端UDS路径

function findAvailablePort(startPort: number = 8000, maxPort: number = 8100): Promise<number> {
  return new Promise((resolve, reject) => {
    const tryPort = (port: number) => {
      if (port > maxPort) {
        reject(new Error('No available ports found'));
        return;
      }

      const server = net.createServer();
      server.listen(port, '127.0.0.1', () => {
        const address = server.address();
        if (address && typeof address === 'object' && 'port' in address) {
          const availablePort = address.port;
          server.close(() => {
            resolve(availablePort);
          });
        } else {
          server.close(() => {
            reject(new Error('Invalid server address'));
          });
        }
      });

      server.on('error', () => {
        tryPort(port + 1);
      });
    };

    tryPort(startPort);
  });
}

async function startBackendServer() {
  console.log('[Backend] Starting API server...');

  // 在开发环境中，使用Python源码
  // 在生产环境中，使用打包好的二进制文件
  let backendCommand: string;
  let backendArgs: string[];
  let envVars: NodeJS.ProcessEnv;

  if (process.env.NODE_ENV === 'development') {
    // 开发环境：使用Python源码
    const projectRoot = path.join(__dirname, '..', '..');
    const backendScript = path.join(projectRoot, 'zsim', 'api.py');

    console.log('[Backend] Using Python script:', backendScript);

    // 确定IPC模式 - 在Unix类系统上默认使用UDS，Windows上使用HTTP
    let ipcMode: 'http' | 'uds' = 'uds';
    if (process.platform === 'win32') {
      ipcMode = 'http';
    }

    backendIpcMode = ipcMode;

    if (ipcMode === 'uds') {
      // UDS模式
      envVars = { ...process.env, ZSIM_IPC_MODE: 'uds', ZSIM_UDS_PATH: backendUdsPath };
      console.log(`[Backend] Using UDS mode with socket: ${backendUdsPath}`);
    } else {
      // HTTP模式
      const availablePort = await findAvailablePort();
      backendPort = availablePort;
      envVars = { ...process.env, ZSIM_API_PORT: availablePort.toString(), ZSIM_IPC_MODE: 'http' };
      console.log(`[Backend] Using HTTP mode with port: ${availablePort}`);
    }

    // 使用uv run python
    backendCommand = 'uv';
    backendArgs = ['run', 'python', backendScript];
  } else {
    // 生产环境：使用打包好的二进制文件
    // 尝试多个可能的路径
    const possiblePaths = [
      path.join(__dirname, '..', 'resources', 'zsim_api', 'zsim_api'), // 开发环境路径
      path.join(__dirname, '..', 'dist', 'zsim_api', 'zsim_api'), // 开发环境路径
      path.join(process.resourcesPath, 'resources', 'zsim_api', 'zsim_api'), // 生产环境路径
      path.join(process.resourcesPath, 'zsim_api', 'zsim_api'), // 备用生产环境路径
    ];

    let binaryPath: string | undefined;
    for (const testPath of possiblePaths) {
      if (existsSync(testPath)) {
        binaryPath = testPath;
        break;
      }
    }

    if (!binaryPath) {
      throw new Error(`Backend binary not found. Tried: ${possiblePaths.join(', ')}`);
    }

    console.log('[Backend] Using binary:', binaryPath);

    // 确定IPC模式 - 在Unix类系统上默认使用UDS，Windows上使用HTTP
    let ipcMode: 'http' | 'uds' = 'uds';
    if (process.platform === 'win32') {
      ipcMode = 'http';
    }

    backendIpcMode = ipcMode;

    if (ipcMode === 'uds') {
      // UDS模式
      envVars = { ...process.env, ZSIM_IPC_MODE: 'uds', ZSIM_UDS_PATH: backendUdsPath };
      console.log(`[Backend] Using UDS mode with socket: ${backendUdsPath}`);
    } else {
      // HTTP模式
      const availablePort = await findAvailablePort();
      backendPort = availablePort;
      envVars = { ...process.env, ZSIM_API_PORT: availablePort.toString(), ZSIM_IPC_MODE: 'http' };
      console.log(`[Backend] Using HTTP mode with port: ${availablePort}`);
    }

    // 直接使用二进制文件
    backendCommand = binaryPath;
    backendArgs = [];
  }

  console.log(`[Backend] Starting with: ${backendCommand} ${backendArgs.join(' ')}`);

  // 设置正确的工作目录
  let cwd: string;
  if (process.env.NODE_ENV === 'development') {
    cwd = path.join(__dirname, '..', '..');
  } else {
    // 生产环境：设置为包含 zsim_api 二进制文件的目录
    cwd = path.dirname(backendCommand);
  }

  console.log(`[Backend] Working directory: ${cwd}`);

  backendProcess = spawn(backendCommand, backendArgs, {
    env: envVars as typeof process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd,
  });

  backendProcess?.stdout?.on('data', data => {
    const message = data.toString().trim();
    if (message) {
      // 在开发环境中转发所有输出，在生产环境中过滤INFO消息
      if (process.env.NODE_ENV === 'development' || !message.includes('INFO:')) {
        console.log(`[Backend] ${message}`);
      }
    }
  });

  backendProcess?.stderr?.on('data', data => {
    const message = data.toString().trim();
    if (message) {
      // 在开发环境中转发所有输出，在生产环境中过滤INFO消息
      if (process.env.NODE_ENV === 'development' || !message.includes('INFO:')) {
        console.error(`[Backend] ${message}`);
      }
    }
  });

  backendProcess?.on('close', code => {
    console.log(`[Backend] Process exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess?.on('error', err => {
    console.error('[Backend] Failed to start:', err);
  });

  // 等待后端启动完成
  return new Promise<void>(resolve => {
    setTimeout(() => {
      if (backendIpcMode === 'uds') {
        console.log(`[Backend] UDS server started on ${backendUdsPath}`);
      } else {
        console.log(`[Backend] HTTP server started on port ${backendPort}`);
      }
      resolve();
    }, 3000); // 等待 3 秒让服务器启动
  });
}

function stopBackendServer() {
  if (backendProcess) {
    console.log('[Backend] Stopping Python API server...');
    backendProcess.kill();
    backendProcess = null;
  }
}

function createWindow() {
  // 尝试多个可能的preload路径
  let preloadPath = path.join(__dirname, 'preload.cjs'); // 默认路径
  const possiblePaths = [
    path.join(__dirname, 'preload.cjs'),
    path.join(process.env.APP_ROOT || '', 'dist-electron', 'preload.cjs'),
    path.join(process.env.APP_ROOT || process.cwd(), 'dist-electron', 'preload.cjs'),
  ];

  // 找到第一个存在的路径
  for (const testPath of possiblePaths) {
    if (existsSync(testPath)) {
      preloadPath = testPath;
      break;
    }
  }

  // 只在开发环境下输出调试信息
  if (process.env.NODE_ENV === 'development') {
    console.log('[Main] Preload script path:', preloadPath);
    console.log('[Main] Preload script exists:', existsSync(preloadPath));
  }

  win = new BrowserWindow({
    width: 1440,
    height: 800,
    minWidth: 900,
    minHeight: 500,
    show: false,
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: preloadPath,
      sandbox: false,
      nodeIntegration: false, // 保持false，使用preload脚本更安全
      contextIsolation: true, // 确保contextBridge工作
    },
  });

  win.setMenu(null);

  win.on('ready-to-show', () => {
    win?.show();
  });

  win.webContents.setWindowOpenHandler(details => {
    shell.openExternal(details.url);
    return { action: 'deny' };
  });

  if (VITE_DEV_SERVER_URL) {
    win.loadURL(VITE_DEV_SERVER_URL);
  } else {
    win.loadFile(path.join(RENDERER_DIST, 'index.html'));
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.electron.app');

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window);
  });

  ipcMain.on('ping', () => console.warn('pong'));

  // 处理获取API端口的请求
  ipcMain.handle('get-api-port', async () => {
    if (!backendProcess) {
      throw new Error('Backend server not running');
    }

    // 返回存储的端口号
    return backendPort;
  });

  // 处理获取IPC配置的请求
  ipcMain.handle('get-ipc-config', async () => {
    if (!backendProcess) {
      throw new Error('Backend server not running');
    }

    // 返回IPC配置
    return {
      mode: backendIpcMode,
      port: backendPort,
      udsPath: backendUdsPath,
    };
  });

  // 处理UDS请求
  ipcMain.handle('make-uds-request', async (_, requestConfig) => {
    const { method, path, headers, body, query, udsPath } = requestConfig;

    return new Promise((resolve, reject) => {
      let requestPath = path;

      // 处理查询参数
      if (query) {
        const queryString = new URLSearchParams(query).toString();
        if (queryString) {
          requestPath += (requestPath.includes('?') ? '&' : '?') + queryString;
        }
      }

      const options = {
        socketPath: udsPath,
        path: requestPath,
        method: method,
        headers: headers || {},
      };

      const req = http.request(options, res => {
        let data = '';

        res.on('data', chunk => {
          data += chunk;
        });

        res.on('end', () => {
          const outHeaders: Record<string, string> = {};
          Object.entries(res.headers).forEach(([k, v]) => {
            if (typeof v === 'string') {
              outHeaders[k] = v;
            } else if (Array.isArray(v)) {
              outHeaders[k] = v.join(', ');
            }
          });

          resolve({
            status: res.statusCode || 500,
            headers: outHeaders,
            body: data,
          });
        });
      });

      req.on('error', error => {
        console.error(`[Main] UDS request failed:`, error);
        reject(error);
      });

      if (body !== undefined) {
        req.write(JSON.stringify(body));
      }

      req.end();
    });
  });

  // 启动后端服务器
  try {
    await startBackendServer();
  } catch (error) {
    console.error('[Main] Failed to start backend server:', error);
  }

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    stopBackendServer();
    app.quit();
    win = null;
  }
});

app.on('before-quit', () => {
  stopBackendServer();
});
