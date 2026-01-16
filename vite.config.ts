import react from "@vitejs/plugin-react";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { defineConfig, loadEnv } from "vite";

import { alias } from "./src/ui/alias.config";

const isDev = "VSCODE_PROXY_URI" in process.env;

// VS Code dev container proxy path override
//
// When running in VS Code dev containers with port forwarding, Vite's default
// behavior sets a base path that conflicts with the proxy setup.
//
// This is fixed via patch-package (see patches/vite+4.5.14.patch), which:
// - Disables the base path override in resolveServerUrls
// - Sets hmrBase to empty string for correct HMR websocket paths
//
// The patch is applied automatically on `npm install` via the postinstall script.
//
// Supported Vite version: 4.x (current: 4.5.14)
// If upgrading Vite, regenerate the patch:
// 1. Run `npm install` to get clean vite
// 2. Apply the manual fixes to node_modules/vite/dist/node/chunks/*.js
// 3. Run `npx patch-package vite` to regenerate the patch
// 4. Test in VS Code dev container environment

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
    // Default must match DEFAULT_API_PORT in src/api/main.py
    return 8080;
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
            alias
        }
    };
});