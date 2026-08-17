export interface SessionUser {
    token: string;
    email: string;
    username: string;
    isSuperuser: boolean;
    role: string | null;
    clinicId: string | null;
}