const path = require('path');
const { promisify } = require('util');
const { execFile } = require('child_process');
const { dialog } = require('electron');
const fs = require('fs').promises;

const execFileAsync = promisify(execFile);

async function getFileList(pythonType, pythonPath) {
  try {
    const { stdout } = await execFileAsync(pythonType, [path.join(pythonPath, 'list_files.py')]);
    return JSON.parse(stdout);
  } catch (error) {
    throw new Error(`Failed to get file list: ${error.message}`);
  }
}

async function uploadFile(event, pythonType, pythonPath, filePath) {
  const startTime = Date.now();
  const upload = execFile(pythonType, [path.join(pythonPath, 'upload_file.py'), filePath]);

  let buffer = '';
  upload.stdout.on('data', (data) => {
    buffer += data.toString();
    const parts = buffer.split('\n');
    for (let i = 0; i < parts.length - 1; i++) {
      try {
        const progressData = parseInt(parts[i]);
        const fileName = path.basename(filePath);
        event.sender.send('upload-progress', { fileName, progress: progressData });
      } catch (parseError) {
        console.error('Error parsing progress data:', parseError);
      }
    }
    buffer = parts[parts.length - 1];
  });

  try {
    const result = await new Promise((resolve, reject) => {
      upload.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout: buffer, code });
        } else {
          reject(new Error(`Upload process exited with code ${code}`));
        }
      });
      upload.on('error', reject);
    });

    const duration = Date.now() - startTime;
    return { 
      success: true, 
      message: result.stdout || 'Upload completed successfully', 
      fileName: path.basename(filePath), 
      duration 
    };
  } catch (error) {
    console.error('Upload failed:', error);
    return { 
      success: false, 
      message: `Upload failed: ${error.message}`, 
      fileName: path.basename(filePath),
      duration: Date.now() - startTime
    };
  }
}

async function downloadFile(event, pythonType, pythonPath, fileName, uniqueId) {
  const { canceled, filePath } = await dialog.showSaveDialog({
    defaultPath: fileName,
    filters: [{ name: 'All Files', extensions: ['*'] }]
  });

  if (canceled) {
    return { success: false, message: 'Download cancelled' };
  }

  const startTime = Date.now();
  const download = execFile(pythonType, [path.join(pythonPath, 'download_file.py'), fileName, filePath]);

  let buffer = '';
  download.stdout.on('data', (data) => {
    buffer += data.toString();
    const parts = buffer.split('\n');
    for (let i = 0; i < parts.length - 1; i++) {
      try {
        const progressData = parseInt(parts[i]);
        const savedName = path.basename(filePath);
        event.sender.send('download-progress', { uniqueId, fileName, progress: progressData, savedName });
      } catch (parseError) {
        console.error('Error parsing progress data:', parseError);
      }
    }
    buffer = parts[parts.length - 1];
  });

  try {
    const result = await new Promise((resolve, reject) => {
      download.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout: buffer, code });
        } else {
          reject(new Error(`Download process exited with code ${code}`));
        }
      });
      download.on('error', reject);
    });

    const duration = Date.now() - startTime;
    return { 
      success: true, 
      message: result.stdout || 'Download completed successfully', 
      filePath, 
      duration 
    };
  } catch (error) {
    console.error('Download failed:', error);
    return { 
      success: false, 
      message: `Download failed: ${error.message}`, 
      filePath,
      duration: Date.now() - startTime
    };
  }
}

async function updateServerIp(serverIp) {
  const configPath = path.join(__dirname, '..', '..', 'config.json');
  try {
    const configData = await fs.readFile(configPath, 'utf8');
    const config = JSON.parse(configData);
    config.host = serverIp;
    await fs.writeFile(configPath, JSON.stringify(config, null, 2), 'utf8');
    return { success: true, message: 'Server IP updated successfully' };
  } catch (error) {
    throw new Error(`Failed to update server IP: ${error.message}`);
  }
}

function setupIpcHandlers(ipcMain, pythonType, pythonPath) {
  ipcMain.handle('get-file-list', () => getFileList(pythonType, pythonPath));
  ipcMain.handle('show-open-dialog', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections']
    });
    return canceled ? { success: false, message: 'File selection cancelled' } : { success: true, filePaths };
  });
  ipcMain.handle('upload-file', (event, filePath) => uploadFile(event, pythonType, pythonPath, filePath));
  ipcMain.handle('download-file', (event, { fileName, uniqueId }) => downloadFile(event, pythonType, pythonPath, fileName, uniqueId));
  ipcMain.handle('update-server-ip', (event, serverIp) => updateServerIp(serverIp));
}

module.exports = setupIpcHandlers;