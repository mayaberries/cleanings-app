import {atom, computed} from "nanostores";
import type {SessionUser} from "../lib/auth";
import {tabsForRole} from "../lib/nav";
import type {Tab} from "../lib/nav";

/**
 * Client-side mirror of the signed-in user.
 *
 * !! NEVER `.set()` ANY STORE IN THIS FILE FROM SERVER CODE !!
 *
 * Nanostores atoms are module-level singletons. Under `output: 'server'` the
 * module is instantiated once per Node process and shared by every concurrent
 * request, so a `.set()` in `.astro` frontmatter or in middleware would let one
 * visitor's session data render into another visitor's page. Writes are
 * confined to `hydrateCurrentUser`, which is only ever called from a Vue
 * `onMounted` -- a lifecycle hook that does not run during SSR.
 *
 * The server's copy of these stores therefore stays permanently null, which is
 * exactly what we want. SSR gets the user through component props instead
 * (`Astro.locals.user` -> `<AdminNav user={...}>`); the store only takes over
 * once hydration has happened in the browser.
 */
export const $currentUser = atom<SessionUser | null>(null);

/** id of the tab currently being viewed (see lib/nav.ts), or null off-tab. */
export const $activeTab = atom<string | null>(null);

export const $visibleTabs = computed($currentUser, (user): Tab[] =>
    user ? tabsForRole(user) : []
);

export const $isSuperadmin = computed($currentUser, (user) => user?.isSuperuser ?? false);

/**
 * Seed the client stores from the server-rendered props. Browser-only -- see
 * the warning above before calling this from anywhere new.
 */
export function hydrateCurrentUser(user: SessionUser, activeTab: string | null): void {
    $currentUser.set(user);
    $activeTab.set(activeTab);
}
