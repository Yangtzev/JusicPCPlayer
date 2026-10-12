"""Run each GUI smoke check in a separate process (ttkbootstrap has one root)."""
import asyncio
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from jusic_server import load_server_settings, save_server_settings

async def idle_session(self, room_id, password):
    await asyncio.Future()

def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)

with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"APPDATA": folder}), \
        patch("jusic_core.get_rooms", return_value=[{"id": "DEFAULT", "name": "test"}]), \
        patch("jusic_core.RoomClient._session_loop", idle_session):
    save_server_settings("http://127.0.0.1:8080", [])
    if sys.argv[1] == "theme":
        import ttkbootstrap as ttb
        from jusic_gui_bootstrap import BootstrapGui as Gui, parse_args
        root = ttb.Window(themename="bootstrap-light")
    else:
        from jusic_gui import JusicGui as Gui, parse_args
        root = tk.Tk()
    root.withdraw()
    # Avoid creating a real system-tray icon during a hidden GUI test.
    with patch.object(Gui, "_init_tray"):
        gui = Gui(root, parse_args(["--console"]))
    old_client = gui.client
    try:
        assert gui.args.host == "http://127.0.0.1:8080", "Saved server was not restored"
        assert any(str(w.cget("text")) == "服务器…" for w in widgets(root) if "text" in w.keys())
        gui._open_server_settings()
        gui._server_win.withdraw()
        body = gui._server_win.winfo_children()[0]
        def at(row, column):
            return body.grid_slaves(row=row, column=column)[0]
        at(1, 1).set("http")
        for row, value in ((2, "192.168.1.20"), (3, "8081"), (4, "")):
            at(row, 1).delete(0, "end")
            at(row, 1).insert(0, value)
        gui._current_music = {"id": "old-song", "name": "old song"}
        gui._queue_songs = [{"id": "old-song"}]
        gui.args.house = "private-old-room"
        gui.args.password = "old-password"
        save = next(w for w in widgets(body) if "text" in w.keys() and w.cget("text") == "保存并连接")
        save.invoke()
        assert gui.args.host == "http://192.168.1.20:8081"
        assert gui.args.house == "" and gui.args.password == ""
        assert gui._current_music is None and gui._queue_songs == []
        assert gui.client.engine.volume == 90
        assert load_server_settings()["server"] == gui.args.host
        # Simulate an old request returning after the server has been switched.
        old_client._emit("rooms", [{"id": "STALE", "name": "old server"}])
        old_client._emit("music", {"id": "STALE", "name": "old song"})
        gui._poll()
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            root.update()
            if gui.rooms and gui.client.room:
                break
            time.sleep(0.01)
        assert [r["id"] for r in gui.rooms] == ["DEFAULT"]
        assert gui._current_music is None, "Late old-server music reached the interface"
        assert gui.client.room["id"] == "DEFAULT"
        old_client.engine._ipc_thread.join(1)
        assert not old_client.engine._ipc_thread.is_alive()
        # Reopen the dialog: fields and history must reflect the saved server.
        gui._open_server_settings()
        gui._server_win.withdraw()
        body = gui._server_win.winfo_children()[0]
        assert at(2, 1).get() == "192.168.1.20" and at(3, 1).get() == "8081"
        assert "http://127.0.0.1:8080" in at(0, 1).cget("values")
        print(sys.argv[1] + " GUI: save/connect, restore, history and stale-event isolation passed")
    finally:
        gui._on_close()
