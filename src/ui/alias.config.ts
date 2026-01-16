import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Shared alias configuration for Vite and Vitest
// Single source of truth to prevent inconsistencies
export const alias = {
  "@": path.resolve(__dirname, "./")
};
