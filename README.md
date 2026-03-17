# DJ Visualizer (USB / Plug-and-Go)

A single-file, browser-based DJ visualizer designed to live on a USB stick: plug in, run the launcher, and you're live.

It starts a local web server and opens:

- `http://localhost:8080/dj-visualizer.html` (or `8081` / `8082` if busy)

## What's inside

- `dj-visualizer.html` — the full visualizer (canvas + UI + audio analysis)
- `start.bat` — Windows launcher (portable Python → system Python → Node)
- `start.command` — macOS launcher (Python → Node)
- `python-portable/` — bundled Python for Windows (if present)
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

## Controls

Move the mouse to reveal the UI panel.

Hotkeys:
- `Space` — Start / Stop
- `A` — Audio source (MIC / SYSTEM / MIX)
- `M` — Mode
- `C` — Color mode
- `S` — Strobe toggle
- `F` — Fullscreen
- `G` — Debug overlay (FPS, audio levels)

## Safety warning (strobe / flashes)

This visualizer can produce rapid flashes (strobe/whiteouts).
Use responsibly. If you or anyone present is sensitive to flashing lights (photosensitive epilepsy),
disable strobe (`S`) and avoid high-intensity settings.

## Troubleshooting

### "Server failed to start on ports 8080/8081/8082"
Something is already using those ports. Close the other process, or edit the launcher to use different ports.

### "AUDIO DENIED"
Grant permission for microphone / screen-share audio in your browser, then try again.

### No system audio captured
Try a different browser (Chrome is the most consistent for screen/tab audio capture).
When sharing, ensure **audio sharing is enabled**.

## Language

The launcher scripts display messages in **Czech**. You can translate them by editing `start.bat` or `start.command`.

## Browser access

The server is **localhost-only** and not exposed to the network (safe for USB gigs).

## License

MIT License — use, modify, and share freely. See [LICENSE](LICENSE).
