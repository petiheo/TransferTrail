import { handleDownload } from './fileHandlers.js';
import { showNotification } from './notifications.js';

const fileCategories = {
    music: ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.alac'],
    videos: ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.vob', '.webm'],
    compressed: ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
    programs: ['.exe', '.msi', '.bat', '.sh', '.deb', '.rpm', '.dmg'],
    images: ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg', '.webp'],
    documents: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.odt', '.ods', '.odp'],
    apks: ['.apk', '.xapk']
};

const getFileCategory = (fileName) => {
    const extension = fileName.slice(fileName.lastIndexOf('.')).toLowerCase();
    return Object.entries(fileCategories).find(([, extensions]) => 
        extensions.includes(extension)
    )?.[0] || 'others';
};

const formatFileSize = (bytes) => {
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    let unitIndex = 0;
    let size = bytes;

    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }

    return `${size.toFixed(size % 1 === 0 ? 0 : 2)} ${units[unitIndex]}`;
};

const createFileRow = (file, formattedSize) => {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${file.name}</td>
        <td>${formattedSize}</td>
        <td>${new Date(file.last_modified).toLocaleString()}</td>
        <td><button class="download-button" data-file="${file.name}">Download</button></td>
    `;
    return row;
};

export const updateFileList = async (category = 'all') => {
    const fileTableBody = document.querySelector('#file-table tbody');
    fileTableBody.innerHTML = '';

    try {
        const fileList = await window.electron.invoke('get-file-list');
        
        if (fileList.length === 0) {
            fileTableBody.innerHTML = '<tr><td colspan="4">No files found on the server.</td></tr>';
            return;
        }

        const filteredFiles = fileList.filter(file => 
            category === 'all' || getFileCategory(file.name) === category
        );

        filteredFiles.forEach(file => {
            const formattedSize = formatFileSize(file.size);
            const row = createFileRow(file, formattedSize);
            fileTableBody.appendChild(row);
        });

        document.querySelectorAll('.download-button').forEach(button => {
            button.addEventListener('click', handleDownload);
        });
    } catch (error) {
        console.error('Error fetching file list:', error);
        fileTableBody.innerHTML = '<tr><td colspan="4">Unable to connect to the server. Please check your connection and try again.</td></tr>';
        showNotification('Error', 'Failed to fetch file list from the server', '', 'error');
    }
};

export const initializeCategoryButtons = () => {
    document.querySelectorAll('.sidebar button').forEach(button => {
        button.addEventListener('click', (event) => {
            const category = event.target.getAttribute('data-category');
            updateFileList(category);
        });
    });
};