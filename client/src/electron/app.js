const path = require('path');
const os = require('os');
const { app, BrowserWindow, ipcMain } = require('electron');
const setupIpcHandlers = require('./ipcHandlers');

function createWindow(options) {
  const defaultOptions = {
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false,
      nodeIntegration: false
    }
  };

  const windowOptions = { ...defaultOptions, ...options };
  const window = new BrowserWindow(windowOptions);
  return window;
}

function createMainWindow() {
  const mainWindow = createWindow();
  mainWindow.loadFile(path.join(__dirname, '..', 'index.html'));

  const pythonType = os.platform() === 'win32' ? 'python' : 'python3';
  const pythonPath = path.join(__dirname, '..', '..', 'python');

  setupIpcHandlers(ipcMain, pythonType, pythonPath);
}

app.whenReady().then(createMainWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});