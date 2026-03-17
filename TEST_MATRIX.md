# DJ Visualizer Mini Test Matrix

## Automated (run in terminal)

1. Smoke test without running server
   - Command: `python3 smoke_test.py --retries 1 --delay 0.1`
   - Expected: `FAIL no reachable server URL`
2. Smoke test with local server
   - Command:
     - `python3 -m http.server 8080 --bind 127.0.0.1`
     - `python3 smoke_test.py`
   - Expected: `OK http://127.0.0.1:8080/dj-visualizer.html (200)`
3. Delayed-start smoke test (retry behavior)
   - Command: start server after delay and run `smoke_test.py --retries 12 --delay 0.3`
   - Expected: `OK ...` after retries
4. Port fallback in mac launcher
   - Occupy `8080`, run `start.command`
   - Expected: launcher uses `8081`
   - Occupy `8080` + `8081`
   - Expected: launcher uses `8082`

## Manual (browser interaction required)

1. Denied permissions
   - Deny MIC/SYSTEM capture.
   - Expected: `AUDIO DENIED`.
2. SYSTEM capture without shared audio
   - Share screen/window/tab without audio.
   - Expected: `NO SYSTEM AUDIO`.
3. SYSTEM audio ended
   - Start SYSTEM capture, then stop sharing.
   - Expected: `SYSTEM AUDIO ENDED`.
4. Fullscreen denied
   - Trigger fullscreen in restricted context.
   - Expected: `FULLSCREEN DENIED`.
5. Low-FPS quality scaling
   - Run on low-power machine and open debug (`G`).
   - Expected: quality drops to MED/LOW when FPS decreases.
