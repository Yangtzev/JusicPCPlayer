# Jusic self-hosted room client

English | [简体中文](README.md)

Based on [seaworld92/JusicRoomPlayer](https://github.com/seaworld92/JusicRoomPlayer),
for [Jusic-Serve-Houses](https://github.com/JumpAlang/Jusic-Serve-Houses).
The desktop interface supports entering a server IP / domain, port, protocol and API prefix,
saving the address, and switching between recently used servers.

## Use the Windows client

Run `JusicRoomPlayer-SelfHosted.exe`. Python and mpv are bundled; no separate installation is needed.
The single-file executable extracts its embedded components at startup, which can take a few seconds.

Click **服务器…** (Server settings). For a direct Docker deployment, choose `http`,
enter your server IP / domain, enter the published port (usually `8080`), and leave the API path empty.
Click **保存并连接** (Save and connect). For an HTTPS reverse proxy, choose `https` and set the
port and prefix to match your proxy. The saved address is restored at startup.

Switching stops playback, disconnects the old room, refreshes the new server's rooms and enters
the default room. Previous room passwords are cleared. The classic interface has the same settings
button above its room list; the theme interface has it at the top right.

Features include synchronized playback, song search and requests, queues, lyrics, voting,
favorites, chat, online members, room sharing, themes and the Windows system tray.
Settings are stored in `%APPDATA%/JusicRoomPlayer/`:
`server.json` for servers, `ui.json` for themes and geometry, and `favorites.json` for favorites.

## Build a Windows client with mpv

Use a Windows 10 / 11 x64 computer with Python 3.10+ x64 including Tkinter.
The build has been verified with Python 3.12. Internet access is required to download dependencies
and mpv; extraction uses the Windows `tar` command.

Close any running copy of the client before rebuilding.
From your cloned repository's root, run in PowerShell:

```powershell
python -m venv .venv
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_local_client.ps1
```

The script installs runtime dependencies and PyInstaller in `.venv`, downloads a pinned standard
x64 mpv build into `build/`, reads `VERSION`, and builds the theme client as a single-file EXE.
No system-wide mpv installation or virtual-environment activation is required.
The execution-policy override only applies to the build process.

Outputs:

- `dist/JusicRoomPlayer-SelfHosted.exe`
- `dist/JusicRoomPlayer-SelfHosted-Windows-x64.zip`
- Usage instructions, licenses and `dist/build-info.json` with download details and SHA-256 hashes.

Share the ZIP to include the instructions and licenses. To rebuild with dependencies already installed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_local_client.ps1 -SkipDependencies
```

Use `-OutputDirectory .\dist\new-build` to build into another folder.
Change `VERSION` before rebuilding to update the executable's version metadata.
Deleting `build/` causes the next build to download mpv again.
For the optional packaged-app smoke check, see the [Chinese build instructions](README.md).
It verifies the interface, server settings, embedded mpv and local audio decoding, without connecting to a server.

## Run from source

Source runs require an installed mpv or an explicit `--mpv` path:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe jusic_client.py
.\.venv\Scripts\python.exe jusic_client.py --host http://192.168.1.10:8080
```

Other frontends are `jusic_gui.py` (classic) and `jusic_room_player.py` (CLI).
A complete `--host` URL does not automatically add `/api`.
Omitting `--host` in the GUI restores the saved server; the legacy domain-only syntax remains supported.
Add `--console` for GUI debugging output.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests\check_server_gui.py classic
.\.venv\Scripts\python.exe tests\check_server_gui.py theme
```

GUI checks require a desktop environment and use isolated settings.
`tools/mem_bench.py` remains available for development memory measurements.

## Repository contents

Keep application sources, tests, documentation, licenses, `VERSION`, `requirements.txt`,
`make_version_file.py` and `build_local_client.ps1` in Git.
The ignore rules exclude `.venv/`, `build/`, `dist/`, Python caches, logs and editor caches.
Publish EXE / ZIP files as Release attachments rather than source files.
Duplicate launchers and legacy build / release scripts have been removed.

## License and credits

Licensed under [GPL-3.0](LICENSE). See [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES).
Credits: the original JusicRoomPlayer project, Jusic-Serve-Houses, mpv,
shinchiro's Windows mpv builds, Tkinter, ttkbootstrap and websockets.
