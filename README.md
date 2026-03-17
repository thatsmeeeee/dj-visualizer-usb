# DJ Visualizer (USB / Plug-and-Go)

A single-file, browser-based DJ visualizer designed to live on a USB stick: plug in, run the launcher, and you're live.

It starts a local web server and opens:

- `http://localhost:8080/dj-visualizer.html` (or `8081` / `8082` if busy)

## What's inside

- `dj-visualizer.html` — the full visualizer (canvas + UI + audio analysis)
- `start.bat` — Windows launcher (portable Python → system Python → Node)
- `start.command` — macOS launcher (Python → Node)
- `python-portable/` — bundled Python for Windows (if present)
- `smoke_test.py` — quick local server smoke test
- `RELEASE_CHECKLIST.md` — pre-gig validation checklist
- `README.md`

## Quick start (Windows)

1. Plug in the USB stick and open the folder.
2. Double-click `start.bat`.
3. Your browser should open the visualizer automatically.

If it doesn't open, manually visit:

- `http://localhost:8080/dj-visualizer.html`
- then try `8081` or `8082`.

### Windows requirements / notes

`start.bat` will try in this order:

1. `python-portable\python.exe` (bundled)
2. `py -3`
3. `python`
4. `python3`
5. `npx http-server`

If none are available, install **Python 3** or **Node.js**.

If PowerShell execution is blocked by policy, the script prints a manual fallback command.
If PowerShell is blocked, `start.bat` now auto-falls back to a CMD launch on `localhost:8080`.

## Quick start (macOS)

1. Plug in the USB stick and open the folder.
2. (One-time) make the launcher executable:
   ```bash
   chmod +x start.command
   ```
3. Double-click `start.command`.

If it doesn't open, manually visit:

- `http://localhost:8080/dj-visualizer.html`
- then try `8081` or `8082`.

### macOS requirements / notes

`start.command` will try:

1. `python3`
2. `python`
3. `npx http-server`

So you need **Python 3** or **Node.js** installed.

The launcher prefers **Chrome**. If not found, it falls back to your default browser.
On both Windows and macOS, launchers now try **Chrome**, then **Edge**, then default browser.

## Using audio (MIC / SYSTEM / MIX)

In the UI, you can switch the audio source:

- **MIC** — uses your microphone input
- **SYSTEM** — captures system/tab audio via screen sharing (browser capture)
- **MIX** — combines MIC + SYSTEM

### Important: SYSTEM audio needs permission + correct sharing option

When you start **SYSTEM** (or **MIX**) the browser will ask you to share a screen/window/tab.

To actually get audio, you usually must:
- select the right screen/tab/window, and
- enable something like **"Share audio"** (wording depends on the browser/OS).

If you deny permission, the app shows `AUDIO DENIED`.
If you share screen/tab but audio is not included, the app shows `NO SYSTEM AUDIO`.
If shared system audio stops mid-session, the app shows `SYSTEM AUDIO ENDED`.

## Controls

Move the mouse to reveal the UI panel.

Hotkeys:
- `Space` — Start / Stop
- `A` — Audio source (MIC / SYSTEM / MIX)
- `P` — Preset (CLUB / OPEN AIR / LOW POWER)
- `M` — Mode
- `C` — Color mode
- `Q` — Quality mode (AUTO / HIGH / MED / LOW)
- `T` — Toggle tuning panel
- `S` — Strobe toggle
- `F` — Fullscreen
- `G` — Debug overlay (FPS, audio levels)

## Presets and tuning

- **CLUB** — balanced default for indoor DJ setup.
- **OPEN AIR** — more stable beat response for spacious/less compressed audio.
- **LOW POWER** — safer defaults for weaker laptops.

Use **TUNE** panel for live adjustments:
- **SENSITIVITY** — how easily flashes react to signal changes.
- **FLASH RATE** — overall flash intensity/rate scaling.
- **SAFETY** — stricter/looser limiter behavior.

## Safety warning (strobe / flashes)

This visualizer can produce rapid flashes (strobe/whiteouts).
Use responsibly. If you or anyone present is sensitive to flashing lights (photosensitive epilepsy),
disable strobe (`S`) and avoid high-intensity settings.

## Troubleshooting

### "Server failed to start on ports 8080/8081/8082"
Something is already using those ports. Close the other process, or edit the launcher to use different ports.

### "AUDIO DENIED"
Grant permission for microphone / screen-share audio in your browser, then try again.

### "NO SYSTEM AUDIO"
Start again in `SYSTEM` or `MIX` mode and make sure **Share audio** is enabled in the browser share dialog.

### "SYSTEM AUDIO ENDED"
Your screen-share audio track was stopped. Start audio again and re-share with audio enabled.

### No system audio captured
Try a different browser (Chrome is the most consistent for screen/tab audio capture).
When sharing, ensure **audio sharing is enabled**.

## Browser access

The server is **localhost-only** and not exposed to the network (safe for USB gigs).

## Quick smoke test

After launching, run:

```bash
python3 smoke_test.py
```

Expected result: `OK http://127.0.0.1:8080/dj-visualizer.html (...)` (or 8081/8082).

## Test matrix

See [TEST_MATRIX.md](TEST_MATRIX.md) for automated and manual test scenarios.

## USB Reality (Important)

- USB auto-run is commonly blocked by OS security policy. Plan for manual launcher click.
- On Windows, SmartScreen may warn on first run.
- On macOS, Gatekeeper may require right-click -> Open on first launch.
- Screen/system-audio capture always requires an explicit user permission step in the browser.

## License

MIT License — use, modify, and share freely. See [LICENSE](LICENSE).
