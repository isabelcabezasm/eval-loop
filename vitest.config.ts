import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text", "html"]
    },
    alias: {
      "@": path.resolve(__dirname, "./src/ui/")
    }
  }
});
