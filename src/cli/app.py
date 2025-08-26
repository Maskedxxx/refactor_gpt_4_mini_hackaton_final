# src/cli/app.py
# --- agent_meta ---
# role: cli-app
# owner: @backend
# contract: Реализация CLI для пользовательских сценариев поверх WebApp API
# last_reviewed: 2025-08-25
# interfaces:
#   - main(argv: list[str]) -> int
#   - Команды: status | auth | hh | sessions | features | pdf | scenarios
# --- /agent_meta ---

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path
from typing import Any, Dict, Optional

from .client import ApiClient


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_status(client: ApiClient, args: argparse.Namespace) -> int:
    h = client.get("/healthz")
    r = client.get("/readyz")
    feats = client.get("/features")
    summary = {
        "healthz": h.status_code == 200,
        "readyz": r.status_code == 200,
        "features_count": len((feats.json() or {}).get("features", {})) if feats.status_code == 200 else 0,
    }
    if getattr(args, "json", False):
        _print_json({
            "summary": summary,
            "features": feats.json() if feats.status_code == 200 else None,
        })
    else:
        print(f"Service health: {'OK' if summary['healthz'] else 'FAIL'}")
        print(f"Service ready:  {'OK' if summary['readyz'] else 'FAIL'}")
        if feats.status_code == 200:
            feats_json = feats.json()
            print(f"Features available: {len(feats_json.get('features', {}))}")
            for name, info in feats_json.get("features", {}).items():
                versions = ", ".join(info.get("versions", []))
                print(f" - {name}: versions [{versions}] (default: {info.get('default_version')})")
        else:
            print("Features endpoint not available")
    return 0


# ---------------------- AUTH ----------------------

def cmd_auth_signup(client: ApiClient, args: argparse.Namespace) -> int:
    body = {"email": args.email, "password": args.password, "org_name": args.org_name}
    resp = client.post_json("/auth/signup", json_body=body)
    if resp.status_code == 200:
        print("Signed up and logged in.")
        _print_json(resp.json())
        return 0
    print(f"Signup failed: {resp.status_code}")
    try:
        print(resp.text)
    except Exception:
        pass
    return 1


def cmd_auth_login(client: ApiClient, args: argparse.Namespace) -> int:
    body = {"email": args.email, "password": args.password}
    resp = client.post_json("/auth/login", json_body=body)
    if resp.status_code == 200:
        print("Logged in.")
        return 0
    print(f"Login failed: {resp.status_code}")
    print(resp.text)
    return 1


def cmd_auth_logout(client: ApiClient, _args: argparse.Namespace) -> int:
    resp = client.post_json("/auth/logout", json_body={})
    client.clear_sid()
    if resp.status_code == 200:
        print("Logged out.")
        return 0
    print(f"Logout request failed: {resp.status_code}")
    return 1


def cmd_auth_me(client: ApiClient, _args: argparse.Namespace) -> int:
    resp = client.get("/me")
    if resp.status_code == 200:
        _print_json(resp.json())
        return 0
    print(f"/me failed: {resp.status_code}")
    print(resp.text)
    return 1


# ---------------------- HH ----------------------

def cmd_hh_status(client: ApiClient, _args: argparse.Namespace) -> int:
    resp = client.get("/auth/hh/status")
    if resp.status_code == 200:
        _print_json(resp.json())
        return 0
    print(f"HH status failed: {resp.status_code}")
    print(resp.text)
    return 1


def cmd_hh_connect(client: ApiClient, args: argparse.Namespace) -> int:
    resp = client.get("/auth/hh/connect")
    if resp.status_code != 200:
        print(f"HH connect failed: {resp.status_code}")
        print(resp.text)
        return 1
    data = resp.json()
    auth_url = data.get("auth_url")
    if not auth_url:
        print("No auth_url in response")
        return 1
    print(f"Open this URL to authorize HH: {auth_url}")
    if not args.no_browser and not args.print_url:
        try:
            webbrowser.open(auth_url)
            print("Browser opened. Complete authorization and come back.")
        except Exception:
            print("Failed to open browser. Please open the URL manually.")
    if not args.print_url:
        input("Press Enter after completing HH OAuth...")
    return 0


def cmd_hh_disconnect(client: ApiClient, _args: argparse.Namespace) -> int:
    resp = client.post_json("/auth/hh/disconnect", json_body={})
    if resp.status_code == 200:
        print("HH disconnected.")
        return 0
    print(f"HH disconnect failed: {resp.status_code}")
    print(resp.text)
    return 1


