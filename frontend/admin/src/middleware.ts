import {defineMiddleware} from "astro:middleware";
import {requireSession} from "./lib/session";
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
        return context.redirect("/");
    }

    return next();
});