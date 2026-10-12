"""Opt-in packaged-app check; inactive during normal client launches."""
import os
if os.environ.get("JUSIC_BUILD_SMOKE_CHECK"):
    import json
    from pathlib import Path
    import subprocess
    import sys
    import tempfile
    import wave
    result_path = Path(os.environ["JUSIC_BUILD_SMOKE_CHECK"])
    result = {"ok": False}
    root = None
    try:
        import ttkbootstrap as ttb
        from jusic_gui_bootstrap import BootstrapGui, parse_args
        from jusic_gui import bundled_mpv_path
        from jusic_server import ServerAddress
        root = ttb.Window(themename="bootstrap-light")
        root.withdraw()
        # Hidden build verification must not install a tray icon or contact a server.
        BootstrapGui._init_tray = lambda self: None
        gui = BootstrapGui(root, parse_args(["--host", "http://127.0.0.1:8080", "--console"]))
        gui._open_server_settings()
        gui._server_win.withdraw()
        root.update_idletasks()
        mpv = bundled_mpv_path()
        assert mpv and Path(mpv).is_file(), "Embedded mpv is missing"
        assert gui.client.engine.mpv_path == mpv
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        version = subprocess.run([mpv, "--version"], capture_output=True, text=True,
                                  timeout=15, creationflags=flags)
        assert version.returncode == 0, version.stderr
        with tempfile.TemporaryDirectory() as folder:
            audio = str(Path(folder) / "silence.wav")
            with wave.open(audio, "wb") as fh:
                fh.setnchannels(1)
                fh.setsampwidth(2)
                fh.setframerate(8000)
                fh.writeframes(bytes(16000))
            decode = subprocess.run([mpv, "--no-config", "--no-video", "--ao=null",
                                     "--really-quiet", audio], capture_output=True, text=True,
                                     timeout=15, creationflags=flags)
            assert decode.returncode == 0, decode.stderr
        result.update(ok=True, frozen=bool(getattr(sys, "frozen", False)),
                      mpv_embedded=True, mpv_version=version.stdout.splitlines()[0],
                      audio_decode=True, server_settings_dialog=True,
                      websocket_url=ServerAddress.parse(gui.args.host).websocket_url("server/000/test/websocket"))
        gui._on_close()
        root = None
    except Exception:
        import traceback
        result["error"] = traceback.format_exc()
    finally:
        if root is not None:
            root.destroy()
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    os._exit(0 if result["ok"] else 1)
