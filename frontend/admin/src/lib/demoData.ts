import type { SessionUser } from "./auth";

export const DEMO_CLINIC_ID = "demo-clinic-1";

export function buildDemoUser(): SessionUser {
    return {
        token: "demo-token",
        email: "demo@acmevet.dev",
        username: "demo-clinic-admin",
        isSuperuser: false,
        role: "clinic_admin",
        clinicId: DEMO_CLINIC_ID,
        isDemo: true,
    };
}

export interface DemoService {
    id: string;
    name: string;
    description: string;
    category: string;
    duration_minutes: number;
    price: number;
}

export interface DemoAppointment {
    id: string;
    service_id: string;
    start_time: string; // ISO
    status: "requested" | "confirmed" | "cancelled";
}

export interface DemoApiKey {
    id: string;
    public_key: string;
    label: string | null;
    environment: "live" | "test";
    is_active: boolean;
}

function inHours(h: number): string {
    return new Date(Date.now() + h * 3600_000).toISOString();
}

export function getDemoServices(): DemoService[] {
    return [
        {
            id: "svc-1",
            name: "Wellness Exam",
            description: "Annual checkup and vaccinations.",
            category: "wellness_exam",
            duration_minutes: 30,
            price: 65,
        },
        {
            id: "svc-2",
            name: "Nail Trim",
            description: "Quick nail trim, walk-ins welcome.",
            category: "nail_trim",
            duration_minutes: 15,
            price: 20,
        },
    ];
}

export function getDemoAppointments(): DemoAppointment[] {
    return [
        { id: "appt-1", service_id: "svc-1", start_time: inHours(2), status: "requested" },
        { id: "appt-2", service_id: "svc-1", start_time: inHours(26), status: "confirmed" },
        { id: "appt-3", service_id: "svc-1", start_time: inHours(-30), status: "cancelled" },
        { id: "appt-4", service_id: "svc-2", start_time: inHours(4), status: "requested" },
    ];
}

export function getDemoApiKeys(): DemoApiKey[] {
    return [
        { id: "key-1", public_key: "pk_live_5f8a2c9d1e3b", label: "Website widget", environment: "live", is_active: true },
        { id: "key-2", public_key: "pk_test_a1b2c3d4e5f6", label: "Local testing", environment: "test", is_active: false },
    ];
}