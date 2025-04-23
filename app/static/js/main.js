// Main JavaScript file for Discord Bot Panel

// Helper function to show notifications
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 5000);
}

// Helper function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Helper function to handle API errors
function handleApiError(error) {
    console.error('API Error:', error);
    showNotification('An error occurred. Please try again.', 'error');
}

// Check if token exists and redirect to login if not
document.addEventListener('DOMContentLoaded', function() {
    const token = localStorage.getItem('token');
    const isLoginPage = window.location.pathname === '/login';
    
    if (!token && !isLoginPage) {
        window.location.href = '/login';
    }
});
