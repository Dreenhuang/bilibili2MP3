#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载脚本 - 使用 you-get
用于下载薄世宁医生的视频并转换为音频
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path

# B站用户空间URL
BILIBILI_SPACE_URL = "https://space.bilibili.com/647411513"
OUTPUT_DIR = "./downloads"

def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建输出目录: {OUTPUT_DIR}")

def check_you_get():
    """检查是否安装了you-get"""
    try:
        result = subprocess.run(['you-get', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"you-get 版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未安装 you-get")
        print("请运行: pip install you-get")
        return False

def check_ffmpeg():
    """检查是否安装了ffmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, check=True)
        version_line = result.stdout.split('\n')[0]
        print(f"FFmpeg: {version_line}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("警告: 未安装 ffmpeg，将只下载视频不转换为MP3")
        print("如需转换音频，请安装 ffmpeg: https://ffmpeg.org/download.html")
        return False

def get_video_list_with_you_get(space_url):
    """使用you-get获取视频列表"""
    print(f"\n正在获取视频列表: {space_url}")
    
    # 使用you-get获取视频列表
    cmd = [
        'you-get',
        '--playlist',
        '--json',
        space_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # 解析输出获取视频信息
        videos = []
        # you-get 输出格式解析
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if 'http' in line and 'bilibili' in line:
                # 尝试提取URL和标题
                match = re.search(r'(https?://[^\s]+)', line)
                if match:
                    url = match.group(1)
                    # 清理URL
                    url = url.split('?')[0] if '?' in url else url
                    videos.append({
                        'title': f'video_{len(videos)+1}',
                        'url': url
                    })
        
        return videos
    except Exception as e:
        print(f"获取视频列表失败: {e}")
        return []

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()

def convert_to_mp3(video_path, output_path):
    """将视频转换为MP3"""
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 不处理视频
            '-acodec', 'libmp3lame',
            '-q:a', '0',  # 最高质量
            '-y',  # 覆盖已存在文件
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def download_video_you_get(url, output_dir, index):
    """使用you-get下载单个视频"""
    print(f"\n[{index}] 正在下载: {url}")
    
    try:
        # 先获取视频信息
        info_cmd = ['you-get', '--json', url]
        info_result = subprocess.run(info_cmd, capture_output=True, text=True, encoding='utf-8')
        
        title = f"video_{index}"
        try:
            info = json.loads(info_result.stdout)
            if 'title' in info:
                title = sanitize_filename(info['title'])
        except:
            pass
        
        output_file = os.path.join(output_dir, f"{index:03d}_{title}.mp3")
        
        if os.path.exists(output_file):
            print(f"    文件已存在，跳过: {output_file}")
            return True
        
        # 下载视频
        download_cmd = [
            'you-get',
            '-o', output_dir,
            '-O', f"temp_{index:03d}",
            url
        ]
        
        result = subprocess.run(download_cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            # 查找下载的视频文件
            temp_files = [f for f in os.listdir(output_dir) if f.startswith(f"temp_{index:03d}")]
            if temp_files:
                video_file = os.path.join(output_dir, temp_files[0])
                # 转换为MP3
                if convert_to_mp3(video_file, output_file):
                    print(f"    ✓ 下载并转换成功: {output_file}")
                    # 删除原视频文件
                    os.remove(video_file)
                    return True
                else:
                    print(f"    ! 视频下载成功但转换失败，保留视频文件: {video_file}")
                    return False
        
        print(f"    ✗ 下载失败")
        if result.stderr:
            print(f"    错误: {result.stderr[:200]}")
        return False
        
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("B站视频下载工具 - 薄世宁医生视频")
    print("=" * 60)
    
    # 检查依赖
    if not check_you_get():
        print("\n尝试安装 you-get...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'you-get'], 
                         capture_output=True, check=True)
            print("you-get 安装成功")
        except:
            print("you-get 安装失败，请手动安装: pip install you-get")
            sys.exit(1)
    
    has_ffmpeg = check_ffmpeg()
    
    # 创建输出目录
    ensure_output_dir()
    
    # 获取视频列表
    print("\n正在获取视频列表，请稍候...")
    
    # 由于you-get获取playlist可能有限制，我们使用另一种方式
    # 直接下载用户空间页面并解析
    videos = []
    
    # 尝试使用you-get下载playlist
    cmd = ['you-get', '--playlist', BILIBILI_SPACE_URL]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        print("you-get 输出:")
        print(result.stdout)
        print(result.stderr)
    except Exception as e:
        print(f"获取列表出错: {e}")
    
    # 如果没有获取到视频，提示用户
    if not videos:
        print("\n注意: 自动获取视频列表可能需要登录或其他处理")
        print("您可以手动提供视频URL列表，或尝试其他方式")
        
        # 尝试直接下载单个视频作为示例
        sample_url = "https://www.bilibili.com/video/BV1xx411c7mD"  # 示例URL
        print(f"\n尝试下载示例视频进行测试...")
        download_video_you_get(sample_url, OUTPUT_DIR, 1)
    
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
