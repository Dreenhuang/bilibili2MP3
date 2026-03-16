#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载器 - 薄世宁医生
使用 you-get (如果可用) 或 yt-dlp
"""

import os
import sys
import re
import json
import time
import subprocess
from urllib.request import urlopen, Request
from html.parser import HTMLParser

OUTPUT_DIR = "./downloads"
USER_ID = "647411513"
USER_SPACE_URL = f"https://space.bilibili.com/{USER_ID}/video"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Referer': 'https://space.bilibili.com',
    }

def fetch_page(url):
    """获取页面内容"""
    try:
        req = Request(url, headers=get_headers())
        response = urlopen(req, timeout=30)
        return response.read().decode('utf-8')
    except Exception as e:
        print(f"获取页面失败: {e}")
        return None

def extract_videos_from_html(html):
    """从HTML中提取视频列表"""
    videos = []
    
    # 尝试从 __INITIAL_STATE__ 中提取
    pattern = r'window\.__INITIAL_STATE__\s*=\s*({.+?});'
    match = re.search(pattern, html)
    
    if match:
        try:
            data = json.loads(match.group(1))
            video_list = data.get('space', {}).get('videoList', [])
            
            for video in video_list:
                videos.append({
                    'bvid': video.get('bvid'),
                    'title': video.get('title', ''),
                    'description': video.get('description', ''),
                    'created': video.get('created', 0)
                })
        except:
            pass
    
    # 如果上面的方法失败，尝试其他模式
    if not videos:
        # 查找 videoList
        pattern = r'"videoList":\s*(\[.+?\])'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                video_list = json.loads(match.group(1))
                for video in video_list:
                    if isinstance(video, dict):
                        videos.append({
                            'bvid': video.get('bvid'),
                            'title': video.get('title', ''),
                            'description': video.get('description', ''),
                            'created': video.get('created', 0)
                        })
            except:
                pass
    
    return videos

def get_all_videos():
    """获取所有视频"""
    print(f"正在获取视频列表: {USER_SPACE_URL}")
    
    html = fetch_page(USER_SPACE_URL)
    if not html:
        return []
    
    videos = extract_videos_from_html(html)
    
    # 尝试获取多页
    page = 2
    max_pages = 10
    
    while page <= max_pages:
        page_url = f"{USER_SPACE_URL}?tid=0&pn={page}"
        html = fetch_page(page_url)
        if not html:
            break
        
        page_videos = extract_videos_from_html(html)
        if not page_videos:
            break
        
        # 检查是否有重复
        existing_bvids = {v['bvid'] for v in videos}
        new_videos = [v for v in page_videos if v['bvid'] not in existing_bvids]
        
        if not new_videos:
            break
        
        videos.extend(new_videos)
        print(f"  第 {page} 页: 找到 {len(new_videos)} 个新视频")
        
        page += 1
        time.sleep(1)
    
    return videos

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    filename = ' '.join(filename.split())
    if len(filename) > 80:
        filename = filename[:80]
    return filename.strip()

def download_with_yt_dlp(bvid, title, output_dir, index):
    """使用 yt-dlp 下载"""
    url = f"https://www.bilibili.com/video/{bvid}"
    safe_title = sanitize_filename(title)
    output_file = os.path.join(output_dir, f"{index:03d}_{safe_title}.mp3")
    
    if os.path.exists(output_file):
        print(f"  [{index}] 已存在，跳过: {safe_title[:50]}...")
        return True
    
    print(f"  [{index}] 正在下载: {safe_title[:60]}...")
    
    try:
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--output', output_file,
            '--no-warnings',
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
        
        if result.returncode == 0:
            file_size = os.path.getsize(output_file) / (1024 * 1024) if os.path.exists(output_file) else 0
            print(f"      ✓ 成功 ({file_size:.1f} MB)")
            return True
        else:
            print(f"      ✗ 失败")
            if result.stderr:
                print(f"      错误: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"      ✗ 超时")
        return False
    except Exception as e:
        print(f"      ✗ 错误: {e}")
        return False

def download_with_you_get(bvid, title, output_dir, index):
    """使用 you-get 下载"""
    url = f"https://www.bilibili.com/video/{bvid}"
    safe_title = sanitize_filename(title)
    output_file = os.path.join(output_dir, f"{index:03d}_{safe_title}.mp3")
    
    if os.path.exists(output_file):
        print(f"  [{index}] 已存在，跳过: {safe_title[:50]}...")
        return True
    
    print(f"  [{index}] 正在下载: {safe_title[:60]}...")
    
    try:
        temp_dir = os.path.join(output_dir, f"temp_{index}")
        ensure_dir(temp_dir)
        
        # 下载视频
        cmd = [
            'you-get',
            '-o', temp_dir,
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=300)
        
        if result.returncode != 0:
            print(f"      ✗ you-get 下载失败")
            return False
        
        # 查找下载的文件
        files = os.listdir(temp_dir)
        if not files:
            print(f"      ✗ 未找到下载的文件")
            return False
        
        video_file = os.path.join(temp_dir, files[0])
        
        # 转换为MP3
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vn',
            '-acodec', 'libmp3lame',
            '-q:a', '2',
            '-y',
            output_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        
        if result.returncode == 0 and os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            print(f"      ✓ 成功 ({file_size:.1f} MB)")
            return True
        else:
            print(f"      ! 转换失败")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"      ✗ 超时")
        return False
    except Exception as e:
        print(f"      ✗ 错误: {e}")
        return False

def check_tool(tool_name):
    """检查工具是否可用"""
    try:
        subprocess.run([tool_name, '--version'], capture_output=True, check=True)
        return True
    except:
        return False

def install_tool(tool_name):
    """安装工具"""
    print(f"尝试安装 {tool_name}...")
    try:
        if tool_name == 'yt-dlp':
            # 尝试直接下载可执行文件
            import urllib.request
            url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
            output_path = os.path.join(os.getcwd(), "yt-dlp.exe")
            
            print(f"  下载 yt-dlp.exe...")
            urllib.request.urlretrieve(url, output_path)
            
            if os.path.exists(output_path):
                print(f"  yt-dlp 已下载到: {output_path}")
                return True
        
        elif tool_name == 'you-get':
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'you-get'], 
                         capture_output=True, check=True)
            return True
            
    except Exception as e:
        print(f"  安装失败: {e}")
    
    return False

def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生")
    print("=" * 70)
    
    # 检查并安装工具
    downloader = None
    
    if check_tool('yt-dlp'):
        print("✓ yt-dlp 已安装")
        downloader = 'yt-dlp'
    elif check_tool('you-get'):
        print("✓ you-get 已安装")
        downloader = 'you-get'
    else:
        print("未找到下载工具，尝试安装 yt-dlp...")
        if install_tool('yt-dlp'):
            downloader = 'yt-dlp'
        elif install_tool('you-get'):
            downloader = 'you-get'
        else:
            print("\n错误: 无法安装下载工具")
            print("请手动安装 yt-dlp 或 you-get:")
            print("  - yt-dlp: https://github.com/yt-dlp/yt-dlp#installation")
            print("  - you-get: pip install you-get")
            sys.exit(1)
    
    # 检查 ffmpeg
    has_ffmpeg = check_tool('ffmpeg')
    if has_ffmpeg:
        print("✓ ffmpeg 已安装")
    else:
        print("! ffmpeg 未安装")
        if downloader == 'you-get':
            print("  you-get 需要 ffmpeg 来转换音频")
            print("  请安装 ffmpeg: https://ffmpeg.org/download.html")
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 获取视频列表
    videos = get_all_videos()
    
    if not videos:
        print("\n未能获取到视频列表")
        print("尝试使用备用方法...")
        
        # 使用 yt-dlp 直接获取列表
        if downloader == 'yt-dlp':
            print("使用 yt-dlp 获取视频列表...")
            try:
                cmd = ['yt-dlp', '--flat-playlist', '--print', '%(title)s\t%(id)s', USER_SPACE_URL]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=60)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '\t' in line:
                            parts = line.split('\t')
                            if len(parts) >= 2:
                                videos.append({
                                    'title': parts[0],
                                    'bvid': parts[1]
                                })
            except Exception as e:
                print(f"  失败: {e}")
    
    if not videos:
        print("\n无法获取视频列表，请检查:")
        print("1. 网络连接")
        print("2. B站是否可访问")
        print("3. 用户ID是否正确")
        sys.exit(1)
    
    print(f"\n共找到 {len(videos)} 个视频")
    print("-" * 70)
    
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
        
        if downloader == 'yt-dlp':
            success = download_with_yt_dlp(bvid, title, OUTPUT_DIR, i)
        else:
            success = download_with_you_get(bvid, title, OUTPUT_DIR, i)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
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