# ---------------------- SESSIONS ----------------------

def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_sessions_init_json(client: ApiClient, args: argparse.Namespace) -> int:
    resume = _load_json(Path(args.resume))
    vacancy = _load_json(Path(args.vacancy))
    body: Dict[str, Any] = {
        "resume": resume,
        "vacancy": vacancy,
        "reuse_by_hash": bool(args.reuse_by_hash),
    }
    if args.ttl is not None:
        body["ttl_sec"] = int(args.ttl)
    resp = client.post_json("/sessions/init_json", json_body=body)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Session created: {data['session_id']}")
        _print_json(data)
        return 0
    if resp.status_code == 401:
        print("Unauthorized: HH authorization required (login + hh connect)")
    print(f"init_json failed: {resp.status_code}")
    print(resp.text)
    return 1


def cmd_sessions_init_upload(client: ApiClient, args: argparse.Namespace) -> int:
    pdf_path = Path(args.resume_pdf)
    if not pdf_path.exists():
        print(f"Resume PDF not found: {pdf_path}")
        return 1
    data: Dict[str, Any] = {
        "vacancy_url": args.vacancy_url,
        "reuse_by_hash": str(bool(args.reuse_by_hash)).lower(),
    }
    if args.ttl is not None:
        data["ttl_sec"] = str(int(args.ttl))
    files = {"resume_file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
    resp = client.post_form("/sessions/init_upload", data=data, files=files, timeout=300.0)
    if resp.status_code == 200:
        data = resp.json()
        print(f"Upload session created: {data['session_id']}")
        _print_json(data)
        return 0
    if resp.status_code == 401:
        print("Unauthorized: HH authorization required (login + hh connect)")
    print(f"init_upload failed: {resp.status_code}")
    print(resp.text)
    return 1


# ---------------------- FEATURES ----------------------

def cmd_features_list(client: ApiClient, _args: argparse.Namespace) -> int:
    resp = client.get("/features")
    if resp.status_code == 200:
        _print_json(resp.json())
        return 0
    print(f"/features failed: {resp.status_code}")
    print(resp.text)
    return 1


def _preview_feature_result(name: str, result: Dict[str, Any]) -> None:
    print("Preview:")
    if name == "cover_letter":
        subject = result.get("subject_line") or result.get("subject")
        content = result.get("content") or result.get("letter_text")
        print(f"  Subject: {subject}")
        if isinstance(content, str):
            print(f"  Length: {len(content)} chars")
    elif name == "gap_analyzer":
        gaps = result.get("skill_gaps", [])
        print(f"  Skill gaps: {len(gaps)}")
    elif name == "interview_checklist":
        questions = result.get("questions", [])
        print(f"  Questions: {len(questions)}")
    elif name == "interview_simulation":
        rounds = result.get("total_rounds_completed", 0)
        print(f"  Rounds: {rounds}")


def cmd_features_run(client: ApiClient, args: argparse.Namespace) -> int:
        
    body: Dict[str, Any] = {}
    if args.session_id:
        body["session_id"] = args.session_id
    else:
        resume = _load_json(Path(args.resume)) if args.resume else None
        vacancy = _load_json(Path(args.vacancy)) if args.vacancy else None
        if not (resume and vacancy):
            print("Provide --session-id or both --resume and --vacancy")
            return 1
        body["resume"] = resume
        body["vacancy"] = vacancy
    if args.options:
        body["options"] = _load_json(Path(args.options))
    params: Dict[str, Any] = {}
    if args.version:
        params["version"] = args.version
    resp = client.post_json(f"/features/{args.name}/generate", json_body=body | ({"version": args.version} if args.version else {}))
    if resp.status_code == 200:
        data = resp.json()
        _preview_feature_result(args.name, data.get("result", {}))
        if args.out:
            Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"Saved result to {args.out}")
        else:
            _print_json(data)
        return 0
    if resp.status_code == 401:
        print("Unauthorized: HH authorization required")
    print(f"Feature run failed: {resp.status_code}")
    print(resp.text)
    return 1


# ---------------------- PDF ----------------------

