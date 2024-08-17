import { showNotification } from './notifications.js';
import { updateFileList } from './uiHandlers.js';

document.addEventListener('DOMContentLoaded', () => {
    const serverIpInput = document.getElementById('server-ip');
    const updateButton = document.getElementById('update-ip-button');

    updateButton.addEventListener('click', async () => {
        const serverIp = serverIpInput.value.trim();
        if (serverIp) {
            try {
                const result = await window.electron.invoke('update-server-ip', serverIp);
                if (result.success) {
                    showNotification('Success', 'Server IP updated successfully!', '', 'success');
                    
                    // Update the file list
                    try {
                        await updateFileList();
                    } catch (updateError) {
                        console.error('Error updating file list:', updateError);
                        // The error notification is now handled in updateFileList()
                    }
                } else {
                    showNotification('Error', 'Failed to update server IP: ' + result.message, '', 'error');
                }
            } catch (error) {
                showNotification('Error', 'An unexpected error occurred: ' + error.message, '', 'error');
            }
        } else {
            showNotification('Warning', 'Please enter a valid IP address.', '', 'error');
        }
    });
});