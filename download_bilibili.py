#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载并转换为MP3脚本
用于下载薄世宁医生的视频并转换为音频
"""

import os
import sys
import subprocess
import json
import re
from urllib.parse import urljoin
from pathlib import Path

# B站用户空间URL
BILIBILI_SPACE_URL = "https://space.bilibili.com/647411513"
OUTPUT_DIR = "./downloads"

def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"创建输出目录: {OUTPUT_DIR}")

def check_yt_dlp():
    """检查是否安装了yt-dlp"""
    try:
        result = subprocess.run(['yt-dlp', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"yt-dlp 版本: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 未安装 yt-dlp")
        print("请运行: pip install yt-dlp")
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

def get_video_list(space_url):
    """获取用户空间的所有视频列表"""
    print(f"\n正在获取视频列表: {space_url}")
    
    # 使用yt-dlp获取视频列表
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(title)s\t%(id)s\t%(url)s',
        space_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        videos = []
        for line in result.stdout.strip().split('\n'):
            if line and '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 3:
                    title, video_id, url = parts[0], parts[1], parts[2]
                    videos.append({
                        'title': title,
                        'id': video_id,
                        'url': url
                    })
        return videos
    except subprocess.CalledProcessError as e:
        print(f"获取视频列表失败: {e}")
        print(f"错误输出: {e.stderr}")
        return []

def sanitize_filename(filename):
    """清理文件名，移除非法字符"""
    # 移除或替换Windows文件名中的非法字符
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # 限制文件名长度
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()

def download_and_convert(video_info, index, total, has_ffmpeg):
    """下载单个视频并转换为MP3"""
    title = video_info['title']
    video_id = video_info['id']
    url = video_info['url']
    
    safe_title = sanitize_filename(title)
    output_file = os.path.join(OUTPUT_DIR, f"{index:03d}_{safe_title}.mp3")
    
    print(f"\n[{index}/{total}] 正在处理: {title}")
    print(f"    视频ID: {video_id}")
    print(f"    输出文件: {output_file}")
    
    if os.path.exists(output_file):
        print(f"    文件已存在，跳过")
        return True
    
    try:
        if has_ffmpeg:
            # 使用yt-dlp直接下载并转换为MP3
            cmd = [
                'yt-dlp',
                '-f', 'bestaudio/best',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',  # 最佳质量
                '--output', output_file,
                '--embed-thumbnail',  # 嵌入缩略图
                '--add-metadata',     # 添加元数据
                url
            ]
        else:
            # 只下载视频
            cmd = [
                'yt-dlp',
                '-f', 'best',
                '--output', os.path.join(OUTPUT_DIR, f"{index:03d}_{safe_title}.%(ext)s"),
                url
            ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"    ✓ 下载成功")
            return True
        else:
            print(f"    ✗ 下载失败")
            print(f"    错误: {result.stderr}")
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
    if not check_yt_dlp():
        sys.exit(1)
    
    has_ffmpeg = check_ffmpeg()
    
    # 创建输出目录
    ensure_output_dir()
    
    # 获取视频列表
    videos = get_video_list(BILIBILI_SPACE_URL)
    
    if not videos:
        print("未找到任何视频，请检查URL是否正确")
        sys.exit(1)
    
    print(f"\n共找到 {len(videos)} 个视频")
    print("-" * 60)
    
    # 显示视频列表
    for i, video in enumerate(videos, 1):
        print(f"{i}. {video['title']}")
    
    print("-" * 60)
    
    # 询问用户确认
    confirm = input(f"\n是否下载以上 {len(videos)} 个视频并转换为MP3? (y/n): ").lower()
    if confirm != 'y':
        print("已取消下载")
        sys.exit(0)
    
    # 下载并转换
    success_count = 0
    fail_count = 0
    
    for i, video in enumerate(videos, 1):
        if download_and_convert(video, i, len(videos), has_ffmpeg):
            success_count += 1
        else:
            fail_count += 1
    
    # 统计结果
    print("\n" + "=" * 60)
    print("下载完成!")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
