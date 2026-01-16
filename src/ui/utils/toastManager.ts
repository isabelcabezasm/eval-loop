export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastMessage {
  id: number;
  message: string;
  type: ToastType;
  duration?: number;
}

// Toast manager singleton
class ToastManager {
  private listeners: Array<(toasts: ToastMessage[]) => void> = [];
  private toasts: ToastMessage[] = [];
  private nextId = 1;

  subscribe(listener: (toasts: ToastMessage[]) => void) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== listener);
    };
  }

  private notify() {
    this.listeners.forEach((listener) => listener([...this.toasts]));
  }

  show(message: string, type: ToastType, duration?: number) {
    const toast: ToastMessage = {
      id: this.nextId++,
      message,
      type,
      duration
    };
    this.toasts.push(toast);
    this.notify();
  }

  remove(id: number) {
    this.toasts = this.toasts.filter((t) => t.id !== id);
    this.notify();
  }

  error(message: string, duration?: number) {
    this.show(message, "error", duration);
  }

  success(message: string, duration?: number) {
    this.show(message, "success", duration);
  }

  info(message: string, duration?: number) {
    this.show(message, "info", duration);
  }

  warning(message: string, duration?: number) {
    this.show(message, "warning", duration);
  }
}

export const toastManager = new ToastManager();
