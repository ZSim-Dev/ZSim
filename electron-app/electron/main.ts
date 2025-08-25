import { app, BrowserWindow, shell, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { electronApp, optimizer } from '@electron-toolkit/utils';
import { spawn, ChildProcess, spawnSync } from 'node:child_process';
import net from 'node:net';
import { platform } from 'node:os';
import http from 'node:http';
import { URLSearchParams } from 'node:url';

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
let backendUdsPath: string = '/tmp/zsim_api.sock'; // 存储后端UDS路径

function findPythonExecutable(): string {
  // 优先尝试使用 uv run python
  const uvPython = 'uv run python';
  
  // 尝试 python3 和 python 命令
  const pythonCommands = ['python3', 'python'];
  
  // 在开发环境中，优先使用 uv run python
  if (process.env.NODE_ENV === 'development') {
    return uvPython;
  }
  
  // 在生产环境中，尝试找到合适的 python 命令
  for (const cmd of pythonCommands) {
    try {
      const result = spawnSync(cmd, ['--version'], { stdio: 'pipe' });
      if (result.status === 0) {
        return cmd;
      }
    } catch {
      continue;
    }
  }
  
  // 默认返回 python
  return 'python';
}

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
  console.log('[Backend] Starting Python API server...');
  
  // 在开发环境中，使用相对路径到项目根目录
  // 在生产环境中，使用相对于 electron-app 的路径
  let backendScript: string;
  
  if (process.env.NODE_ENV === 'development') {
    // 开发环境：从 electron-app 目录回到项目根目录，然后到 zsim/api.py
    const projectRoot = path.join(__dirname, '..', '..');
    backendScript = path.join(projectRoot, 'zsim', 'api.py');
  } else {
    // 生产环境：从 electron-app 目录回到项目根目录，然后到 zsim/api.py
    const projectRoot = path.join(__dirname, '..');
    backendScript = path.join(projectRoot, 'zsim', 'api.py');
  }
  
  console.log('[Backend] Using script:', backendScript);
  
  // 确定IPC模式
  const currentPlatform = platform();
  let ipcMode: 'http' | 'uds' = 'http';
  
  if (currentPlatform === 'win32') {
    // Windows系统只能使用HTTP
    ipcMode = 'http';
  } else {
    // 非Windows系统优先使用UDS
    ipcMode = 'uds';
  }
  
  backendIpcMode = ipcMode;
  
  let envVars: Record<string, string> = {};
  
  if (ipcMode === 'uds') {
    // UDS模式
    const udsPath = '/tmp/zsim_api.sock';
    backendUdsPath = udsPath;
    envVars = { ...process.env, ZSIM_IPC_MODE: 'uds', ZSIM_UDS_PATH: udsPath };
    console.log(`[Backend] Using UDS mode with path: ${udsPath}`);
  } else {
    // HTTP模式
    const availablePort = await findAvailablePort();
    backendPort = availablePort;
    envVars = { ...process.env, ZSIM_API_PORT: availablePort.toString(), ZSIM_IPC_MODE: 'http' };
    console.log(`[Backend] Using HTTP mode with port: ${availablePort}`);
  }
  
  // 找到合适的Python命令
  const pythonCommand = findPythonExecutable();
  let backendCommand: string;
  let backendArgs: string[];
  
  if (process.env.NODE_ENV === 'development' && pythonCommand.startsWith('uv run')) {
    // 开发环境：拆分 uv run python 命令
    backendCommand = 'uv';
    backendArgs = ['run', 'python', backendScript];
  } else {
    // 生产环境：直接使用 python 命令
    backendCommand = pythonCommand;
    backendArgs = [backendScript];
  }
    
  console.log(`[Backend] Starting with: ${backendCommand} ${backendArgs.join(' ')}`);
  
  // 设置正确的工作目录为项目根目录
  const cwd = process.env.NODE_ENV === 'development' 
    ? path.join(__dirname, '..', '..') 
    : path.join(__dirname, '..');
  
  console.log(`[Backend] Working directory: ${cwd}`);
  
  backendProcess = spawn(backendCommand, backendArgs, {
    env: { ...envVars, ...process.env } as typeof process.env,
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd,
  });

  backendProcess?.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess?.stderr?.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess?.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess?.on('error', (err) => {
    console.error('[Backend] Failed to start:', err);
  });

  // 等待后端启动完成
  return new Promise<void>((resolve) => {
    setTimeout(() => {
      if (ipcMode === 'uds') {
        console.log(`[Backend] Server started with UDS: ${backendUdsPath}`);
      } else {
        console.log(`[Backend] Server started on port ${backendPort}`);
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
  win = new BrowserWindow({
    width: 900,
    height: 670,
    minWidth: 900,
    minHeight: 670,
    show: false,
    icon: path.join(process.env.VITE_PUBLIC, 'electron-vite.svg'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.mjs'),
      sandbox: false,
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
    console.log('[Main] Handling get-ipc-config request');
    console.log('[Main] Backend process exists:', !!backendProcess);
    console.log('[Main] IPC mode:', backendIpcMode);
    console.log('[Main] Port:', backendPort);
    console.log('[Main] UDS path:', backendUdsPath);
    
    if (!backendProcess) {
      throw new Error('Backend server not running');
    }
    
    // 返回IPC配置
    return {
      mode: backendIpcMode,
      port: backendPort,
      udsPath: backendUdsPath
    };
  });

  // 处理UDS请求
  ipcMain.handle('make-uds-request', async (_, requestConfig) => {
    const { method, path, headers, body, query, udsPath } = requestConfig;
    
    console.log(`[Main] Making UDS request to: ${udsPath}${path}`);
    console.log(`[Main] Request method: ${method}`);
    console.log(`[Main] Request path: ${path}`);
    console.log(`[Main] Request headers:`, headers);
    console.log(`[Main] Request body:`, body);
    console.log(`[Main] Request query:`, query);
    
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
        headers: headers || {}
      };
      
      const req = http.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
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
          
          console.log(`[Main] UDS response received: ${res.statusCode} ${res.statusCode && res.statusCode < 400 ? 'OK' : 'ERROR'}`);
          
          resolve({
            status: res.statusCode || 500,
            headers: outHeaders,
            body: data
          });
        });
      });
      
      req.on('error', (error) => {
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
    console.log(`[Main] Backend server started successfully`);
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
