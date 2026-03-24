#!/usr/bin/env python3
"""Simple smoke test for DJ Visualizer local server."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Iterable


def probe_urls(host: str, ports: Iterable[str], path: str, timeout: float, retries: int, delay: float) -> str | None:
    for _ in range(max(1, retries)):
        for p in ports:
            url = f"http://{host}:{p}{path}"
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    code = getattr(resp, "status", 200)
                    if 200 <= code < 400:
                        print(f"OK {url} ({code})")
                        return url
            except urllib.error.URLError:
                continue
            except Exception:
                continue
        if delay > 0:
            time.sleep(delay)
    return None


def start_temp_server(host: str, ports: Iterable[str]) -> tuple[subprocess.Popen | None, str | None]:
    for p in ports:
        cmd = [sys.executable, "-m", "http.server", p, "--bind", host]
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            continue
        time.sleep(0.35)
        if proc.poll() is None:
            return proc, p
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for local DJ Visualizer server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--ports", default="8080,8081,8082", help="Comma-separated ports")
    parser.add_argument("--path", default="/dj-visualizer.html", help="Path to check")
    parser.add_argument("--timeout", type=float, default=2.0, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=10, help="How many retry rounds to run")
    parser.add_argument("--delay", type=float, default=0.4, help="Delay between retry rounds (seconds)")
    parser.add_argument(
        "--autostart",
        action="store_true",
        help="If no server is reachable, start a temporary local server and retry",
    )
    args = parser.parse_args()

    ports = [p.strip() for p in args.ports.split(",") if p.strip()]
    hit = probe_urls(args.host, ports, args.path, args.timeout, args.retries, args.delay)
    if hit:
        return 0

    if not args.autostart:
        print("FAIL no reachable server URL")
        return 1

    proc, port = start_temp_server(args.host, ports)
    if proc is None or port is None:
        print("FAIL no reachable server URL (autostart failed)")
        return 1

    try:
        hit = probe_urls(args.host, [port], args.path, args.timeout, args.retries, args.delay)
        if hit:
            print("INFO smoke test used temporary server")
            return 0
        print("FAIL no reachable server URL (temporary server not responding)")
        return 1
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
