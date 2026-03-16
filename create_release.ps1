# B站视频下载器 - 发布包制作脚本
$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "B站视频下载器 - 发布包制作工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$RELEASE_DIR = "release\B站视频下载器_v1.0.0"
$DIST_DIR = "dist"

Write-Host "[1/4] 创建发布目录..." -ForegroundColor Yellow
if (Test-Path "release") { Remove-Item -Recurse -Force "release" }
New-Item -ItemType Directory -Force -Path $RELEASE_DIR | Out-Null
New-Item -ItemType Directory -Force -Path "$RELEASE_DIR\tools" | Out-Null
New-Item -ItemType Directory -Force -Path "$RELEASE_DIR\downloads" | Out-Null

Write-Host "[2/4] 复制主程序..." -ForegroundColor Yellow
Copy-Item "$DIST_DIR\B站视频下载器.exe" $RELEASE_DIR -Force

Write-Host "[3/4] 下载外部依赖..." -ForegroundColor Yellow

# 下载 yt-dlp
Write-Host ""
Write-Host "正在下载 yt-dlp..." -ForegroundColor Green
try {
    $ytDlpUrl = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    Invoke-WebRequest -Uri $ytDlpUrl -OutFile "$RELEASE_DIR\tools\yt-dlp.exe" -UseBasicParsing
    Write-Host "yt-dlp 下载成功" -ForegroundColor Green
} catch {
    Write-Host "yt-dlp 下载失败: $_" -ForegroundColor Red
}

# 下载 ffmpeg
Write-Host ""
Write-Host "正在下载 ffmpeg..." -ForegroundColor Green
try {
    $ffmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $ffmpegZip = "$RELEASE_DIR\tools\ffmpeg.zip"
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $ffmpegZip -UseBasicParsing
    
    Write-Host "正在解压 ffmpeg..." -ForegroundColor Green
    Expand-Archive -Path $ffmpegZip -DestinationPath "$RELEASE_DIR\tools" -Force
    
    $ffmpegDir = Get-ChildItem "$RELEASE_DIR\tools" -Filter "ffmpeg-*" -Directory | Select-Object -First 1
    if ($ffmpegDir) {
        Copy-Item "$($ffmpegDir.FullName)\bin\ffmpeg.exe" "$RELEASE_DIR\tools\" -Force
        Copy-Item "$($ffmpegDir.FullName)\bin\ffprobe.exe" "$RELEASE_DIR\tools\" -Force
        Remove-Item $ffmpegDir.FullName -Recurse -Force
    }
    Remove-Item $ffmpegZip -Force
    Write-Host "ffmpeg 下载成功" -ForegroundColor Green
} catch {
    Write-Host "ffmpeg 下载失败: $_" -ForegroundColor Red
}

Write-Host "[4/4] 创建说明文件..." -ForegroundColor Yellow

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "发布包制作完成！" -ForegroundColor Green
Write-Host "输出目录: $RELEASE_DIR" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请将整个文件夹打包发送给其他人使用" -ForegroundColor Yellow
Write-Host ""
