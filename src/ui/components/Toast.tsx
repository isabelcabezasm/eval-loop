import "./Toast.css";
import { useEffect } from "react";

import { ToastMessage } from "@/utils/toastManager";

interface ToastProps {
  message: ToastMessage;
  onClose: (id: number) => void;
}

function Toast({ message, onClose }: ToastProps) {
  useEffect(() => {
    const duration = message.duration ?? 5000;
    const timer = setTimeout(() => {
      onClose(message.id);
    }, duration);

    return () => clearTimeout(timer);
  }, [message, onClose]);

  return (
    <div className={`toast ${message.type}`}>
      <div className="toast-message">{message.message}</div>
      <button className="toast-close" onClick={() => onClose(message.id)} aria-label="Close">
        ×
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onClose: (id: number) => void;
}

export function ToastContainer({ toasts, onClose }: ToastContainerProps) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast key={toast.id} message={toast} onClose={onClose} />
      ))}
    </div>
  );
}
