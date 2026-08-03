/**
 * Custom Modal & Toast Library
 * Replaces native alert, confirm, and prompt
 */

class CustomModal {
    constructor() {
        this.overlay = null;
        this.modal = null;
        this.currentInstance = null;
        this.titleSequence = 0;
        this.init();
    }

    init() {
        // Create Toast Container if it doesn't exist
        if (!document.querySelector('.custom-toast-container')) {
            const toastContainer = document.createElement('div');
            toastContainer.className = 'custom-toast-container';
            toastContainer.setAttribute('aria-live', 'polite');
            toastContainer.setAttribute('aria-atomic', 'true');
            document.body.appendChild(toastContainer);
        }
    }

    getFocusableElements(container) {
        const selector = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled]):not([type="hidden"])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])'
        ].join(',');
        return Array.from(container.querySelectorAll(selector)).filter(element => (
            !element.hidden && element.getAttribute('aria-hidden') !== 'true'
        ));
    }

    finalizeInstance(instance, result, restoreFocus = true) {
        if (!instance || instance.settled) return;
        instance.settled = true;
        window.clearTimeout(instance.openTimer);
        window.clearTimeout(instance.closeTimer);
        instance.overlay.remove();

        if (this.currentInstance === instance) {
            this.currentInstance = null;
            this.overlay = null;
            this.modal = null;
        }

        instance.resolve(result);
        if (restoreFocus && !this.currentInstance && instance.returnFocus?.isConnected) {
            instance.returnFocus.focus();
        }
    }

    createOverlay(message, title, type = 'info', showCancel = false, inputValue = null, contentBuilder = null, resolve) {
        const previousInstance = this.currentInstance;
        const returnFocus = previousInstance?.returnFocus || document.activeElement;
        if (previousInstance) {
            const previousResult = previousInstance.closing ? previousInstance.result : null;
            this.finalizeInstance(previousInstance, previousResult, false);
        }

        const overlay = document.createElement('div');
        overlay.className = 'custom-modal-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');

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

        const modal = document.createElement('div');
        modal.className = 'custom-modal';
        modal.tabIndex = -1;

        const header = document.createElement('div');
        header.className = 'custom-modal-header';
        const titleElement = document.createElement('h3');
        titleElement.className = 'custom-modal-title';
        titleElement.id = `custom-modal-title-${++this.titleSequence}`;
        overlay.setAttribute('aria-labelledby', titleElement.id);
        const iconElement = document.createElement('span');
        iconElement.className = 'custom-modal-icon';
        iconElement.textContent = icon;
        titleElement.append(iconElement, document.createTextNode(String(title ?? '')));
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'custom-modal-close-btn';
        closeButton.setAttribute('aria-label', cancelText);
        closeButton.textContent = '×';
        header.append(titleElement, closeButton);

        const body = document.createElement('div');
        body.className = 'custom-modal-body';
        const messageElement = document.createElement('div');
        messageElement.className = 'custom-modal-message';
        if (contentBuilder) {
            contentBuilder(messageElement);
        } else {
            messageElement.textContent = String(message ?? '');
        }
        body.appendChild(messageElement);

        let input = null;
        if (isPrompt) {
            input = document.createElement('input');
            input.type = 'text';
            input.className = 'custom-modal-input';
            input.value = inputValue === 'undefined' ? '' : String(inputValue);
            body.appendChild(input);
        }

        const footer = document.createElement('div');
        footer.className = 'custom-modal-footer';
        let cancelButton = null;
        if (showCancel) {
            cancelButton = document.createElement('button');
            cancelButton.type = 'button';
            cancelButton.className = 'custom-modal-btn custom-modal-btn-cancel';
            cancelButton.textContent = cancelText;
            footer.appendChild(cancelButton);
        }
        const okButton = document.createElement('button');
        okButton.type = 'button';
        okButton.className = `custom-modal-btn ${btnClass} btn-ok`;
        okButton.textContent = btnText;
        footer.appendChild(okButton);
        modal.append(header, body, footer);
        overlay.appendChild(modal);

        document.body.appendChild(overlay);
        const instance = {
            overlay,
            modal,
            resolve,
            returnFocus,
            openTimer: null,
            closeTimer: null,
            closing: false,
            result: null,
            settled: false
        };
        this.currentInstance = instance;
        this.overlay = overlay;
        this.modal = modal;

        // Use setTimeout to allow DOM to paint before adding active class for animation
        instance.openTimer = window.setTimeout(() => {
            if (instance.settled || this.currentInstance !== instance) return;
            overlay.classList.add('active');
            if (isPrompt) {
                if (input) {
                    input.focus();
                    input.select(); // Select all text if default value exists

                    // Allow Enter key to submit
                    input.addEventListener('keyup', (e) => {
                        if (e.key === 'Enter') {
                            this.closeInstance(instance, input.value);
                        }
                    });
                }
            } else {
                okButton.focus();
            }
        }, 10);

        // Bind events
        closeButton.addEventListener('click', () => this.closeInstance(instance, null));

        if (cancelButton) {
            cancelButton.addEventListener('click', () => this.closeInstance(instance, null)); // Cancel returns null/false
        }

        okButton.addEventListener('click', () => {
            if (isPrompt) {
                this.closeInstance(instance, input.value);
            } else {
                this.closeInstance(instance, true);
            }
        });

        // Click outside to close (optional, maybe not for critical confirms)
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                // Shake effect or just ignore? Let's just ignore for now to prevent accidental closing
                // Or we can close if it's just an alert
                if (!showCancel && !isPrompt) {
                    this.closeInstance(instance, true);
                }
            }
        });

        overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                e.stopPropagation();
                this.closeInstance(instance, null);
                return;
            }

            if (e.key === 'Tab') {
                const focusable = this.getFocusableElements(modal);
                if (focusable.length === 0) {
                    e.preventDefault();
                    modal.focus();
                    return;
                }

                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                const activeElement = document.activeElement;
                if (e.shiftKey && (activeElement === first || !modal.contains(activeElement))) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && (activeElement === last || !modal.contains(activeElement))) {
                    e.preventDefault();
                    first.focus();
                }
            }
        });
    }

    closeInstance(instance, result) {
        if (!instance || instance.settled || instance.closing) return;
        instance.closing = true;
        instance.result = result;
        instance.overlay.classList.remove('active');
        instance.overlay.classList.add('closing');
        instance.closeTimer = window.setTimeout(() => {
            this.finalizeInstance(instance, result, true);
        }, 300);
    }

    close(result) {
        this.closeInstance(this.currentInstance, result);
    }

    // --- Public API ---

    alert(title, message, type = 'info') {
        return new Promise((resolve) => {
            this.createOverlay(message, title, type, false, null, null, resolve);
        });
    }

    confirm(title, message, type = 'warning') {
        return new Promise((resolve) => {
            this.createOverlay(message, title, type, true, null, null, resolve);
        });
    }

    prompt(title, message, defaultValue = '', type = 'info') {
        return new Promise((resolve) => {
            this.createOverlay(message, title, type, true, defaultValue, null, resolve);
        });
    }

    generatedKeys(title, warning, keys, copyLabel, copiedMessage, copyFailedMessage = 'Copy failed') {
        return new Promise((resolve) => {
            this.createOverlay('', title, 'success', false, null, container => {
                const warningElement = document.createElement('p');
                warningElement.className = 'generated-keys-warning';
                warningElement.textContent = String(warning ?? '');
                container.appendChild(warningElement);

                const list = document.createElement('div');
                list.className = 'generated-keys-list';
                for (const key of keys) {
                    const item = document.createElement('div');
                    item.className = 'generated-key-item';
                    const code = document.createElement('code');
                    code.textContent = String(key);
                    const copyButton = document.createElement('button');
                    copyButton.type = 'button';
                    copyButton.className = 'generated-key-copy';
                    copyButton.textContent = String(copyLabel ?? 'Copy');
                    copyButton.addEventListener('click', () => {
                        navigator.clipboard.writeText(String(key)).then(() => {
                            this.toast(copiedMessage, 'success');
                        }).catch(() => {
                            this.toast(copyFailedMessage, 'error');
                        });
                    });
                    item.append(code, copyButton);
                    list.appendChild(item);
                }
                container.appendChild(list);
            }, resolve);
        });
    }

    toast(message, type = 'info') { // success, error, warning, info
        const container = document.querySelector('.custom-toast-container');
        const toast = document.createElement('div');
        toast.className = `custom-toast ${type}`;
        toast.setAttribute('role', 'status');

        let icon = 'ℹ️';
        if (type === 'success') icon = '✅';
        if (type === 'error') icon = '❌';
        if (type === 'warning') icon = '⚠️';

        const iconElement = document.createElement('span');
        iconElement.className = 'custom-toast-icon';
        iconElement.textContent = icon;
        const messageElement = document.createElement('span');
        messageElement.className = 'custom-toast-message';
        messageElement.textContent = String(message ?? '');
        toast.append(iconElement, messageElement);

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
