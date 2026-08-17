"""
Grant (or revoke) platform-operator (is_superuser) status for a user.

Deliberately NOT an HTTP endpoint -- self-service privilege escalation to
a cross-tenant role has no business existing on the wire at all. This
talks to the DB directly and is meant to be run by whoever already has
prod DB access (same trust level as running a migration by hand).

Usage:
    python scripts/promote_superuser.py owner@example.com
    python scripts/promote_superuser.py owner@example.com --revoke
"""
import argparse
import asyncio

from databases import Database

from app.core.config import DATABASE_URL

GET_USER_QUERY = "SELECT id, email, is_superuser FROM users WHERE email = :email;"
SET_SUPERUSER_QUERY = "UPDATE users SET is_superuser = :value WHERE email = :email RETURNING id, email, is_superuser;"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Email of the user to promote/revoke")
    parser.add_argument("--revoke", action="store_true", help="Revoke instead of grant")
    args = parser.parse_args()

    db = Database(str(DATABASE_URL))
    await db.connect()
    try:
        user = await db.fetch_one(query=GET_USER_QUERY, values={"email": args.email})
        if not user:
            print(f"No user found with email {args.email}")
            return

        updated = await db.fetch_one(
            query=SET_SUPERUSER_QUERY,
            values={"email": args.email, "value": not args.revoke},
        )
        action = "revoked from" if args.revoke else "granted to"
        print(f"is_superuser {action} {updated['email']} (id={updated['id']})")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