def cmd_pdf_export(client: ApiClient, args: argparse.Namespace) -> int:
    data = _load_json(Path(args.result))
    # Если файл содержит {"result": ...}, извлекаем только result часть
    actual_result = data.get("result", data) if isinstance(data, dict) and "result" in data else data
    body: Dict[str, Any] = {"result": actual_result}
    if args.metadata:
        body["metadata"] = _load_json(Path(args.metadata))
    resp = client.post_json(f"/features/{args.feature_name}/export/pdf", json_body=body)
    if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/pdf"):
        Path(args.out).write_bytes(resp.content)
        print(f"PDF saved to {args.out}")
        return 0
    print(f"PDF export failed: {resp.status_code}")
    ct = resp.headers.get("content-type")
    if ct and ct.startswith("application/json"):
        print(resp.text)
    return 1


# ---------------------- SCENARIOS ----------------------

def cmd_scenario_test_user_setup(client: ApiClient, _args: argparse.Namespace) -> int:
    # Try login with demo user; else sign up
    email = "demo_user@testapp.com"
    password = "demo123"
    r = client.post_json("/auth/login", json_body={"email": email, "password": password})
    if r.status_code != 200:
        r = client.post_json(
            "/auth/signup",
            json_body={"email": email, "password": password, "org_name": "Demo Test Organization"},
        )
        if r.status_code != 200 and r.status_code != 409:
            print("Failed to create demo user")
            return 1
        if r.status_code == 409:
            # user exists, login
            r = client.post_json("/auth/login", json_body={"email": email, "password": password})
            if r.status_code != 200:
                print("Login failed for existing demo user")
                return 1
    me = client.get("/me")
    if me.status_code == 200:
        print("Demo user profile:")
        _print_json(me.json())
        return 0
    print("Failed to fetch /me")
    return 1


def cmd_scenario_hh_auth_demo(client: ApiClient, args: argparse.Namespace) -> int:
    if cmd_scenario_test_user_setup(client, args) != 0:
        return 1
    st = client.get("/auth/hh/status")
    if st.status_code == 200 and st.json().get("is_connected"):
        print("HH already connected.")
        return 0
    print("Starting HH OAuth...")
    rc = cmd_hh_connect(client, args)
    if rc != 0:
        return rc
    st2 = client.get("/auth/hh/status")
    if st2.status_code == 200 and st2.json().get("is_connected"):
        print("HH connected.")
        return 0
    print("HH connection not completed.")
    return 1


def cmd_scenario_feature_with_hash(client: ApiClient, args: argparse.Namespace) -> int:
    if cmd_scenario_test_user_setup(client, args) != 0:
        return 1
    # First session (store objects)
    resume = _load_json(Path("tests/data/simple_resume.json"))
    vacancy = _load_json(Path("tests/data/simple_vacancy.json"))
    print("Creating initial session with reuse_by_hash=true...")
    r1 = client.post_json("/sessions/init_json", json_body={
        "resume": resume, "vacancy": vacancy, "reuse_by_hash": True
    })
    if r1.status_code != 200:
        if r1.status_code == 401:
            print("Requires HH authorization; run hh-auth-demo first.")
        print("Initial session failed.")
        return 1
    print("Creating second session expecting reuse...")
    r2 = client.post_json("/sessions/init_json", json_body={
        "resume": resume, "vacancy": vacancy, "reuse_by_hash": True
    })
    if r2.status_code != 200:
        print("Second session failed.")
        return 1
    data = r2.json()
    print("Reused flags:")
    _print_json(data.get("reused", {}))
    # Simulate feature run: list features and pick provided
    feature = args.feature
    print(f"Simulating feature preview for {feature} using sample result file...")
    # Load sample result from tests/data
    sample_map = {
        "cover_letter": "tests/data/cover_letter_result_208e5d1f.json",
        "gap_analyzer": "tests/data/gap_analysis_result_8407a6f5.json",
        "interview_checklist": "tests/data/interview_checklist_result_6423ab26.json",
        "interview_simulation": "tests/data/interview_simulation_result_20250820_104305.json",
    }
    sample_path = Path(sample_map.get(feature, ""))
    if not sample_path.exists():
        print(f"Sample result not found for {feature}: {sample_path}")
        return 1
    sample = _load_json(sample_path)
    _preview_feature_result(feature, sample)
    print(f"Loaded sample from {sample_path}")
    return 0


