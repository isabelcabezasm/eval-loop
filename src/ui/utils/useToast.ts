import { useEffect, useState } from "react";

import { ToastMessage, toastManager } from "@/utils/toastManager";

export function useToast() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const unsubscribe = toastManager.subscribe(setToasts);
    return unsubscribe;
  }, []);

  return { toasts, removeToast: (id: number) => toastManager.remove(id) };
}
