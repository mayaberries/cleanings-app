/// <reference types="astro/client" />

interface ImportMetaEnv {
    readonly PUBLIC_CLINIC_ID: string;
    readonly PUBLIC_CLINIC_SLUG: string;
    readonly PUBLIC_CLINIC_NAME: string;
    readonly PUBLIC_CLINIC_KEY: string; // pk_live_... / pk_test_..., safe client-side
    readonly PUBLIC_API_BASE_URL: string;
    readonly PUBLIC_PRIMARY_COLOR?: string;
    readonly PUBLIC_LOGO_URL?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}