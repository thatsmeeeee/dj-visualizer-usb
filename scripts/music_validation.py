#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from pathlib import Path
from statistics import mean, median

import librosa
import numpy as np

EXTS = {".mp3", ".wav", ".flac", ".m4a", ".aiff", ".ogg"}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ema(x: np.ndarray, a: float) -> np.ndarray:
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, len(x)):
        out[i] = out[i - 1] * (1 - a) + x[i] * a
    return out


def gather_tracks(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.name.startswith("._"):
            continue
        if p.suffix.lower() in EXTS:
            files.append(p)
    return sorted(files)


def process_track(path: Path, max_seconds: float = 90.0, debug: bool = False) -> dict | None:
    try:
        y, sr = librosa.load(path, sr=22050, mono=True, duration=max_seconds)
        if len(y) < sr * 20:
            return None

        hop = 512
        n_fft = 2048
        S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        def band(lo: float, hi: float) -> np.ndarray:
            idx = np.where((freqs >= lo) & (freqs < hi))[0]
            if len(idx) == 0:
                return np.zeros(S.shape[1], dtype=np.float32)
            return S[idx].mean(axis=0)

        sub = band(40, 120)
        bass = band(120, 250)
        mid = band(250, 3000)
        high = band(3000, 9000)
        energy = sub * 0.35 + bass * 0.35 + mid * 0.2 + high * 0.1

        # Normalize with robust percentile scaling
        def norm(x: np.ndarray) -> np.ndarray:
            p95 = np.percentile(x, 95)
            if p95 <= 1e-9:
                return np.zeros_like(x)
            return np.clip(x / p95, 0, 1)

        sub_n = norm(sub)
        high_n = norm(high)
        energy_n = norm(energy)

        onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
        flux_n = norm(onset_env)

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=hop, trim=False)
        tempo = float(np.ravel(tempo)[0])
        beat_frames = np.asarray(beat_frames, dtype=int)
        if len(beat_frames) < 24:
            return None

        beat_frames = beat_frames[beat_frames < len(energy_n)]
        if len(beat_frames) < 24:
            return None

        energy_s = ema(energy_n, 0.2)
        short_e = ema(energy_n, 0.12)
        long_e = ema(energy_n, 0.002)
        intensity = np.clip(0.88 + energy_s * 1.45 + ema(high_n, 0.2) * 0.7, 0.65, 2.9)

        # Per-beat snapshot
        b_sub = sub_n[beat_frames]
        b_energy = energy_s[beat_frames]
        b_flux = flux_n[np.minimum(beat_frames, len(flux_n) - 1)]
        b_intensity = intensity[beat_frames]

        # Downbeat inference by beat accents
        accent = b_sub * 1.3 + b_energy * 0.7 + b_flux * 0.6
        sums = [0.0, 0.0, 0.0, 0.0]
        for i, a in enumerate(accent):
            sums[i % 4] += float(a)
        offset = int(np.argmax(sums))

        beat_in_bar = np.array([((i - offset) % 4) + 1 for i in range(len(beat_frames))])
        bar_idx = np.array([((i - offset) // 4) for i in range(len(beat_frames))])
        phrase_bar = np.mod(bar_idx, 8)
        phrase_boundary = (beat_in_bar == 1) & (phrase_bar == 0)

        # harmonic tension proxy from chroma concentration
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=hop)
        chroma_sum = chroma.sum(axis=0)
        top2 = np.partition(chroma, -2, axis=0)[-2:]
        t_stability = np.clip((top2[-1] - top2[-2]) / np.maximum(1e-6, chroma_sum), 0, 1)
        harm_tension = 1 - t_stability
        b_tension = harm_tension[np.minimum(beat_frames, len(harm_tension) - 1)]

        # Simulated JS-like hot score + musical accent
        bpm_conf = np.clip(1 - (np.std(np.diff(librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop))) /
                              max(1e-3, np.mean(np.diff(librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)))))/0.15, 0, 1)

        hot = np.clip(
            b_energy * 0.33 +
            b_sub * 0.30 +
            np.clip((b_intensity - 0.65) / 2.25, 0, 1) * 0.17 +
            bpm_conf * 0.10 +
            phrase_boundary.astype(float) * 0.06 +
            b_tension * 0.04,
            0,
            1,
        )

        downbeat_conf = float((max(sums) - sorted(sums)[-2]) / max(1e-6, sum(sums) * 0.55))
        downbeat_conf = clamp(downbeat_conf, 0.0, 1.0)
        musical = np.ones_like(hot)
        for i in range(len(hot)):
            down = 1.0 if beat_in_bar[i] == 1 else 0.0
            boundary = 1.0 if phrase_boundary[i] else 0.0
            build = clamp((b_flux[i] - np.mean(b_flux)) * 0.5, 0, 0.35)
            release = clamp((b_sub[i] - 0.42) * 1.2, 0, 0.35)
            down_lift = down * (0.18 + 0.24 * downbeat_conf)
            musical[i] = clamp(1 + down_lift + boundary * 0.28 + build + release, 0.75, 1.85)

        beat_score = hot * musical

        # Flash decision model (closer to current JS gating)
        flash = np.zeros(len(beat_score), dtype=bool)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
        flashed_recent: list[float] = []
        rhythmic_mode = (105 <= tempo <= 180) and (bpm_conf >= 0.28)
        for i in range(len(beat_score)):
            down = beat_in_bar[i] == 1
            transient = clamp(b_flux[i] * 0.8 + b_sub[i] * 0.4, 0, 1.4)
            reactive_gain = clamp(0.72 + hot[i] * 1.55 + transient * 0.55, 0.72, 2.4)
            if rhythmic_mode:
                reactive_gain = max(reactive_gain, 1.6)

            lock_energy_floor = b_energy[i] > 0.11
            weak_gate = (rhythmic_mode and lock_energy_floor) or (hot[i] > 0.24) or (down and downbeat_conf > 0.30)
            hot_gate = (hot[i] > 0.16) if rhythmic_mode else (hot[i] > 0.36)
            if not weak_gate:
                continue
            t = float(beat_times[i])
            flashed_recent = [x for x in flashed_recent if (t - x) <= 1.0]
            by_signal = round((2 + hot[i] * 10) * reactive_gain)
            by_signal += 1 if b_sub[i] > 0.56 else 0
            by_signal += 1 if bpm_conf > 0.45 else 0
            by_signal += 1 if down else 0
            by_signal += 1 if phrase_boundary[i] else 0
            if rhythmic_mode:
                by_signal += 1
            elif (not down) and hot[i] < 0.48 and b_tension[i] < 0.30:
                by_signal -= 1
            hard_cap = 18 if rhythmic_mode else 14
            budget = int(clamp(by_signal, 1, hard_cap))
            if len(flashed_recent) >= budget:
                continue
            dynamic_thresh = 0.30 - (0.08 if hot[i] > 0.60 else 0.0) - (0.05 if rhythmic_mode else 0.0)
            pulse = beat_score[i] * (1.12 if hot[i] > 0.68 else 1.0)
            allow = hot_gate or (pulse >= dynamic_thresh) or (rhythmic_mode and pulse > 0.16)
            if allow:
                flash[i] = True
                flashed_recent.append(t)

        cov = float(np.mean(flash))
        down_flash = beat_score[beat_in_bar == 1].mean() if np.any(beat_in_bar == 1) else 0.0
        other_flash = beat_score[beat_in_bar != 1].mean() if np.any(beat_in_bar != 1) else 1e-6
        down_emphasis = float(down_flash / max(1e-6, other_flash))
        phrase_emphasis = float(
            beat_score[phrase_boundary].mean() / max(1e-6, beat_score[~phrase_boundary].mean())
        ) if np.any(phrase_boundary) and np.any(~phrase_boundary) else 1.0

        weak_mask = b_energy < np.percentile(b_energy, 35)
        weak_flash = float(np.mean(flash[weak_mask])) if np.any(weak_mask) else 0.0

        quality = (
            (0.40 <= cov <= 0.78)
            and (down_emphasis >= 1.12)
            and (phrase_emphasis >= 1.06)
            and (weak_flash <= 0.55)
        )

        return {
            "path": str(path),
            "tempo": float(tempo),
            "beats": int(len(beat_frames)),
            "coverage": cov,
            "down_emphasis": down_emphasis,
            "phrase_emphasis": phrase_emphasis,
            "weak_flash": weak_flash,
            "ok": quality,
        }
    except Exception as e:
        if debug:
            print(f"ERR {path}: {type(e).__name__}: {e}")
        return None


