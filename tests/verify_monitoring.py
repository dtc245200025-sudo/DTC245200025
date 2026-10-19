"""Read-only monitoring checks with stdlib; never print credentials or app data."""
import argparse
import base64
import json
import math
import os
from pathlib import Path
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROM = os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090").rstrip("/")
GRAFANA = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3000").rstrip("/")
JOBS = {"chat-app", "postgres", "nginx", "cadvisor", "prometheus"}
SERVICES = {"app", "nginx", "postgres", "pgadmin", "postgres-exporter", "nginx-exporter", "cadvisor", "prometheus", "grafana"}
CURRENT = 'topk by (service) (1, container_last_seen{job="cadvisor",service!=""} > time() - 60)'


def env_values(path):
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip("\"'")
    return values


def api(base, path, auth=None, payload=None):
    headers = {"Accept": "application/json"}
    if auth:
        headers["Authorization"] = "Basic " + base64.b64encode((auth[0] + ":" + auth[1]).encode()).decode()
    raw = None
    if payload is not None:
        raw = json.dumps(payload).encode(); headers["Content-Type"] = "application/json"
    with urlopen(Request(base + path, data=raw, headers=headers), timeout=20) as response:
        return json.load(response)


def query(expression, at=None):
    args = {"query": expression}
    if at is not None: args["time"] = str(at)
    result = api(PROM, "/api/v1/query?" + urlencode(args))
    assert result["status"] == "success", "Prometheus query failed"
    return result["data"]["result"]


def check_values(expression):
    rows = query(expression)
    assert rows and all(math.isfinite(float(row["value"][1])) for row in rows), "Missing/non-finite metric: " + expression
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=".env")
    parser.add_argument("--save", help="Optional numeric evidence for persistence check")
    parser.add_argument("--persistence", help="Numeric evidence file saved before monitoring restart")
    parser.add_argument("--prepare-access", action="store_true")
    parser.add_argument("--with-logging", action="store_true")
    args = parser.parse_args()
    values = env_values(args.env)
    auth = (values["GRAFANA_ADMIN_USER"], values["GRAFANA_ADMIN_PASSWORD"])
    if args.prepare_access:
        path = Path("work/grafana-access.txt"); path.parent.mkdir(exist_ok=True)
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            output.write("GRAFANA_USER=" + auth[0] + "\nGRAFANA_PASSWORD=" + auth[1] + "\n")
        print("[OK] Ghi thong tin Grafana rieng tai work/grafana-access.txt, quyen600; khong chup mat khau")
    deadline = time.monotonic() + 60
    while True:
        targets = api(PROM, "/api/v1/targets")["data"]["activeTargets"]
        if {target["labels"]["job"] for target in targets} == JOBS and all(target["health"] == "up" and not target["lastError"] for target in targets):
            break
        assert time.monotonic() < deadline, "Scrape targets not ready within 60 seconds"
        time.sleep(3)
    print("[OK] Prometheus 5/5 UP: cadvisor, chat-app, nginx, postgres, prometheus")
    for metric in ("container_memory_working_set_bytes", "container_cpu_usage_seconds_total"):
        rows = check_values(f'sum by (service) ({metric}{{job="cadvisor",service!=""}} and on (id,instance,job) {CURRENT})')
        observed = {row["metric"]["service"] for row in rows}
        assert SERVICES <= observed, "CPU/RAM missing a monitoring service"
        if args.with_logging:
            assert observed == SERVICES | {"loki", "promtail"}, "CPU/RAM missing logging service"
    print(f"[OK] CPU/RAM cua {len(observed)} service, chi project nay; bo container one-off")
    assert float(check_values('pg_up{job="postgres"}')[0]["value"][1]) == 1
    assert float(check_values('nginx_up{job="nginx"}')[0]["value"][1]) == 1
    health = api(GRAFANA, "/api/health"); assert health["database"] == "ok"
    datasource = api(GRAFANA, "/api/datasources/uid/prometheus/health", auth)
    assert datasource["status"].upper() == "OK", "Grafana cannot query Prometheus"
    saved = api(GRAFANA, "/api/dashboards/uid/linhchat-overview", auth)
    dashboard = saved["dashboard"]
    source_path = Path(__file__).resolve().parents[1] / "grafana/dashboards/de32-chat.json"
    expected = json.loads(source_path.read_text(encoding="utf-8"))
    expected_queries = {panel["id"]: panel["targets"][0]["expr"] for panel in expected["panels"]}
    deadline = time.monotonic() + 30
    while {panel["id"]: panel["targets"][0]["expr"] for panel in dashboard["panels"]} != expected_queries:
        assert time.monotonic() < deadline, "Grafana provisioned dashboard differs from source"
        time.sleep(3)
        saved = api(GRAFANA, "/api/dashboards/uid/linhchat-overview", auth); dashboard = saved["dashboard"]
    assert dashboard["title"] == "LinhChat Overview" and saved["meta"]["provisioned"]
    assert dashboard["refresh"] == "15s" and "15s" in dashboard["timepicker"]["refresh_intervals"]
    assert len(dashboard["panels"]) == 11
    for panel in dashboard["panels"]:
        for target in panel["targets"]:
            check_values(target["expr"])
    now = int(time.time() * 1000)
    queries = [{"refId": "panel" + str(panel["id"]), "datasource": {"type": "prometheus", "uid": "prometheus"},
                "expr": panel["targets"][0]["expr"], "instant": True, "range": False,
                "format": "time_series", "intervalMs": 15000, "maxDataPoints": 60} for panel in dashboard["panels"]]
    rendered = api(GRAFANA, "/api/ds/query", auth, {"from": str(now - 120000), "to": str(now), "queries": queries})
    for result in rendered["results"].values():
        assert not result.get("error") and result.get("frames"), "Grafana panel query failed"
        assert any(frame.get("data", {}).get("values") and all(frame["data"]["values"]) for frame in result["frames"]), "Grafana returned an empty frame"
    print("[OK] Grafana datasource OK, dashboard tu provision; 11/11 panel co du lieu that")
    if args.save:
        sample_at = time.time() - 30
        sample = check_values('sum(chat_http_requests_total{job="chat-app"})')[0]
        historic = query('sum(chat_http_requests_total{job="chat-app"})', sample_at)
        assert historic, "Need at least 30 seconds of samples before saving"
        Path(args.save).write_text(json.dumps({"time": sample_at, "http": historic[0]["value"][1]}), encoding="utf-8")
        print("[OK] Luu mau metrics khong co bi mat de kiem tra restart")
    if args.persistence:
        evidence = json.loads(Path(args.persistence).read_text(encoding="utf-8"))
        rows = query('sum(chat_http_requests_total{job="chat-app"})', evidence["time"])
        assert rows and rows[0]["value"][1] == evidence["http"], "Prometheus lost historic samples"
        print("MONITORING_PERSISTENCE_OK: mau TSDB va dashboard/datasource con sau recreate monitoring")
    print("GIAI_DOAN_5_OK")


if __name__ == "__main__": main()
