#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载器 - 独立打包入口
自动下载和管理外部依赖
"""

import os
import sys
import subprocess
import threading
import webbrowser
import time
import traceback

APP_NAME = "B站视频下载器"
VERSION = "1.0.0"

def get_app_dir():
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_tools_dir():
    """获取工具目录"""
    return os.path.join(get_app_dir(), 'tools')

def get_yt_dlp_path():
    """获取yt-dlp路径"""
    tools_dir = get_tools_dir()
    yt_dlp_exe = os.path.join(tools_dir, 'yt-dlp.exe')
    if os.path.exists(yt_dlp_exe):
        return yt_dlp_exe
    
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'yt-dlp'
    except:
        pass
    
    return None

def get_ffmpeg_path():
    """获取ffmpeg路径"""
    tools_dir = get_tools_dir()
    ffmpeg_exe = os.path.join(tools_dir, 'ffmpeg.exe')
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe
    
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        if result.returncode == 0:
            return 'ffmpeg'
    except:
        pass
    
    return None

def setup_environment():
    """设置环境变量"""
    tools_dir = get_tools_dir()
    
    if os.path.exists(tools_dir):
        os.environ['PATH'] = tools_dir + os.pathsep + os.environ.get('PATH', '')

def check_dependencies():
    """检查依赖"""
    print("正在检查依赖...")
    
    yt_dlp = get_yt_dlp_path()
    ffmpeg = get_ffmpeg_path()
    
    if yt_dlp:
        print(f"  yt-dlp: 已就绪 ({yt_dlp})")
    else:
        print("  yt-dlp: 未找到")
    
    if ffmpeg:
        print(f"  ffmpeg: 已就绪 ({ffmpeg})")
    else:
        print("  ffmpeg: 未找到")
    
    return yt_dlp is not None and ffmpeg is not None

def main():
    print("=" * 60)
    print(f"{APP_NAME} v{VERSION}")
    print("=" * 60)
    print()
    
    try:
        setup_environment()
        
        deps_ok = check_dependencies()
        
        if not deps_ok:
            print()
            print("警告: 部分依赖缺失，程序可能无法正常工作")
            print()
            print("请确保以下文件存在:")
            tools_dir = get_tools_dir()
            print(f"  - {os.path.join(tools_dir, 'yt-dlp.exe')}")
            print(f"  - {os.path.join(tools_dir, 'ffmpeg.exe')}")
            print()
            print("或确保系统已安装 yt-dlp 和 ffmpeg")
            print()
        
        print("正在启动服务...")
        print()
        
        from app import app
        
        port = 5000
        
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open(f'http://localhost:{port}')
            except Exception as e:
                print(f"无法自动打开浏览器: {e}")
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        print(f"服务已启动，访问地址: http://localhost:{port}")
        print("浏览器将自动打开，如未打开请手动访问上述地址")
        print("按 Ctrl+C 停止服务")
        print("=" * 60)
        print()
        
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
        
    except KeyboardInterrupt:
        print()
        print("服务已停止")
    except ImportError as e:
        print()
        print(f"错误: 缺少必要的Python模块 - {e}")
        print()
        print("这可能是打包问题，请重新下载程序")
    except Exception as e:
        print()
        print(f"错误: {e}")
        print()
        print("详细错误信息:")
        traceback.print_exc()
    finally:
        print()
        print("按回车键退出...")
        try:
            input()
        except:
            pass

if __name__ == '__main__':
    main()
