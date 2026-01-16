import { defineConfig } from "vitest/config";

import { alias } from "./src/ui/alias.config";

export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      reporter: ["text", "html"]
    },
    alias
  }
});
