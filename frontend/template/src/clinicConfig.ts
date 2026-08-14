// Single place every page/component reads clinic config from, so nothing
// touches import.meta.env directly and validation lives in one spot.
export interface ClinicConfig {
    clinicId: string;
    slug: string;
    name: string;
    publicKey: string;
    apiBaseUrl: string;
    primaryColor: string;
    logoUrl?: string;
}

function required(name: keyof ImportMetaEnv): string {
    const value = import.meta.env[name];
    if (!value) {
        throw new Error(
            `Missing required env var ${name} — this site was built without full clinic config.`
        );
    }
    return value;
}

export function getClinicConfig(): ClinicConfig {
    return {
        clinicId: required("PUBLIC_CLINIC_ID"),
        slug: required("PUBLIC_CLINIC_SLUG"),
        name: required("PUBLIC_CLINIC_NAME"),
        publicKey: required("PUBLIC_CLINIC_KEY"),
        apiBaseUrl: required("PUBLIC_API_BASE_URL"),
        primaryColor: import.meta.env.PUBLIC_PRIMARY_COLOR || "#2563eb",
        logoUrl: import.meta.env.PUBLIC_LOGO_URL,
    };
}