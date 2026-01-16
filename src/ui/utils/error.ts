import { toastManager } from "@/utils/toastManager";

export function error(message: string) {
  toastManager.error(message);
}
