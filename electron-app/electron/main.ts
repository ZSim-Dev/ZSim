import { app, BrowserWindow, shell, ipcMain } from 'electron';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { electronApp, optimizer } from '@electron-toolkit/utils';
import { spawn, ChildProcess } from 'node:child_process';
import net from 'node:net';

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
  
  // 查找可用端口
  const availablePort = await findAvailablePort();
  console.log(`[Backend] Found available port: ${availablePort}`);
  
  // 设置环境变量
  const env = { ...process.env, ZSIM_API_PORT: availablePort.toString() };
  
  // 始终使用 python 运行 api.py
  const backendCommand = 'python';
  const backendArgs = [backendScript];
    
  console.log(`[Backend] Starting with: ${backendCommand} ${backendArgs.join(' ')}`);
  
  // 设置正确的工作目录为项目根目录
  const cwd = process.env.NODE_ENV === 'development' 
    ? path.join(__dirname, '..', '..') 
    : path.join(__dirname, '..');
  
  console.log(`[Backend] Working directory: ${cwd}`);
  
  backendProcess = spawn(backendCommand, backendArgs, {
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
    cwd,
  });

  backendProcess.stdout?.on('data', (data) => {
    console.log(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    console.error(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
    backendProcess = null;
  });

  backendProcess.on('error', (err) => {
    console.error('[Backend] Failed to start:', err);
  });

  // 等待后端启动完成，并返回端口信息
  return new Promise<number>((resolve) => {
    setTimeout(() => {
      console.log(`[Backend] Server started on port ${availablePort}`);
      resolve(availablePort);
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
    
    // 从环境变量获取端口
    const port = parseInt(process.env.ZSIM_API_PORT || '8000');
    return port;
  });

  // 启动后端服务器
  try {
    const port = await startBackendServer();
    console.log(`[Main] Backend server started successfully on port ${port}`);
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
