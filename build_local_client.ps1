param(
    [string]$PythonPath = "",
    [switch]$SkipDependencies,
    [string]$OutputDirectory = "dist"
)
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$outputExe = Join-Path $OutputDirectory "JusicRoomPlayer-SelfHosted.exe"
$outputZip = Join-Path $OutputDirectory "JusicRoomPlayer-SelfHosted-Windows-x64.zip"
if (Test-Path -LiteralPath $outputExe) {
    try {
        $outputHandle = [System.IO.File]::Open($outputExe, 'Open', 'ReadWrite', 'None')
        $outputHandle.Dispose()
    } catch {
        throw "Close the running client before rebuilding, or use -OutputDirectory to select another output folder."
    }
}
if (-not $PythonPath) {
    $PythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $PythonPath)) {
        throw "Create .venv first: python -m venv .venv"
    }
}
if (-not $SkipDependencies) {
    & $PythonPath -m pip install -r requirements.txt pyinstaller
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
}
$mpvArchive = Join-Path $PSScriptRoot "build\mpv-download\mpv-x86_64-20261012.7z"
$mpvFolder = Join-Path $PSScriptRoot "build\mpv-bundled"
$mpvExecutable = Join-Path $mpvFolder "mpv.exe"
$mpvUrl = "https://github.com/shinchiro/mpv-winbuild-cmake/releases/download/20261012/mpv-x86_64-20261012-git-88eb9f2e73.7z"
New-Item -ItemType Directory -Path (Split-Path $mpvArchive), $mpvFolder -Force | Out-Null
if (-not (Test-Path -LiteralPath $mpvExecutable)) {
    if (-not (Test-Path -LiteralPath $mpvArchive)) {
        Invoke-WebRequest $mpvUrl -OutFile $mpvArchive
    }
    & tar -xf $mpvArchive -C $mpvFolder
    if ($LASTEXITCODE -ne 0) { throw "mpv extraction failed" }
}
& $PythonPath make_version_file.py
if ($LASTEXITCODE -ne 0) { throw "Version resource generation failed" }
$buildArguments = @(
    "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
    "--name", "JusicRoomPlayer-SelfHosted", "--distpath", $OutputDirectory,
    "--workpath", "build\selfhost", "--specpath", "build",
    "--version-file", "$(Join-Path $PSScriptRoot 'build\version_info.txt')",
    "--exclude-module", "numpy", "--exclude-module", "matplotlib",
    "--exclude-module", "pandas", "--exclude-module", "scipy",
    "--exclude-module", "pytest", "--exclude-module", "IPython",
    "--add-data", "$mpvExecutable;_engine\mpv",
    "--add-data", "$(Join-Path $mpvFolder 'd3dcompiler_43.dll');_engine\mpv",
    "--add-data", "$(Join-Path $mpvFolder 'mpv\fonts.conf');_engine\mpv\mpv",
    "--add-data", "$(Join-Path $PSScriptRoot 'VERSION');.", "--add-data", "$(Join-Path $PSScriptRoot 'LICENSE');.",
    "--add-data", "$(Join-Path $PSScriptRoot 'THIRD_PARTY_NOTICES');.", "jusic_client.py"
)
& $PythonPath @buildArguments
if ($LASTEXITCODE -ne 0) { throw "Client packaging failed" }
Copy-Item -LiteralPath LICENSE -Destination (Join-Path $OutputDirectory "LICENSE") -Force
Copy-Item -LiteralPath THIRD_PARTY_NOTICES -Destination (Join-Path $OutputDirectory "THIRD_PARTY_NOTICES.txt") -Force
$buildInfo = [ordered]@{
    mpv_download = $mpvUrl
    mpv_archive_sha256 = (Get-FileHash -LiteralPath $mpvArchive -Algorithm SHA256).Hash
    client_sha256 = (Get-FileHash -LiteralPath $outputExe -Algorithm SHA256).Hash
}
$buildInfo | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory "build-info.json") -Encoding utf8
Write-Host "Created $outputExe (Python + mpv included)"

$instructions = @'
Jusic 自建服务器客户端（Windows 64 位）

双击 JusicRoomPlayer-SelfHosted.exe 即可运行。
程序已内置 Python、主题界面和 mpv，无需单独安装运行环境。
单文件版首次打开需要解压内置组件，请等待几秒。

点击右上角「服务器…」，填写：
  协议：http
  IP / 域名：你的服务器 IP 或域名，不含协议和端口
  端口：8080（如 Docker 映射了其他端口，以实际端口为准）
  API 路径：留空
然后点击「保存并连接」。地址会自动保存，最近使用列表可切换服务器。
HTTPS 反向代理请选择 https，通常端口留空；API 路径按代理配置填写。

服务器和界面配置保存在 %APPDATA%\JusicRoomPlayer 目录。
这是包含本地修改的客户端，并非上游原版 Release。

客户端源码：https://github.com/seaworld92/JusicRoomPlayer
重新构建请使用源码仓库中的 build_local_client.ps1，步骤见 README.md。
MPV 构建：https://github.com/shinchiro/mpv-winbuild-cmake/releases/tag/20261012
MPV 上游：https://github.com/mpv-player/mpv
MPV 随本客户端作为独立播放进程运行。
随包保留 LICENSE、THIRD_PARTY_NOTICES.txt 和 build-info.json。
'@
$instructions | Set-Content -LiteralPath (Join-Path $OutputDirectory "使用说明.txt") -Encoding utf8
Compress-Archive -LiteralPath @(
    $outputExe, (Join-Path $OutputDirectory "LICENSE"),
    (Join-Path $OutputDirectory "THIRD_PARTY_NOTICES.txt"),
    (Join-Path $OutputDirectory "build-info.json"), (Join-Path $OutputDirectory "使用说明.txt")
) -DestinationPath $outputZip -Force
Write-Host "Created $outputZip"
