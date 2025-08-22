# examples/run_auth_demo.py
# --- agent_meta ---
# role: example-auth-demo
# owner: @backend
# contract: Демонстрация работы MVP-аутентификации: signup/login/me/logout/orgs
# last_reviewed: 2025-08-22
# interfaces:
#   - CLI: python -m examples.run_auth_demo --base-url http://localhost:8080 --email user@example.com --password secret123
# --- /agent_meta ---

import argparse
import sys
import uuid

import httpx


def demo(base_url: str, email: str | None, password: str) -> int:
    email = email or f"demo+{uuid.uuid4().hex[:6]}@example.com"
    org_name = f"Demo Org {uuid.uuid4().hex[:4]}"

    print(f"Base URL: {base_url}")
    print(f"Email: {email}")
    print("---")

    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # 1) Signup (try)
        print("[1] Signup...")
        r = client.post("/auth/signup", json={"email": email, "password": password, "org_name": org_name})
        if r.status_code == 200:
            print("Signup OK:", r.json())
        elif r.status_code == 409:
            print("User exists, will login...")
        else:
            print("Signup failed:", r.status_code, r.text)
            return 1

        # 2) Login if needed
        if r.status_code == 409:
            r2 = client.post("/auth/login", json={"email": email, "password": password})
            if r2.status_code != 200:
                print("Login failed:", r2.status_code, r2.text)
                return 1
            print("Login OK")

        # 3) /me
        print("[2] GET /me ...")
        r = client.get("/me")
        print(r.status_code, r.json())

        # 4) Create org
        print("[3] POST /orgs ...")
        r = client.post("/orgs", params={"name": f"{org_name} Extra"})
        print(r.status_code, r.json())

        # 5) Logout
        print("[4] Logout ...")
        r = client.post("/auth/logout")
        print(r.status_code, r.json())

        # 6) /me after logout
        print("[5] GET /me after logout...")
        r = client.get("/me")
        print(r.status_code, r.text)

    print("Done")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Auth MVP demo")
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default="secret123")
    args = parser.parse_args(argv)
    return demo(args.base_url, args.email, args.password)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