def cmd_scenario_feature_no_hash(client: ApiClient, args: argparse.Namespace) -> int:
    if cmd_scenario_test_user_setup(client, args) != 0:
        return 1
    pdf_path = Path("tests/data/resume.pdf")
    if pdf_path.exists():
        print("Creating upload session with reuse_by_hash=false (force parsing)...")
        files = {"resume_file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
        data = {"vacancy_url": "https://hh.ru/vacancy/12345678", "reuse_by_hash": "false"}
        r = client.post_form("/sessions/init_upload", data=data, files=files, timeout=300.0)
        if r.status_code != 200:
            if r.status_code == 401:
                print("Requires HH authorization; run hh-auth-demo first.")
            print("init_upload failed.")
            return 1
        print("Upload session created:")
        _print_json(r.json())
    else:
        print("Resume PDF not found; falling back to init_json with reuse_by_hash=false")
        resume = _load_json(Path("tests/data/simple_resume.json"))
        vacancy = _load_json(Path("tests/data/simple_vacancy.json"))
        r = client.post_json("/sessions/init_json", json_body={
            "resume": resume, "vacancy": vacancy, "reuse_by_hash": False
        })
        if r.status_code != 200:
            print("init_json fallback failed.")
            return 1
        print("Session created without reuse:")
        _print_json(r.json())

    feature = args.feature
    print(f"Simulating feature preview for {feature} using sample result files...")
    sample_map = {
        "cover_letter": "tests/data/cover_letter_result_208e5d1f.json",
        "gap_analyzer": "tests/data/gap_analysis_result_8407a6f5.json",
        "interview_checklist": "tests/data/interview_checklist_result_6423ab26.json",
        "interview_simulation": "tests/data/interview_simulation_result_20250820_104305.json",
    }
    sample_path = Path(sample_map.get(feature, ""))
    if not sample_path.exists():
        print(f"Sample result not found for {feature}: {sample_path}")
        return 1
    sample = _load_json(sample_path)
    _preview_feature_result(feature, sample)
    print(f"Loaded sample from {sample_path}")
    return 0


def cmd_scenario_full_demo(client: ApiClient, args: argparse.Namespace) -> int:
    if cmd_scenario_test_user_setup(client, args) != 0:
        return 1
    st = client.get("/auth/hh/status")
    if not (st.status_code == 200 and st.json().get("is_connected")):
        print("HH not connected. Run: python -m src.cli hh connect")
        print("Skipping HH-dependent feature demos.")
        return 0
    # Pick first available feature
    fl = client.get("/features")
    feature_name = "cover_letter"
    if fl.status_code == 200:
        feats = fl.json().get("features", {})
        if feats:
            feature_name = next(iter(feats.keys()))
    print(f"Running hash and no-hash scenarios for {feature_name}...")
    args.feature = feature_name
    rc1 = cmd_scenario_feature_with_hash(client, args)
    rc2 = cmd_scenario_feature_no_hash(client, args)
    return 0 if rc1 == 0 and rc2 == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="hh-cli", description="CLI for HH WebApp")
    p.add_argument("--base-url", default="http://localhost:8080")
    p.add_argument("--cookies", default=".hh_cli_cookies.json")
    p.add_argument("--timeout", type=float, default=600.0)
    p.add_argument("--no-browser", action="store_true")

    sp = p.add_subparsers(dest="cmd", required=True)

    # status
    p_status = sp.add_parser("status", help="Check service and features")
    p_status.add_argument("--json", action="store_true")
    p_status.set_defaults(handler=cmd_status)

    # auth
    p_auth = sp.add_parser("auth", help="Auth commands")
    sp_auth = p_auth.add_subparsers(dest="sub", required=True)
    p_signup = sp_auth.add_parser("signup", help="Sign up and login")
    p_signup.add_argument("--email", required=True)
    p_signup.add_argument("--password", required=True)
    p_signup.add_argument("--org-name", required=True)
    p_signup.set_defaults(handler=cmd_auth_signup)

    p_login = sp_auth.add_parser("login", help="Login")
    p_login.add_argument("--email", required=True)
    p_login.add_argument("--password", required=True)
    p_login.set_defaults(handler=cmd_auth_login)

    p_logout = sp_auth.add_parser("logout", help="Logout")
    p_logout.set_defaults(handler=cmd_auth_logout)

    p_me = sp_auth.add_parser("me", help="Current user profile")
    p_me.set_defaults(handler=cmd_auth_me)

    # hh
    p_hh = sp.add_parser("hh", help="HH integration")
    sp_hh = p_hh.add_subparsers(dest="sub", required=True)
    p_hh_status = sp_hh.add_parser("status", help="HH connection status")
    p_hh_status.set_defaults(handler=cmd_hh_status)

    p_hh_connect = sp_hh.add_parser("connect", help="Init HH OAuth")
    p_hh_connect.add_argument("--print-url", action="store_true")
    p_hh_connect.set_defaults(handler=cmd_hh_connect)

    p_hh_disconnect = sp_hh.add_parser("disconnect", help="Disconnect HH")
    p_hh_disconnect.set_defaults(handler=cmd_hh_disconnect)

    # sessions
    p_sessions = sp.add_parser("sessions", help="Manage sessions")
    sp_sess = p_sessions.add_subparsers(dest="sub", required=True)
    p_init_json = sp_sess.add_parser("init-json", help="Init session from JSON")
    p_init_json.add_argument("--resume", required=True)
    p_init_json.add_argument("--vacancy", required=True)
    p_init_json.add_argument("--reuse-by-hash", action="store_true", default=True)
    p_init_json.add_argument("--ttl", type=int)
    p_init_json.set_defaults(handler=cmd_sessions_init_json)

    p_init_upload = sp_sess.add_parser("init-upload", help="Init session from PDF+URL")
    p_init_upload.add_argument("--resume-pdf", required=True)
    p_init_upload.add_argument("--vacancy-url", required=True)
    p_init_upload.add_argument("--reuse-by-hash", action="store_true", default=True)
    p_init_upload.add_argument("--ttl", type=int)
    p_init_upload.set_defaults(handler=cmd_sessions_init_upload)

    # features
    p_features = sp.add_parser("features", help="LLM features")
    sp_feat = p_features.add_subparsers(dest="sub", required=True)
    p_feat_list = sp_feat.add_parser("list", help="List features")
    p_feat_list.set_defaults(handler=cmd_features_list)

    p_feat_run = sp_feat.add_parser("run", help="Run feature")
    p_feat_run.add_argument("--name", required=True, choices=["cover_letter", "gap_analyzer", "interview_checklist", "interview_simulation"])
    p_feat_run.add_argument("--version")
    p_feat_run.add_argument("--session-id")
    p_feat_run.add_argument("--resume")
    p_feat_run.add_argument("--vacancy")
    p_feat_run.add_argument("--options") # Передать имя файла с JSON опциями
    p_feat_run.add_argument("--out")
    p_feat_run.set_defaults(handler=cmd_features_run)

    # pdf
    p_pdf = sp.add_parser("pdf", help="PDF export")
    sp_pdf = p_pdf.add_subparsers(dest="sub", required=True)
    p_pdf_export = sp_pdf.add_parser("export", help="Export feature result to PDF")
    p_pdf_export.add_argument("--feature-name", required=True)
    p_pdf_export.add_argument("--result", required=True)
    p_pdf_export.add_argument("--metadata")
    p_pdf_export.add_argument("--out", required=True)
    p_pdf_export.set_defaults(handler=cmd_pdf_export)

    # scenarios
    p_scen = sp.add_parser("scenarios", help="Predefined scenarios")
    sp_scen = p_scen.add_subparsers(dest="sub", required=True)
    p_scen_user = sp_scen.add_parser("test-user-setup", help="Setup or login demo user")
    p_scen_user.set_defaults(handler=cmd_scenario_test_user_setup)
    p_scen_hh = sp_scen.add_parser("hh-auth-demo", help="Run HH OAuth demo")
    p_scen_hh.add_argument("--print-url", action="store_true")
    p_scen_hh.set_defaults(handler=cmd_scenario_hh_auth_demo)
    p_scen_hash = sp_scen.add_parser("feature-with-hash", help="Run feature with hash reuse scenario")
    p_scen_hash.add_argument("--feature", required=True, choices=["cover_letter", "gap_analyzer", "interview_checklist", "interview_simulation"])
    p_scen_hash.set_defaults(handler=cmd_scenario_feature_with_hash)
    p_scen_nohash = sp_scen.add_parser("feature-no-hash", help="Run feature without hash scenario")
    p_scen_nohash.add_argument("--feature", required=True, choices=["cover_letter", "gap_analyzer", "interview_checklist", "interview_simulation"])
    p_scen_nohash.set_defaults(handler=cmd_scenario_feature_no_hash)
    p_scen_full = sp_scen.add_parser("full-demo", help="Full end-to-end demo")
    p_scen_full.add_argument("--feature", help="Optional explicit feature to use")
    p_scen_full.set_defaults(handler=cmd_scenario_full_demo)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = ApiClient(base_url=args.base_url, cookies_path=Path(args.cookies), timeout=float(args.timeout))
    try:
        handler = getattr(args, "handler", None)
        if handler is None:
            parser.print_help()
            return 2
        return int(handler(client, args))
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

