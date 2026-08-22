import type {SessionUser} from "./auth";

/**
 * The admin dashboard's tab registry -- ported from `docs/proto/shared.js`'s
 * `PAGES` map.
 *
 * `role` does double duty, exactly as it did in the prototype: it decides who
 * sees a tab in the nav (see `tabsForRole`, used by AdminNav.vue) *and* who is
 * allowed to land on its URL directly (see `canAccess`, used by middleware.ts).
 * Keeping both readings in one table is the point -- a tab that's hidden from
 * the nav but reachable by typing the URL is the bug this guards against.
 *
 * This module is imported by both the server (middleware) and the client
 * (the Vue island), so it must stay pure data + pure functions. No state.
 */

export type TabRole = "superadmin" | "clinic_admin" | "both";

export interface Tab {
    id: string;
    label: string;
    href: string;
    role: TabRole;
}

export const TABS: Tab[] = [
    {id: "clinics", label: "Clinics", href: "/clinics", role: "superadmin"},
    {id: "overview", label: "Overview", href: "/overview", role: "clinic_admin"},
    {id: "appointments", label: "Appointments", href: "/appointments", role: "clinic_admin"},
    {id: "services", label: "Services", href: "/services", role: "clinic_admin"},
    {id: "keys", label: "API Keys", href: "/api-keys", role: "clinic_admin"},
    {id: "website", label: "Website", href: "/website", role: "clinic_admin"},
    {id: "account", label: "Account", href: "/account", role: "both"},
];

export function roleOf(user: SessionUser): Exclude<TabRole, "both"> {
    return user.isSuperuser ? "superadmin" : "clinic_admin";
}

export function tabsForRole(user: SessionUser): Tab[] {
    return TABS.filter((tab) => canAccess(user, tab));
}

export function canAccess(user: SessionUser, tab: Tab): boolean {
    return tab.role === "both" || tab.role === roleOf(user);
}

/** Where a freshly signed-in user belongs -- `firstPageFor()` in the prototype. */
export function landingPathFor(user: SessionUser): string {
    return roleOf(user) === "superadmin" ? "/clinics" : "/overview";
}

/**
 * The tab that owns a URL, or null if the path isn't a tab at all (`/login`,
 * `/onboarding`, a 404). Prefix-matches so future nested routes -- the
 * `/settings/clinic`, `/settings/hours` pages sketched in tests/wip -- resolve
 * to their parent tab once that tab exists.
 */
export function tabForPath(pathname: string): Tab | null {
    return TABS.find((tab) => pathname === tab.href || pathname.startsWith(tab.href + "/")) ?? null;
}
