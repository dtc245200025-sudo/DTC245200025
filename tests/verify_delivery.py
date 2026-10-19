"""Read-only handover: existing deployment, documents, schema and milestones.

Not a clean-install/restore test or a rerun of the functional WebSocket audit.
"""
import ast
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (
    "README.md", "MEMORY.md", "docs/KIEN_TRUC_VA_DU_LIEU.md",
    "docs/KICH_BAN_DEMO.md", "docs/GD8_BAN_GIAO_VA_BAO_CAO.md",
    "docs/memory/REQUIREMENTS.md", "docs/memory/PROGRESS.md", "docs/memory/CHECKLIST.md",
)
MILESTONES = (
    "feat: milestone 1 - LinhChat, PostgreSQL and Nginx",
    "feat: milestone 2 - Prometheus and Grafana monitoring",
    "feat: milestone 3 - Loki and Promtail centralized logging",
)


def run(*args, timeout=180):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Do not expose child output, environment, inspect data or credentials.
        raise RuntimeError("Kiem tra khong dat: " + Path(args[0]).name)
    return result.stdout


def main():
    for name in DOCUMENTS:
        assert (ROOT / name).is_file(), "Thieu tai lieu: " + name
    architecture = (ROOT / DOCUMENTS[2]).read_text(encoding="utf-8")
    model = ast.parse((ROOT / "app/chatapp/models.py").read_text(encoding="utf-8"))
    tables = {
        node.value.value for node in ast.walk(model)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        and any(isinstance(target, ast.Name) and target.id == "__tablename__" for target in node.targets)
    }
    assert len(tables) == 10 and all("`" + name + "`" in architecture for name in tables)
    actual = run("docker", "compose", "exec", "-T", "postgres", "psql", "-U", "postgres",
                 "-d", "chatdb", "-At", "-c",
                 "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
    assert tables == set(actual.splitlines()), "Schema runtime khac models.py"
    print("[OK] README, kien truc, mo hinh 10 bang, demo, checklist va huong dan bao cao")
    print("[OK] PostgreSQL: 10/10 bang khop models.py; khong doc noi dung nguoi dung")

    # Existing checks validate live data and runtime, not just files on disk.
    run("bash", "scripts/check-phase7.sh")
    print("[OK] 11/11 service running; hardening/source/header va bang chung live dung image/config")
    run(sys.executable, "tests/verify_monitoring.py", "--with-logging")
    print("[OK] Prometheus 5/5 UP; Grafana 11/11 panel; CPU/RAM du 11 service")
    run(sys.executable, "tests/verify_logging.py")
    print("[OK] Loki/Promtail ready; 3/3 LogQL co log qua Loki va Grafana")

    # Detect accidental tracked secrets and missing history without printing private paths.
    tracked = run("git", "ls-files").splitlines()
    assert not any(re.match(r"^(\.env$|work/|outputs/)", name) for name in tracked)
    run("git", "check-ignore", ".env", "work/delivery-private-check", "outputs/delivery-private-check")
    print("[OK] .env/work/outputs ngoai Git; khong in secret")
    print("BA MOC COMMIT DA LUU")
    previous = None
    for title in MILESTONES:
        matches = run("git", "log", "--format=%H%x09%s", "--fixed-strings", "--grep=" + title).splitlines()
        matches = [line for line in matches if line.split("\t", 1)[1] == title]
        assert len(matches) == 1, "Thieu/trung moc commit"
        commit = matches[0].split("\t", 1)[0]
        if previous:
            run("git", "merge-base", "--is-ancestor", previous, commit)
        previous = commit
        print(commit[:7] + " " + title)
    print("[INFO] Functional pytest chay rieng: bash scripts/test-unit.sh")
    print("[LIMIT] HTTP chua TLS; cAdvisor/Promtail co ngoai le quyen, Promtail EOL")
    print("GIAI_DOAN_8_LOCAL_OK")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Avoid tracebacks from authenticated API responses in screenshots.
        print("[FAIL] Ban giao chua dat (" + type(error).__name__ + "); can kiem tra lai truoc khi chup.", file=sys.stderr)
        raise SystemExit(1)
