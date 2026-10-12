# Jusic 自建听歌房客户端

[English](README_EN.md) | 简体中文

基于 [JusicRoomPlayer](https://github.com/seaworld92/JusicRoomPlayer) 的 Windows 听歌房客户端，
用于连接 [Jusic-Serve-Houses](https://github.com/JumpAlang/Jusic-Serve-Houses)。
支持在界面中填写服务器 IP / 域名和端口、保存地址、切换最近使用的服务器。

## 使用 Windows 客户端

运行打包后的 `JusicRoomPlayer-SelfHosted.exe`，无需安装 Python 或单独安装 mpv。
单文件 EXE 启动时会解压内置组件，请等待几秒。

点击右上角「服务器…」，填写服务器信息，再点击「保存并连接」。

| 设置 | Docker 直接部署的示例 |
| --- | --- |
| 协议 | `http` |
| IP / 域名 | 你的服务器 IP 或域名，不含协议和端口 |
| 端口 | `8080`，以 Docker 实际对外映射端口为准 |
| API 路径 | 留空 |

例如服务地址为 `http://192.168.1.10:8080`，IP 填 `192.168.1.10`，端口填 `8080`。
经 HTTPS 反向代理时选择 `https`，默认端口可留空；若代理配置了 `/api` 等前缀，则填写该路径。

保存后会停止当前播放、断开原房间、刷新新服务器的房间列表，并自动进入默认房间。
旧房间密码不会发送到新服务器。地址会在重启后恢复，也可从「最近使用」列表切换。
首次未配置时使用原公共服务器 `https://tx.alang.run/api`。
经典界面的「服务器…」入口在房间列表上方。

## 功能

- 浏览、过滤房间列表，进入密码房，切换房间。
- 随房间切歌同步播放，调整音量，查看歌词和点歌队列。
- 搜歌、点歌、点赞、投票切歌，显示服务端返回的失败原因。
- 保存本地收藏，导入 / 导出收藏，查看在线人员，设置昵称，发送聊天。
- 分享房间链接 / 二维码，最小化后驻留系统托盘。
- 主题界面支持切换主题；另保留经典界面和命令行前端。

配置位于 `%APPDATA%/JusicRoomPlayer/`：

| 文件 | 用途 |
| --- | --- |
| `server.json` | 当前服务器和最近地址 |
| `ui.json` | 主题、窗口大小 |
| `favorites.json` | 本地收藏 |

## 打包 Windows 客户端（内置 mpv）

### 1. 准备环境

在 **Windows 10 / 11 的 64 位电脑**上安装 **Python 3.10 或更高版本（64 位，含 Tkinter）**。
本地构建已使用 Python 3.12 验证。构建时需要联网下载 Python 依赖和 mpv，
并使用 Windows 自带的 `tar` 解压 mpv。

克隆你的仓库后，在仓库根目录打开 PowerShell：

```powershell
python --version
python -m venv .venv
```

### 2. 执行打包

重新打包前，请退出正在运行的客户端，以便覆盖原来的 EXE。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_local_client.ps1
```

此命令仅为当前构建进程允许脚本运行，不更改系统的执行策略。
不需要激活虚拟环境，也不需要在系统中安装 mpv。

构建脚本会自动：

1. 在 `.venv` 中安装 `requirements.txt` 的依赖及 PyInstaller。
2. 下载固定版本的普通 Windows x64 mpv 到 `build/`，并解压。
3. 读取 `VERSION`，生成 EXE 的版本信息。
4. 将主题客户端、Python 运行环境、mpv 和必要资源打进单文件 EXE。
5. 生成包含 EXE、使用说明、许可和文件校验信息的 ZIP。

### 3. 取得产物

```text
dist/
├─ JusicRoomPlayer-SelfHosted.exe
├─ JusicRoomPlayer-SelfHosted-Windows-x64.zip
├─ 使用说明.txt
├─ LICENSE
├─ THIRD_PARTY_NOTICES.txt
└─ build-info.json
```

直接运行 EXE 即可使用。分发时建议提供 ZIP，让使用说明和许可证一同保留。
`build-info.json` 记录 mpv 下载地址、压缩包 SHA-256 和 EXE SHA-256。

依赖已经安装时，再次打包可跳过依赖安装：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build_local_client.ps1 -SkipDependencies
```

也可添加 `-OutputDirectory .\dist\new-build` 输出到其他目录，保留原有产物。
清理 `build/` 后，下次打包会重新下载 mpv。
需要更新版本号时，修改 `VERSION` 后重新打包。

### 4. 验证打包结果（可选）

以下自检使用临时配置目录，验证打包后的界面、服务器设置、内置 mpv 和本地音频解码。
它不连接听歌房服务器；实际点歌和播放还需要连接你的服务进行验证。

```powershell
$env:JUSIC_BUILD_SMOKE_CHECK = "$PWD\dist\frozen-check.json"
$originalAppData = $env:APPDATA
try {
    $env:APPDATA = "$PWD\dist\smoke-appdata"
    Start-Process .\dist\JusicRoomPlayer-SelfHosted.exe -Wait
    Get-Content .\dist\frozen-check.json
} finally {
    $env:APPDATA = $originalAppData
    Remove-Item Env:JUSIC_BUILD_SMOKE_CHECK -ErrorAction SilentlyContinue
}
```

输出中的 `"ok": true` 表示自检通过。

## 从源码运行

源码运行需要另外安装 mpv 或通过 `--mpv` 指定它的位置；打包后的 EXE 已内置 mpv。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe jusic_client.py
```

也可选择其他前端：

```powershell
.\.venv\Scripts\python.exe jusic_gui.py
.\.venv\Scripts\python.exe jusic_room_player.py --host http://192.168.1.10:8080
```

界面支持 `--host` 显式指定服务器，省略时使用上次保存的地址：

```powershell
.\.venv\Scripts\python.exe jusic_client.py --host http://192.168.1.10:8080
.\.venv\Scripts\python.exe jusic_client.py --host https://music.example.com/api
```

完整地址不自动添加 `/api`；原来的纯域名 `--host tx.alang.run` 写法继续兼容公共接口。
需要查看调试输出时加 `--console`；指定播放引擎可加 `--mpv "C:\路径\mpv.exe"`。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests\check_server_gui.py classic
.\.venv\Scripts\python.exe tests\check_server_gui.py theme
```

测试覆盖服务器地址校验、端口和路径、HTTP / WebSocket 连接、设置持久化，
以及两种界面保存 / 切换服务器和隔离旧服务器事件的行为。
界面检查需要 Windows 图形环境，使用隔离配置，不会更改你的个人设置。
`tools/mem_bench.py` 保留用于开发时测量内存占用。

## 上传到 Git

提交源码、测试、文档、`VERSION` 和 `build_local_client.ps1`。
`.gitignore` 已排除 `.venv/`、`build/`、`dist/`、Python 缓存、运行日志和编辑器缓存。
EXE 和 ZIP 可作为仓库 Release 的附件分发，重新克隆仓库后按上述步骤构建。

## 目录结构

```text
JusicRoomPlayer/
├─ jusic_client.py          # Windows 主题客户端入口
├─ jusic_core.py            # HTTP / WebSocket、房间事件、mpv 引擎
├─ jusic_server.py          # 服务器地址解析和设置保存
├─ jusic_gui.py             # 经典界面及共享交互逻辑
├─ jusic_gui_bootstrap.py   # 主题界面
├─ jusic_room_player.py     # 命令行前端
├─ jusic_qr.py              # 分享二维码生成
├─ jusic_tray.py            # Windows 托盘
├─ build_local_client.ps1   # Windows EXE + ZIP 构建入口
├─ make_version_file.py     # Windows 版本资源生成
├─ requirements.txt        # 运行依赖
├─ VERSION                 # 版本号
├─ tests/                  # 服务器连接和界面检查
├─ tools/                  # 打包自检和内存测量
├─ LICENSE
├─ THIRD_PARTY_NOTICES
├─ README.md
└─ README_EN.md
```

## 许可证与致谢

客户端采用 [GPL-3.0](LICENSE)，第三方许可与致谢见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES)。
原项目：[seaworld92/JusicRoomPlayer](https://github.com/seaworld92/JusicRoomPlayer)。
播放引擎：[mpv](https://github.com/mpv-player/mpv)，Windows 构建来自
[shinchiro/mpv-winbuild-cmake](https://github.com/shinchiro/mpv-winbuild-cmake)。
界面使用 Tkinter / ttkbootstrap，实时连接使用 websockets。
