import {ActionError, defineAction} from "astro:actions";
import {z} from "astro:schema";
import {requireSession} from "../lib/session";
import {buildDemoUser} from "../lib/demoData";
import type {SessionUser} from "../lib/auth";

const BACKEND_API_URL = import.meta.env.BACKEND_API_URL || "http://localhost:8000/api";

export const server = {
    login: defineAction({
        accept: "form",
        input: z.object({
            email: z.string().email("Enter a valid email address."),
            password: z.string().min(1, "Password is required."),
        }),
        handler: async ({email, password}, context) => {
            const tokenRes = await fetch(`${BACKEND_API_URL}/users/login/token`, {
                method: "POST",
                headers: {"Content-Type": "application/x-www-form-urlencoded"},
                // Backend expects OAuth2PasswordRequestForm -- "username", not
                // "email", is the field name it reads (see
                // backend/app/api/routes/auth/users.py).
                body: new URLSearchParams({username: email, password}),
            });

            if (!tokenRes.ok) {
                throw new ActionError({
                    code: "UNAUTHORIZED",
                    message: "Incorrect email or password.",
                });
            }

            const {access_token} = (await tokenRes.json()) as { access_token: string };

            const meRes = await fetch(`${BACKEND_API_URL}/users/me/`, {
                headers: {Authorization: `Bearer ${access_token}`},
            });
            if (!meRes.ok) {
                // The backend accepted the login but rejected the token right
                // back -- a server-side problem, not a bad password, so the
                // message shouldn't send someone back to retyping a correct one.
                throw new ActionError({
                    code: "INTERNAL_SERVER_ERROR",
                    message: "Signed in, but couldn't load your profile. Please try again.",
                });
            }
            const me = await meRes.json();

            const sessionUser: SessionUser = {
                token: access_token,
                email: me.email,
                username: me.username,
                isSuperuser: me.is_superuser,
                role: me.role ?? null,
                clinicId: me.clinic_id ?? null,
                isDemo: false,
            };

            requireSession(context.session).set("user", sessionUser);
            return {email: sessionUser.email};
        },
    }),

    logout: defineAction({
        accept: "form",
        handler: async (_input, context) => {
            requireSession(context.session).destroy();
            return {};
        },
    }),

    // Seeds a fake clinic-admin session
    demoLogin: defineAction({
        accept: "form",
        handler: async (_input, context) => {
            requireSession(context.session).set("user", buildDemoUser());
            return {};
        },
    }),
};