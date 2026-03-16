#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载器 - 薄世宁医生
使用 requests 获取视频列表，使用 you-get 下载
"""

import os
import sys
import json
import re
import subprocess
import time
from urllib.request import urlopen, Request
from urllib.parse import urlencode

OUTPUT_DIR = "./downloads"
USER_ID = "647411513"  # 薄世宁医生的B站UID

def ensure_dir(path):
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")

def get_headers():
    """获取请求头"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://space.bilibili.com',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

def get_user_videos(uid, page=1, page_size=30):
    """获取用户视频列表"""
    url = f"https://api.bilibili.com/x/space/wbi/arc/search"
    
    params = {
        'mid': uid,
        'ps': page_size,
        'tid': 0,
        'pn': page,
        'keyword': '',
        'order': 'pubdate',
        'platform': 'web',
        'web_location': '1550101',
        'order_avoided': 'true'
    }
    
    try:
        query_string = urlencode(params)
        full_url = f"{url}?{query_string}"
        
        req = Request(full_url, headers=get_headers())
        response = urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        if data.get('code') == 0:
            return data['data']['list']['vlist']
        else:
            print(f"API返回错误: {data.get('message', '未知错误')}")
            return []
    except Exception as e:
        print(f"获取视频列表失败: {e}")
        return []

def get_all_user_videos(uid):
    """获取用户所有视频"""
    all_videos = []
    page = 1
    
    print(f"正在获取用户 {uid} 的视频列表...")
    
    while True:
        videos = get_user_videos(uid, page)
        if not videos:
            break
        
        all_videos.extend(videos)
        print(f"  第 {page} 页: 获取到 {len(videos)} 个视频")
        
        if len(videos) < 30:
            break
        
        page += 1
        time.sleep(0.5)  # 避免请求过快
    
    return all_videos

def sanitize_filename(filename):
    """清理文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    filename = ' '.join(filename.split())  # 合并多个空格
    if len(filename) > 100:
        filename = filename[:100]
    return filename.strip()

def download_with_you_get(bvid, title, output_dir, index):
    """使用 you-get 下载视频并转换为MP3"""
    url = f"https://www.bilibili.com/video/{bvid}"
    safe_title = sanitize_filename(title)
    
    # 输出文件名
    mp3_file = os.path.join(output_dir, f"{index:03d}_{safe_title}.mp3")
    
    if os.path.exists(mp3_file):
        print(f"  [{index}] 已存在，跳过: {safe_title[:50]}...")
        return True
    
    print(f"  [{index}] 正在下载: {safe_title[:60]}...")
    print(f"      URL: {url}")
    
    try:
        # 先下载视频到临时文件
        temp_video = os.path.join(output_dir, f"temp_{bvid}.mp4")
        
        # 使用 you-get 下载
        cmd = [
            'you-get',
            '-o', output_dir,
            '-O', f"temp_{bvid}",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
        
        if result.returncode != 0:
            print(f"      ✗ you-get 下载失败")
            if "you-get" in str(result.stderr):
                print(f"      错误: {result.stderr[:200]}")
            return False
        
        # 查找下载的文件
        downloaded_files = [f for f in os.listdir(output_dir) if f.startswith(f"temp_{bvid}")]
        if not downloaded_files:
            print(f"      ✗ 未找到下载的文件")
            return False
        
        video_file = os.path.join(output_dir, downloaded_files[0])
        
        # 转换为 MP3
        print(f"      正在转换为 MP3...")
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-y',
            mp3_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0 and os.path.exists(mp3_file):
            # 删除原视频文件
            os.remove(video_file)
            file_size = os.path.getsize(mp3_file) / (1024 * 1024)  # MB
            print(f"      ✓ 成功 ({file_size:.1f} MB)")
            return True
        else:
            print(f"      ! 转换失败，保留视频文件")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"      ✗ 下载超时")
        return False
    except Exception as e:
        print(f"      ✗ 错误: {e}")
        return False

def check_ffmpeg():
    """检查 ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

def check_you_get():
    """检查 you-get"""
    try:
        subprocess.run(['you-get', '--version'], capture_output=True, check=True)
        return True
    except:
        return False

def install_you_get():
    """安装 you-get"""
    print("正在安装 you-get...")
    try:
        # 尝试多种安装方式
        cmds = [
            [sys.executable, '-m', 'pip', 'install', 'you-get', '-i', 'https://pypi.tuna.tsinghua.edu.cn/simple'],
            [sys.executable, '-m', 'pip', 'install', 'you-get'],
            ['pip', 'install', 'you-get'],
        ]
        
        for cmd in cmds:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print("you-get 安装成功")
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        print(f"安装失败: {e}")
        return False

def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生")
    print("=" * 70)
    
    # 检查依赖
    if not check_ffmpeg():
        print("\n错误: 未找到 ffmpeg")
        print("请先安装 ffmpeg: https://ffmpeg.org/download.html")
        print("安装后确保 ffmpeg 在系统 PATH 中")
        sys.exit(1)
    
    print("✓ ffmpeg 已安装")
    
    if not check_you_get():
        print("\n未找到 you-get，尝试安装...")
        if not install_you_get():
            print("\n错误: you-get 安装失败")
            print("请手动安装: pip install you-get")
            sys.exit(1)
    
    print("✓ you-get 已安装")
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 获取视频列表
    videos = get_all_user_videos(USER_ID)
    
    if not videos:
        print("\n未能获取到视频列表，可能原因：")
        print("1. 网络连接问题")
        print("2. B站API限制")
        print("3. 用户ID错误")
        sys.exit(1)
    
    print(f"\n共找到 {len(videos)} 个视频")
    print("-" * 70)
    
    # 显示视频列表
    for i, video in enumerate(videos, 1):
        title = video.get('title', '未知标题')
        print(f"{i}. {title}")
    
    print("-" * 70)
    
    # 确认下载
    confirm = input(f"\n是否下载以上 {len(videos)} 个视频并转换为MP3? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        sys.exit(0)
    
    # 下载视频
    success_count = 0
    fail_count = 0
    
    for i, video in enumerate(videos, 1):
        bvid = video.get('bvid')
        title = video.get('title', f'video_{i}')
        
        if not bvid:
            print(f"  [{i}] 跳过: 无BV号")
            fail_count += 1
            continue
        
        if download_with_you_get(bvid, title, OUTPUT_DIR, i):
            success_count += 1
        else:
            fail_count += 1
        
        # 间隔一段时间，避免请求过快
        if i < len(videos):
            time.sleep(2)
    
    # 统计
    print("\n" + "=" * 70)
    print("下载完成!")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
