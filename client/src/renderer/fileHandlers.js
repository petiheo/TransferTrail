import { showNotification } from './notifications.js';
import { updateFileList } from './uiHandlers.js';
import { formatDuration } from './formatDuration.js';

const currentUnfinishedDownloads = {};
const currentUnfinishedUploads = {};

const handleFileUpload = async (filePath) => {
  const fileName = filePath.replace(/^.*[\\/]/, '');
  currentUnfinishedUploads[fileName] = { progress: 0 };
  updateUnfinishedUploads();

  try {
      const uploadResult = await window.electron.invoke('upload-file', filePath);
      const durationUpload = formatDuration(uploadResult.duration);

      if (uploadResult.success) {
          showNotification('Upload successful', `File uploaded successfully: ${uploadResult.fileName}`, durationUpload);
      } else {
          showNotification('Upload failed', uploadResult.message, durationUpload, 'error');
      }
  } catch (error) {
      console.error('Upload error:', error);
      showNotification('Upload failed', `Error: ${error.message}`, '', 'error');
  } finally {
      delete currentUnfinishedUploads[fileName];
      updateUnfinishedUploads();
  }
};

export const handleUpload = async () => {
  try {
      const result = await window.electron.invoke('show-open-dialog');
      
      if (!result.success) {
          showNotification('Upload cancelled', 'No files were selected', '', 'error');
          return;
      }

      await Promise.all(result.filePaths.map(handleFileUpload));
      await updateFileList();
  } catch (error) {
      console.error('Error in handleUpload:', error);
      showNotification('Upload error', `An unexpected error occurred: ${error.message}`, '', 'error');
  }
};

export const setupDragAndDrop = (dragDropArea) => {
    const preventDefault = (event) => {
        event.preventDefault();
        event.stopPropagation();
    };

    dragDropArea.addEventListener('dragover', (event) => {
        preventDefault(event);
        dragDropArea.classList.add('drag-over');
    });

    dragDropArea.addEventListener('dragleave', (event) => {
        preventDefault(event);
        dragDropArea.classList.remove('drag-over');
    });

    dragDropArea.addEventListener('drop', async (event) => {
        preventDefault(event);
        dragDropArea.classList.remove('drag-over');

        const files = event.dataTransfer.files;
        await Promise.all(Array.from(files).map(file => handleFileUpload(file.path)));
        await updateFileList();
    });
};

const createDownloadItem = (file, isFinished = true) => {
    const item = document.createElement('div');
    item.className = 'download-item';
    item.innerHTML = `
        <span class="file-name">${file.name}</span>
        <div class="progress-container">
            <div class="progress-bar">
                <div class="progress" style="width: ${isFinished ? '100' : '0'}%;"></div>
            </div>
            <span class="status">${isFinished ? 'Complete' : '0%'}</span>
        </div>
    `;
    return item;
};

const updateUnfinishedDownloads = () => {
    const container = document.getElementById('unfinished-download-list');
    container.innerHTML = '<h2>Unfinished Downloads</h2>';

    Object.entries(currentUnfinishedDownloads).forEach(([uniqueId, { progress, savedName }]) => {
        const item = createDownloadItem({ name: savedName || uniqueId.split('-')[0] }, false);
        const progressBar = item.querySelector('.progress');
        const status = item.querySelector('.status');
        progressBar.style.width = `${progress}%`;
        status.textContent = `${progress}%`;
        container.appendChild(item);
    });
};

const updateUnfinishedUploads = () => {
    const container = document.getElementById('unfinished-upload-list');
    container.innerHTML = '<h2>Unfinished Uploads</h2>';

    Object.entries(currentUnfinishedUploads).forEach(([fileName, { progress }]) => {
        const item = createDownloadItem({ name: fileName }, false);
        const progressBar = item.querySelector('.progress');
        const status = item.querySelector('.status');
        progressBar.style.width = `${progress}%`;
        status.textContent = `${progress}%`;
        container.appendChild(item);
    });
};

export const handleDownload = async (event) => {
    const fileName = event.target.getAttribute('data-file');
    const uniqueId = `${fileName}-${Date.now()}`;
    currentUnfinishedDownloads[uniqueId] = { progress: 0, savedName: fileName };
    updateUnfinishedDownloads();

    try {
        const result = await window.electron.invoke('download-file', { fileName, uniqueId });
        const durationDownload = formatDuration(result.duration);
        
        if (result.success) {
            showNotification('Download successful', `File ${fileName} downloaded successfully`, durationDownload);
        } else {
            showNotification('Download failed', result.message, durationDownload, 'error');
        }
    } catch (error) {
        console.error('Download error:', error);
        showNotification('Download failed', `Error: ${error.message}`, '', 'error');
    } finally {
        delete currentUnfinishedDownloads[uniqueId];
        updateUnfinishedDownloads();
    }
};

window.electron.receive('upload-progress', ({ fileName, progress }) => {
    if (currentUnfinishedUploads[fileName]) {
        currentUnfinishedUploads[fileName].progress = progress;
    } else {
        currentUnfinishedUploads[fileName] = { progress };
    }
    updateUnfinishedUploads();
});

window.electron.receive('download-progress', ({ uniqueId, fileName, progress, savedName }) => {
    if (currentUnfinishedDownloads[uniqueId]) {
        currentUnfinishedDownloads[uniqueId] = { progress, savedName };
        updateUnfinishedDownloads();
    }
});

export const initializeCategoryButtons = () => {
    const categoryButtons = document.querySelectorAll('.sidebar button');
    const downloadsSection = document.querySelector('.downloads-section');
    const unfinishedList = document.querySelector('.unfinished-list');
    const fileTable = document.getElementById('file-table');
    const downloadsTitle = document.getElementById('downloads-title');

    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            const category = button.getAttribute('data-category');
            
            if (category === 'unfinished') {
                downloadsTitle.textContent = '';
                fileTable.style.display = 'none';
                unfinishedList.style.display = 'block';
                updateUnfinishedDownloads();
                updateUnfinishedUploads();
            } else {
                downloadsTitle.textContent = 'Downloads';
                fileTable.style.display = 'table';
                unfinishedList.style.display = 'none';
                updateFileList(category);
            }
        });
    });
};