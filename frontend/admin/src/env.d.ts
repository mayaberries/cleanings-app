/// <reference types="astro/client" />
import type { SessionUser } from "./lib/auth";

interface ImportMetaEnv {
    readonly BACKEND_API_URL: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}

declare global {
    namespace App {
        interface Locals {
            user: SessionUser | null;
        }
    }
}