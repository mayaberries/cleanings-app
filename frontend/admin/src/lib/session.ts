export function requireSession<S>(session: S | undefined): S {
    if (session === undefined) {
        throw new Error(
            "No session available -- is a session driver configured for this adapter? See astro.config.mjs."
        );
    }
    return session;
}