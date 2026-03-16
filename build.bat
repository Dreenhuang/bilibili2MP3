@echo off
chcp 65001 >nul
echo ========================================
echo B站视频下载器 - 打包脚本
echo ========================================
echo.

echo [1/3] 安装依赖...
pip install flask pyinstaller -q
echo 依赖安装完成

echo.
echo [2/3] 开始打包...
pyinstaller --clean --noconfirm bilibili_downloader.spec

echo.
echo [3/3] 检查打包结果...
if exist "dist\B站视频下载器.exe" (
    echo.
    echo ========================================
    echo 打包成功！
    echo 输出文件: dist\B站视频下载器.exe
    echo ========================================
) else (
    echo.
    echo 打包失败，请检查错误信息
)

echo.
pause
