# DJ Visualizer Release Checklist

1. Launch test on Windows via `start.bat`.
2. Launch test on macOS via `start.command`.
3. Confirm URL opens on `localhost` (`8080`, fallback `8081/8082`).
4. Run smoke test:
   - `python3 smoke_test.py`
5. Verify `MIC` mode (audio permission granted).
6. Verify `SYSTEM` mode with **Share audio** enabled.
7. Verify `MIX` mode and source switching while live.
8. Confirm `NO SYSTEM AUDIO` appears if audio is not shared.
9. Confirm `SYSTEM AUDIO ENDED` appears when share is stopped.
10. Test hotkeys: `Space`, `A`, `P`, `M`, `C`, `Q`, `T`, `S`, `F`, `G`.
11. Check fullscreen fail handling shows status hint.
12. Watch FPS/quality in debug overlay (`G`) on at least one low-power machine.
13. Confirm strobe safety behavior and default intensity.
14. Re-open once after clean stop to confirm no orphan server process.