def summarize(rows: list[dict]) -> dict:
    cov = [r["coverage"] for r in rows]
    down = [r["down_emphasis"] for r in rows]
    phr = [r["phrase_emphasis"] for r in rows]
    weak = [r["weak_flash"] for r in rows]
    ok = sum(1 for r in rows if r["ok"])
    return {
        "tracks": len(rows),
        "ok_rate": ok / max(1, len(rows)),
        "coverage_median": median(cov),
        "down_median": median(down),
        "phrase_median": median(phr),
        "weak_median": median(weak),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-seconds", type=float, default=90.0)
    ap.add_argument("--print-bad", type=int, default=20)
    ap.add_argument("--debug-errors", action="store_true")
    args = ap.parse_args()

    tracks = gather_tracks(args.root)
    if args.limit > 0:
        tracks = tracks[: args.limit]

    rows: list[dict] = []
    for i, t in enumerate(tracks, 1):
        row = process_track(t, max_seconds=args.max_seconds, debug=args.debug_errors)
        if row is None:
            continue
        rows.append(row)
        if i % 15 == 0:
            print(f"processed {i}/{len(tracks)} -> valid {len(rows)}")

    if not rows:
        print("no valid tracks")
        return 1

    s = summarize(rows)
    print("SUMMARY")
    print(f"tracks={s['tracks']} ok_rate={s['ok_rate']:.3f} coverage_med={s['coverage_median']:.3f} down_med={s['down_median']:.3f} phrase_med={s['phrase_median']:.3f} weak_med={s['weak_median']:.3f}")

    bad = sorted(rows, key=lambda r: (r["ok"], r["down_emphasis"], -r["weak_flash"], abs(r["coverage"] - 0.58)))
    print("BAD_EXAMPLES")
    for r in bad[: args.print_bad]:
        print(
            f"{r['coverage']:.2f} down={r['down_emphasis']:.2f} phrase={r['phrase_emphasis']:.2f} weak={r['weak_flash']:.2f} bpm={r['tempo']:.1f} | {r['path']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
