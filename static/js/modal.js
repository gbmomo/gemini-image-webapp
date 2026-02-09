/**
 * Custom Modal & Toast Library
 * Replaces native alert, confirm, and prompt
 */

class CustomModal {
    constructor() {
        this.overlay = null;
        this.modal = null;
        this.resolvePromise = null;
        this.init();
    }

    init() {
        // Create Toast Container if it doesn't exist
        if (!document.querySelector('.custom-toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.className = 'custom-toast-container';
            document.body.appendChild(toastContainer);
        }
    }

    createOverlay(contentHtml, title, type = 'info', showCancel = false, inputValue = null) {
        // Remove existing overlay if any
        if (this.overlay) {
            document.body.removeChild(this.overlay);
        }

        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';

        let icon = '';
        let btnClass = 'custom-modal-btn-confirm';
        // Use I18n if available, fallback to Chinese
        let btnText = typeof I18n !== 'undefined' && I18n.t ? I18n.t('btn_ok') : '确定';
        let cancelText = typeof I18n !== 'undefined' && I18n.t ? I18n.t('btn_cancel') : '取消';

        if (type === 'success') {
            icon = '✅';
        } else if (type === 'error') {
            icon = '❌';
            btnClass = 'custom-modal-btn-danger';
        } else if (type === 'warning') {
            icon = '⚠️';
            btnClass = 'custom-modal-btn-danger';
        } else {
            icon = 'ℹ️';
        }

        const isPrompt = inputValue !== null;

        overlay.innerHTML = `
            <div class="custom-modal">
                <div class="custom-modal-header">
                    <h3 class="custom-modal-title">
                        <span class="custom-modal-icon">${icon}</span>
                        ${title}
                    </h3>
                    <button class="custom-modal-close-btn">&times;</button>
                </div>
                <div class="custom-modal-body">
                    <div class="custom-modal-message">${contentHtml}</div>
                    ${isPrompt ? `<input type="text" class="custom-modal-input" value="${inputValue === 'undefined' ? '' : inputValue}" autofocus>` : ''}
                </div>
                <div class="custom-modal-footer">
                    ${showCancel ? `<button class="custom-modal-btn custom-modal-btn-cancel">${cancelText}</button>` : ''}
                    <button class="custom-modal-btn ${btnClass} btn-ok">${btnText}</button>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        this.overlay = overlay;

        // Use setTimeout to allow DOM to paint before adding active class for animation
        setTimeout(() => {
            overlay.classList.add('active');
            if (isPrompt) {
                const input = overlay.querySelector('input');
                if (input) {
                    input.focus();
                    input.select(); // Select all text if default value exists

                    // Allow Enter key to submit
                    input.addEventListener('keyup', (e) => {
                        if (e.key === 'Enter') {
                            this.close(input.value);
                        }
                    });
                }
            }
        }, 10);

        // Bind events
        const closeBtn = overlay.querySelector('.custom-modal-close-btn');
        const cancelBtn = overlay.querySelector('.custom-modal-btn-cancel');
        const okBtn = overlay.querySelector('.btn-ok');

        closeBtn.addEventListener('click', () => this.close(null));

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close(null)); // Cancel returns null/false
        }

        okBtn.addEventListener('click', () => {
            if (isPrompt) {
                const input = overlay.querySelector('input');
                this.close(input.value);
            } else {
                this.close(true);
            }
        });

        // Click outside to close (optional, maybe not for critical confirms)
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                // Shake effect or just ignore? Let's just ignore for now to prevent accidental closing
                // Or we can close if it's just an alert
                if (!showCancel && !isPrompt) {
                    this.close(true);
                }
            }
        });
    }

    close(result) {
        if (this.overlay) {
            this.overlay.classList.remove('active');
            this.overlay.classList.add('closing');
            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                }
                this.overlay = null;
                if (this.resolvePromise) {
                    this.resolvePromise(result);
                    this.resolvePromise = null;
                }
            }, 300);
        }
    }

    // --- Public API ---

    alert(title, message, type = 'info') {
        return new Promise((resolve) => {
            this.resolvePromise = resolve;
            this.createOverlay(message, title, type, false, null);
        });
    }

    confirm(title, message, type = 'warning') {
        return new Promise((resolve) => {
            this.resolvePromise = resolve; // returns true or null(false)
            this.createOverlay(message, title, type, true, null);
        });
    }

    prompt(title, message, defaultValue = '', type = 'info') {
        return new Promise((resolve) => {
            this.resolvePromise = resolve; // returns string or null
            this.createOverlay(message, title, type, true, defaultValue);
        });
    }

    toast(message, type = 'info') { // success, error, warning, info
        const container = document.querySelector('.custom-toast-container');
        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;

        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';
        if (type === 'warning') icon = '⚠️';

        toast.innerHTML = `
            <span class="custom-toast-icon">${icon}</span>
            <span class="custom-toast-message">${message}</span>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => toast.classList.add('show'), 10);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 300);
        }, 3000);
    }
}

// Global Instance
window.Modal = new CustomModal();
