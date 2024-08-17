import { handleUpload, setupDragAndDrop, initializeCategoryButtons } from './fileHandlers.js';
import { updateFileList } from './uiHandlers.js';

const initializeApp = async () => {
    const uploadButton = document.getElementById('upload-button');
    const dragDropArea = document.getElementById('drag-drop-area');
    const categoryButtons = document.querySelectorAll('.category-button');
    const mainContent = document.querySelector('.main-content');

    uploadButton.addEventListener('click', handleUpload);
    setupDragAndDrop(dragDropArea);

    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            categoryButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            mainContent.style.animation = 'none';
            mainContent.offsetHeight; // Trigger reflow
            mainContent.style.animation = null;

            console.log(`Category selected: ${button.getAttribute('data-category')}`);
        });
    });

    initializeCategoryButtons();
    await updateFileList();
};

document.addEventListener('DOMContentLoaded', initializeApp);