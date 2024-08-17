export function showNotification(title, message, duration, type = 'success') {
    const notificationContainer = document.querySelector('.notification-container') || (() => {
        const container = document.createElement('div');
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    })();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-icon">${type === 'success' ? '✅' : '❌'}</div>
        <div class="notification-content">
            <h3>${title}</h3>
            <p>
                ${message}
                <br>
                <b> ${duration} </b>
            </p>
        </div>
        <div class="notification-close"></div>
    `;

    notificationContainer.appendChild(notification);

    const closeButton = notification.querySelector('.notification-close');
    closeButton.addEventListener('click', () => {
        notification.style.animation = 'fadeOut 0.5s forwards';
        setTimeout(() => {
            notification.remove();
        }, 500);
    });

    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.5s forwards';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}