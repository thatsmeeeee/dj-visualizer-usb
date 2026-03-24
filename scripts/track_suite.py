#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import median


def pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    i = int(round((len(s) - 1) * p))
    return s[max(0, min(i, len(s) - 1))]


def classify_use_case(bpm: float) -> str:
    if 105 <= bpm <= 180:
        return "rave_like"
    if 90 <= bpm < 105:
        return "midtempo_like"
    return "other"


def summarize(rows: list[dict]) -> dict:
    cov = [r["coverage"] for r in rows]
    weak = [r["weak_flash"] for r in rows]
    down = [r["down_emphasis"] for r in rows]
    phrase = [r["phrase_emphasis"] for r in rows]

    rave = [r for r in rows if classify_use_case(r["tempo"]) == "rave_like"]
    midtempo = [r for r in rows if classify_use_case(r["tempo"]) == "midtempo_like"]

    def med(items: list[dict], key: str) -> float:
        if not items:
            return 0.0
        return float(median([x[key] for x in items]))

    return {
        "tracks": len(rows),
        "coverage_median": float(median(cov)) if cov else 0.0,
        "coverage_p10": pct(cov, 0.10),
        "coverage_p90": pct(cov, 0.90),
        "weak_flash_median": float(median(weak)) if weak else 0.0,
        "down_emphasis_median": float(median(down)) if down else 0.0,
        "phrase_emphasis_median": float(median(phrase)) if phrase else 0.0,
        "rave_tracks": len(rave),
        "rave_coverage_median": med(rave, "coverage"),
        "midtempo_tracks": len(midtempo),
        "midtempo_coverage_median": med(midtempo, "coverage"),
    }


def verdict(summary: dict, rave_min_cov: float, general_min_cov: float) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True

    if summary["coverage_median"] < general_min_cov:
        ok = False
        notes.append(f"general coverage too low: {summary['coverage_median']:.3f} < {general_min_cov:.3f}")

    if summary["rave_tracks"] >= 3 and summary["rave_coverage_median"] < rave_min_cov:
        ok = False
        notes.append(
            f"rave coverage too low: {summary['rave_coverage_median']:.3f} < {rave_min_cov:.3f}"
        )

    if summary["weak_flash_median"] > 0.70:
        ok = False
        notes.append(f"too many flashes in weak sections: {summary['weak_flash_median']:.3f} > 0.700")

    if summary["down_emphasis_median"] < 1.05:
        ok = False
        notes.append(f"downbeat emphasis too weak: {summary['down_emphasis_median']:.3f} < 1.050")

    return ok, notes


def main() -> int:
    from music_validation import gather_tracks, process_track

    ap = argparse.ArgumentParser(description="Batch validation suite for DJ visualizer track behavior")
    ap.add_argument("root", type=Path, help="Path with audio tracks")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-seconds", type=float, default=90.0)
    ap.add_argument("--rave-min-cov", type=float, default=0.85)
    ap.add_argument("--general-min-cov", type=float, default=0.55)
    ap.add_argument("--json-out", type=Path)
    ap.add_argument("--print-worst", type=int, default=12)
    args = ap.parse_args()

    tracks = gather_tracks(args.root)
    if args.limit > 0:
        tracks = tracks[: args.limit]

    rows: list[dict] = []
    for i, t in enumerate(tracks, 1):
        r = process_track(t, max_seconds=args.max_seconds)
        if r is None:
            continue
        rows.append(r)
        if i % 20 == 0:
            print(f"processed {i}/{len(tracks)} valid={len(rows)}")

    if not rows:
        print("RESULT: FAIL")
        print("reason: no valid tracks")
        return 1

    s = summarize(rows)
    ok, notes = verdict(s, args.rave_min_cov, args.general_min_cov)

    worst = sorted(rows, key=lambda r: (r["coverage"], r["down_emphasis"], -r["weak_flash"]))[: args.print_worst]

    print("SUMMARY")
    print(
        "tracks={tracks} cov_med={coverage_median:.3f} cov_p10={coverage_p10:.3f} "
        "cov_p90={coverage_p90:.3f} weak_med={weak_flash_median:.3f} "
        "down_med={down_emphasis_median:.3f} phrase_med={phrase_emphasis_median:.3f} "
        "rave={rave_tracks} rave_cov_med={rave_coverage_median:.3f}".format(**s)
    )

    print("WORST")
    for r in worst:
        print(
            f"cov={r['coverage']:.2f} weak={r['weak_flash']:.2f} down={r['down_emphasis']:.2f} "
            f"phrase={r['phrase_emphasis']:.2f} bpm={r['tempo']:.1f} | {r['path']}"
        )

    if args.json_out:
        payload = {"summary": s, "notes": notes, "ok": ok, "worst": worst}
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON: {args.json_out}")

    if ok:
        print("RESULT: PASS")
        return 0

    print("RESULT: FAIL")
    for n in notes:
        print(f"- {n}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
