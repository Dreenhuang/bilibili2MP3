@echo off
chcp 65001 >nul
echo ========================================
echo B站视频下载器 - 发布包制作工具
echo ========================================
echo.

set RELEASE_DIR=release\B站视频下载器_v1.0.0
set DIST_DIR=dist

echo [1/4] 创建发布目录...
if exist "release" rmdir /s /q "release"
mkdir "%RELEASE_DIR%"
mkdir "%RELEASE_DIR%\tools"
mkdir "%RELEASE_DIR%\downloads"

echo [2/4] 复制主程序...
copy "%DIST_DIR%\B站视频下载器.exe" "%RELEASE_DIR%\" >nul

echo [3/4] 下载外部依赖...
echo.
echo 正在下载 yt-dlp...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile '%RELEASE_DIR%\tools\yt-dlp.exe'}"
if exist "%RELEASE_DIR%\tools\yt-dlp.exe" (
    echo yt-dlp 下载成功
) else (
    echo yt-dlp 下载失败，请手动下载
)

echo.
echo 正在下载 ffmpeg...
powershell -Command "& {$url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'; $output = '%RELEASE_DIR%\tools\ffmpeg.zip'; Invoke-WebRequest -Uri $url -OutFile $output; Expand-Archive -Path $output -DestinationPath '%RELEASE_DIR%\tools' -Force; $ffmpegDir = Get-ChildItem '%RELEASE_DIR%\tools' -Filter 'ffmpeg-*' -Directory | Select-Object -First 1; Copy-Item \"$($ffmpegDir.FullName)\bin\ffmpeg.exe\" '%RELEASE_DIR%\tools\' -Force; Copy-Item \"$($ffmpegDir.FullName)\bin\ffprobe.exe\" '%RELEASE_DIR%\tools\' -Force; Remove-Item $ffmpegDir.FullName -Recurse -Force; Remove-Item $output -Force}"
if exist "%RELEASE_DIR%\tools\ffmpeg.exe" (
    echo ffmpeg 下载成功
) else (
    echo ffmpeg 下载失败，请手动下载
)

echo [4/4] 创建说明文件...
echo B站视频下载器 v1.0.0 > "%RELEASE_DIR%\使用说明.txt"
echo ======================================== >> "%RELEASE_DIR%\使用说明.txt"
echo. >> "%RELEASE_DIR%\使用说明.txt"
echo 使用方法: >> "%RELEASE_DIR%\使用说明.txt"
echo 1. 双击运行 "B站视频下载器.exe" >> "%RELEASE_DIR%\使用说明.txt"
echo 2. 程序会自动打开浏览器 >> "%RELEASE_DIR%\使用说明.txt"
echo 3. 输入B站用户空间地址或视频链接 >> "%RELEASE_DIR%\使用说明.txt"
echo 4. 选择要下载的视频，点击下载 >> "%RELEASE_DIR%\使用说明.txt"
echo. >> "%RELEASE_DIR%\使用说明.txt"
echo 注意事项: >> "%RELEASE_DIR%\使用说明.txt"
echo - 首次运行可能需要等待几秒钟 >> "%RELEASE_DIR%\使用说明.txt"
echo - 下载的文件保存在 downloads 文件夹 >> "%RELEASE_DIR%\使用说明.txt"
echo - 如遇网络问题，请在设置中配置代理 >> "%RELEASE_DIR%\使用说明.txt"
echo. >> "%RELEASE_DIR%\使用说明.txt"
echo 目录结构: >> "%RELEASE_DIR%\使用说明.txt"
echo ├── B站视频下载器.exe  (主程序) >> "%RELEASE_DIR%\使用说明.txt"
echo ├── tools/             (工具目录) >> "%RELEASE_DIR%\使用说明.txt"
echo │   ├── yt-dlp.exe     (视频下载工具) >> "%RELEASE_DIR%\使用说明.txt"
echo │   ├── ffmpeg.exe     (音视频转换工具) >> "%RELEASE_DIR%\使用说明.txt"
echo │   └── ffprobe.exe    (音视频分析工具) >> "%RELEASE_DIR%\使用说明.txt"
echo └── downloads/         (下载目录) >> "%RELEASE_DIR%\使用说明.txt"

echo.
echo ========================================
echo 发布包制作完成！
echo 输出目录: %RELEASE_DIR%
echo ========================================
echo.
echo 请将整个文件夹打包发送给其他人使用
echo.
pause
