import {defineMiddleware} from "astro:middleware";
import {requireSession} from "./lib/session";
import {canAccess, landingPathFor, tabForPath} from "./lib/nav";
import type {SessionUser} from "./lib/auth";

const PUBLIC_PATHS = new Set(["/login", "/onboarding"]);

export const onRequest = defineMiddleware(async (context, next) => {
    const session = requireSession(context.session);
    const user = (await session.get("user")) as SessionUser | undefined;
    context.locals.user = user ?? null;

    const isPublicPath = PUBLIC_PATHS.has(context.url.pathname);

    if (!user && !isPublicPath) {
        return context.redirect("/login");
    }
    if (user && isPublicPath) {
        // Already signed in -- no reason to show the login form again.
        return context.redirect(landingPathFor(user));
    }

    if (user) {
        // The role gate from docs/proto/shared.js's boot(): a clinic admin who
        // types /clinics gets bounced to their own landing tab rather than
        // rendering a page whose markup assumes isSuperuser, and vice versa.
        // `tabForPath` returns null for non-tab URLs, which fall through to
        // Astro's own 404 handling instead of being redirected.
        //
        // This is a UI guard, not the security boundary -- it keeps the admin
        // app's URLs honest, but the backend still has to enforce
        // is_superuser/role on every endpoint, since nothing stops a signed-in
        // user from calling the API directly.
        const tab = tabForPath(context.url.pathname);
        if (tab && !canAccess(user, tab)) {
            return context.redirect(landingPathFor(user));
        }
    }

    return next();
});
