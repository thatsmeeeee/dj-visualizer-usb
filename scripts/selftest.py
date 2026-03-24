#!/usr/bin/env python3
"""Automated local regression checks for DJ Visualizer USB bundle."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "smoke_test.py"


def run(cmd: list[str], expect: int = 0) -> tuple[bool, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    output = (proc.stdout + proc.stderr).strip()
    ok = proc.returncode == expect
    return ok, output


def test_no_server_fail() -> tuple[bool, str]:
    ok, out = run([sys.executable, str(SMOKE), "--retries", "1", "--delay", "0.1"], expect=1)
    if not ok:
        return False, out
    if "FAIL no reachable server URL" not in out:
        return False, out + "\nmissing expected fail marker"
    return True, "EXPECTED FAIL observed: no reachable server URL"


def test_autostart_ok() -> tuple[bool, str]:
    ok, out = run([sys.executable, str(SMOKE), "--autostart"], expect=0)
    if ok and "INFO smoke test used temporary server" not in out:
        # If a local server is already up, smoke test can pass without autostart marker.
        if "OK http://127.0.0.1:" not in out:
            return False, out + "\nmissing autostart info marker"
    return ok, out


def test_with_live_server_ok() -> tuple[bool, str]:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", "8080", "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.8)
        return run([sys.executable, str(SMOKE)], expect=0)
    finally:
        server.terminate()
        try:
            server.wait(timeout=2)
        except Exception:
            server.kill()


def start_port_occupiers(ports: list[int]) -> list[subprocess.Popen]:
    procs: list[subprocess.Popen] = []
    try:
        for p in ports:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    (
                        "import socket,time,sys;"
                        "s=socket.socket();"
                        "s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);"
                        "s.bind(('127.0.0.1',int(sys.argv[1])));"
                        "s.listen(1);"
                        "time.sleep(30)"
                    ),
                    str(p),
                ],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            procs.append(proc)
            time.sleep(0.35)
            if proc.poll() is not None:
                raise RuntimeError(f"failed to occupy port {p}")
        return procs
    except Exception:
        for proc in procs:
            try:
                proc.terminate()
            except Exception:
                pass
        raise


def stop_port_occupiers(procs: list[subprocess.Popen]) -> None:
    for proc in procs:
        try:
            proc.terminate()
        except Exception:
            pass
    for proc in procs:
        try:
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def test_autostart_fallback_when_8080_busy() -> tuple[bool, str]:
    procs = start_port_occupiers([8080])
    try:
        ok, out = run([sys.executable, str(SMOKE), "--autostart"], expect=0)
        if not ok:
            return False, out
        if "127.0.0.1:8081" not in out and "127.0.0.1:8082" not in out:
            return False, out + "\nautostart did not fallback from busy 8080"
        return True, out
    finally:
        stop_port_occupiers(procs)


def test_autostart_fails_when_all_ports_busy() -> tuple[bool, str]:
    procs = start_port_occupiers([8080, 8081, 8082])
    try:
        ok, out = run([sys.executable, str(SMOKE), "--autostart", "--retries", "2", "--delay", "0.1"], expect=1)
        if not ok:
            return False, out
        if "autostart failed" not in out:
            return False, out + "\nmissing expected autostart failure marker"
        return True, "EXPECTED FAIL observed: autostart failed when all ports busy"
    finally:
        stop_port_occupiers(procs)


def test_python_files_compile() -> tuple[bool, str]:
    files = [
        "smoke_test.py",
        "scripts/music_validation.py",
        "scripts/selftest.py",
    ]
    return run([sys.executable, "-m", "py_compile", *files], expect=0)


def test_start_command_syntax() -> tuple[bool, str]:
    return run(["bash", "-n", "start.command"], expect=0)


def test_flash_verdict_rules() -> tuple[bool, str]:
    import track_suite

    good_rows = [
        {"tempo": 128.0, "coverage": 0.74, "weak_flash": 0.34, "down_emphasis": 1.22, "phrase_emphasis": 1.10},
        {"tempo": 132.0, "coverage": 0.76, "weak_flash": 0.30, "down_emphasis": 1.20, "phrase_emphasis": 1.08},
        {"tempo": 140.0, "coverage": 0.78, "weak_flash": 0.28, "down_emphasis": 1.18, "phrase_emphasis": 1.12},
        {"tempo": 100.0, "coverage": 0.54, "weak_flash": 0.40, "down_emphasis": 1.14, "phrase_emphasis": 1.07},
    ]
    ok_summary = track_suite.summarize(good_rows)
    ok, notes = track_suite.verdict(ok_summary, rave_min_cov=0.72, general_min_cov=0.42)
    if not ok:
        return False, f"expected PASS verdict for healthy flash profile, got notes={notes}"

    bad_rows = [dict(r, weak_flash=0.82) for r in good_rows]
    bad_summary = track_suite.summarize(bad_rows)
    bad_ok, bad_notes = track_suite.verdict(bad_summary, rave_min_cov=0.72, general_min_cov=0.42)
    if bad_ok:
        return False, "expected FAIL verdict for excessive weak-section flashing"
    if not any("weak sections" in n for n in bad_notes):
        return False, f"missing weak-flash failure note: {bad_notes}"

    return True, "flash verdict thresholds behave as expected"


def main() -> int:
    tests = [
        ("no_server_fail", test_no_server_fail),
        ("autostart_ok", test_autostart_ok),
        ("live_server_ok", test_with_live_server_ok),
        ("autostart_fallback_when_8080_busy", test_autostart_fallback_when_8080_busy),
        ("autostart_fails_when_all_ports_busy", test_autostart_fails_when_all_ports_busy),
        ("py_compile", test_python_files_compile),
        ("start_command_syntax", test_start_command_syntax),
        ("flash_verdict_rules", test_flash_verdict_rules),
    ]

    failed = 0
    for name, fn in tests:
        ok, out = fn()
        state = "PASS" if ok else "FAIL"
        print(f"[{state}] {name}")
        if out:
            print(out)
        if not ok:
            failed += 1

    if failed:
        print(f"\nRESULT: FAIL ({failed}/{len(tests)} failed)")
        return 1

    print(f"\nRESULT: PASS ({len(tests)} tests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
