#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载器 - 纯Python实现
使用 requests 和 bilibili API
"""

import os
import sys
import json
import re
import time
import subprocess
from urllib.request import urlopen, Request, build_opener, HTTPCookieProcessor
from urllib.parse import urlencode, parse_qs, urlparse
from http.cookiejar import CookieJar

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
        'Origin': 'https://space.bilibili.com',
    }

def get_user_videos(uid, page=1, page_size=30):
    """获取用户视频列表"""
    url = "https://api.bilibili.com/x/space/wbi/arc/search"
    
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
        
        # 创建 opener 并添加 cookie 支持
        cj = CookieJar()
        opener = build_opener(HTTPCookieProcessor(cj))
        
        response = opener.open(req, timeout=30)
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
    max_pages = 10  # 限制最大页数，避免过多请求
    
    print(f"正在获取用户 {uid} 的视频列表...")
    
    while page <= max_pages:
        videos = get_user_videos(uid, page)
        if not videos:
            break
        
        all_videos.extend(videos)
        print(f"  第 {page} 页: 获取到 {len(videos)} 个视频")
        
        if len(videos) < 30:
            break
        
        page += 1
        time.sleep(0.5)
    
    return all_videos

def sanitize_filename(filename):
    """清理文件名"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    filename = ' '.join(filename.split())
    if len(filename) > 80:
        filename = filename[:80]
    return filename.strip()

def download_video_info(bvid):
    """获取视频下载信息"""
    try:
        # 获取视频信息
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = Request(api_url, headers=get_headers())
        response = urlopen(req, timeout=30)
        data = json.loads(response.read().decode('utf-8'))
        
        if data.get('code') != 0:
            return None
        
        cid = data['data']['cid']
        title = data['data']['title']
        
        # 获取视频下载URL
        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&fnver=0&fnval=16&fourk=1"
        req = Request(play_url, headers=get_headers())
        response = urlopen(req, timeout=30)
        play_data = json.loads(response.read().decode('utf-8'))
        
        if play_data.get('code') != 0:
            return None
        
        # 获取音频URL (如果可用)
        dash_data = play_data['data'].get('dash', {})
        audio_list = dash_data.get('audio', [])
        
        if audio_list:
            # 使用音质最好的音频
            best_audio = max(audio_list, key=lambda x: x.get('id', 0))
            return {
                'title': title,
                'audio_url': best_audio.get('baseUrl') or best_audio.get('base_url'),
                'backup_urls': best_audio.get('backupUrl', []) or best_audio.get('backup_url', [])
            }
        
        # 如果没有dash音频，尝试获取普通视频URL
        durl = play_data['data'].get('durl', [])
        if durl:
            return {
                'title': title,
                'video_url': durl[0].get('url'),
                'title': title
            }
        
        return None
        
    except Exception as e:
        print(f"获取视频信息失败: {e}")
        return None

def download_file(url, output_path, headers, max_retries=3):
    """下载文件"""
    for attempt in range(max_retries):
        try:
            req = Request(url, headers=headers)
            response = urlopen(req, timeout=60)
            
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            
            with open(output_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r      进度: {percent:.1f}%", end='', flush=True)
            
            print()  # 换行
            return True
            
        except Exception as e:
            print(f"\n      下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return False
    
    return False

def download_and_convert(bvid, output_dir, index):
    """下载视频并转换为MP3"""
    print(f"\n  [{index}] 正在获取视频信息: {bvid}")
    
    video_info = download_video_info(bvid)
    if not video_info:
        print(f"      ✗ 无法获取视频信息")
        return False
    
    title = sanitize_filename(video_info['title'])
    mp3_file = os.path.join(output_dir, f"{index:03d}_{title}.mp3")
    
    if os.path.exists(mp3_file):
        print(f"      已存在，跳过: {title[:50]}...")
        return True
    
    print(f"      标题: {title[:60]}...")
    
    # 下载音频
    audio_url = video_info.get('audio_url')
    video_url = video_info.get('video_url')
    
    temp_file = os.path.join(output_dir, f"temp_{bvid}.m4a")
    
    if audio_url:
        # 直接下载音频
        print(f"      正在下载音频...")
        headers = get_headers()
        headers['Referer'] = f'https://www.bilibili.com/video/{bvid}'
        
        if download_file(audio_url, temp_file, headers):
            # 转换为MP3
            print(f"      正在转换为MP3...")
            if convert_to_mp3(temp_file, mp3_file):
                os.remove(temp_file)
                file_size = os.path.getsize(mp3_file) / (1024 * 1024)
                print(f"      ✓ 成功 ({file_size:.1f} MB)")
                return True
            else:
                print(f"      ! 转换失败")
                return False
        else:
            return False
    elif video_url:
        # 下载视频后提取音频
        print(f"      正在下载视频...")
        temp_video = os.path.join(output_dir, f"temp_{bvid}.mp4")
        headers = get_headers()
        headers['Referer'] = f'https://www.bilibili.com/video/{bvid}'
        
        if download_file(video_url, temp_video, headers):
            print(f"      正在提取音频...")
            if convert_to_mp3(temp_video, mp3_file):
                os.remove(temp_video)
                file_size = os.path.getsize(mp3_file) / (1024 * 1024)
                print(f"      ✓ 成功 ({file_size:.1f} MB)")
                return True
            else:
                print(f"      ! 提取失败")
                return False
        else:
            return False
    else:
        print(f"      ✗ 无可用下载链接")
        return False

def convert_to_mp3(input_file, output_file):
    """转换为MP3"""
    try:
        # 尝试使用 ffmpeg
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-y',
            output_file
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0 and os.path.exists(output_file):
            return True
        
        # 如果 ffmpeg 失败，尝试使用 pydub
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(input_file)
            audio.export(output_file, format='mp3', quality='192k')
            return True
        except ImportError:
            pass
        
        return False
        
    except Exception as e:
        print(f"转换错误: {e}")
        return False

def check_ffmpeg():
    """检查 ffmpeg"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except:
        return False

def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生")
    print("=" * 70)
    
    # 检查 ffmpeg
    has_ffmpeg = check_ffmpeg()
    if has_ffmpeg:
        print("✓ ffmpeg 已安装")
    else:
        print("! ffmpeg 未安装，将尝试使用备用方法")
        print("  建议安装 ffmpeg 以获得更好的转换效果")
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 获取视频列表
    videos = get_all_user_videos(USER_ID)
    
    if not videos:
        print("\n未能获取到视频列表")
        print("可能原因：")
        print("1. 网络连接问题")
        print("2. B站API限制")
        print("3. 用户ID错误或用户无公开视频")
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
        
        if not bvid:
            print(f"  [{i}] 跳过: 无BV号")
            fail_count += 1
            continue
        
        if download_and_convert(bvid, OUTPUT_DIR, i):
            success_count += 1
        else:
            fail_count += 1
        
        # 间隔一段时间
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
