// ISL Connect - Main JS Utilities
// Each page also has its own inline JS for specific features

console.log("🤟 ISL Connect loaded successfully!");

// Utility: Show a temporary toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 30px; right: 30px;
        background: #1a2235; border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px; padding: 14px 20px;
        color: #e8edf5; font-family: Sora, sans-serif; font-size: 0.85rem;
        z-index: 9999; animation: slideUp 0.3s ease;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}