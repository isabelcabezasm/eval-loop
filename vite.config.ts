// Taken from https://devcloud.ubs.net/ubs/gf/risk/risk-platforms/groupwide-risk-platforms/model-dev-core-platform/risklab-international/AA45436-RISKLAB/risklab-lite/-/blob/main/vite.config.ts?ref_type=heads
import react from "@vitejs/plugin-react";
import { existsSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";
import { defineConfig, loadEnv } from "vite";

const isDev = "VSCODE_PROXY_URI" in process.env;

// VS Code dev container proxy path override workaround
//
// Background: When running in VS Code dev containers with port forwarding, Vite's default
// behavior tries to set a base path that conflicts with the proxy setup. This patching
// disables that behavior to allow the dev server to work correctly.
//
// IMPORTANT: This patch is tightly coupled to Vite's internal structure and file paths.
// The current implementation is tested and working with Vite 4.4.5.
// DO NOT upgrade Vite without verifying this patch still works, as internal file structure
// or variable names may change between versions, breaking the regex patterns below.
//
// Supported Vite version: ^4.4.5 (current: 4.4.5 in package.json)
//
// If upgrading Vite is necessary:
// 1. Test thoroughly in VS Code dev container environment
// 2. Verify the patched file paths and regex patterns still match
// 3. Update this comment with the new supported version range

if (isDev) {
    const VITE_SERVER = path.join(__dirname, "node_modules/vite/dist/node/chunks");
    const VITE_BASE_PATTERN = /const base = (?:config\.)rawBase;/;
    const VITE_HMR_PATTERN = /let hmrBase = devBase;/;
    const files = readdirSync(VITE_SERVER).map((file) => path.join(VITE_SERVER, file));
    let viteUpdated = false;
    files.forEach((file) => {
        const content = readFileSync(file, "utf-8");
        if (VITE_BASE_PATTERN.test(content)) {
            writeFileSync(file, content.replace(VITE_BASE_PATTERN, "return next();"));
            viteUpdated = true;
        }
        if (VITE_HMR_PATTERN.test(content)) {
            writeFileSync(file, content.replace(VITE_HMR_PATTERN, 'let hmrBase = "";'));
            viteUpdated = true;
        }
    });
    if (viteUpdated) {
        console.log("Patched vite sources, please restart frontend");
        process.exit(0);
    }
}

// Read backend port from API config file
function getBackendPort(): number {
    const configFile = path.join(__dirname, '.api-config.json');
    if (existsSync(configFile)) {
        try {
            const config = JSON.parse(readFileSync(configFile, 'utf-8'));
            if (config.port) {
                console.log(`Using backend port ${config.port} from .api-config.json`);
                return config.port;
            }
        } catch {
            console.warn('Failed to read .api-config.json, using default port');
        }
    }
    return 8081; // Default fallback
}

const port = 8007;
const backendPort = getBackendPort();
const devUrl = process.env.VSCODE_PROXY_URI?.replace("{{port}}/", `${port}`);

const hmrConfig = (port: number) => {
    if (!isDev) return false;

    return {
        port,
        clientPort: 443,
        path: new URL(process.env.VSCODE_PROXY_URI!.replace("{{port}}", `${port}`)).pathname
    };
};

export default defineConfig(({ mode }) => {
    // Note that "mode" can either be "dev" or "development". "development" is equivalent to a local development environment
    // (coming from "vite dev"). "dev" refers to the lab/dev environment in AICE.
    const isLocal = mode === "development"

    const env = loadEnv(mode, __dirname);

    const apiBaseUrl = isLocal
        ? (devUrl ? `${devUrl.replace(`${port}`, `${backendPort}`)}/api/` : `http://127.0.0.1:${backendPort}/api/`)
        : env.VITE_API_BASE_URL;

    const assetsBaseUrl = isLocal ? (devUrl || "/") : env.VITE_ASSETS_BASE_URL

    return {
        plugins: [react()],
        clearScreen: false,
        server: {
            host: "127.0.0.1",
            port: port,
            hmr: hmrConfig(8099),
            allowedHosts: true
        },
        define: {
            "import.meta.env.API_BASE_URL": JSON.stringify(apiBaseUrl)
        },
        assetsInclude: ["**/*.png", "**/*.ico", "**/*.svg"],
        optimizeDeps: { force: true, esbuildOptions: { target: "esnext" } },
        cacheDir: `${process.env.HOME}/.cache/vite`,
        base: assetsBaseUrl,
        envPrefix: ["VITE_"],
        resolve: {
            alias: {
                "@": path.resolve(__dirname, "./src/ui/")
            }
        }
    };
});