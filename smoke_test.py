#!/usr/bin/env python3
"""Simple smoke test for DJ Visualizer local server."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test for local DJ Visualizer server.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--ports", default="8080,8081,8082", help="Comma-separated ports")
    parser.add_argument("--path", default="/dj-visualizer.html", help="Path to check")
    parser.add_argument("--timeout", type=float, default=2.0, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=10, help="How many retry rounds to run")
    parser.add_argument("--delay", type=float, default=0.4, help="Delay between retry rounds (seconds)")
    args = parser.parse_args()

    ports = [p.strip() for p in args.ports.split(",") if p.strip()]
    for _ in range(max(1, args.retries)):
        for p in ports:
            url = f"http://{args.host}:{p}{args.path}"
            try:
                with urllib.request.urlopen(url, timeout=args.timeout) as resp:
                    code = getattr(resp, "status", 200)
                    if 200 <= code < 400:
                        print(f"OK {url} ({code})")
                        return 0
            except urllib.error.URLError:
                continue
            except Exception:
                continue
        if args.delay > 0:
            import time
            time.sleep(args.delay)

    print("FAIL no reachable server URL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
