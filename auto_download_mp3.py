#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频批量下载并转MP3 - 薄世宁医生 (自动确认版)
使用 yt-dlp 下载音频
"""

import os
import sys
import subprocess

OUTPUT_DIR = "./downloads"
USER_ID = "647411513"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")

def get_video_list():
    """获取视频列表"""
    print("正在获取视频列表...")
    
    cmd = [
        'yt-dlp',
        '--flat-playlist',
        '--print', '%(title)s\t%(id)s',
        f'https://space.bilibili.com/{USER_ID}'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        
        # 尝试解码输出
        try:
            stdout = result.stdout.decode('utf-8', errors='ignore')
        except:
            try:
                stdout = result.stdout.decode('gbk', errors='ignore')
            except:
                stdout = str(result.stdout)
        
        videos = []
        for line in stdout.strip().split('\n'):
            if '\t' in line:
                parts = line.split('\t')
                if len(parts) >= 2:
                    title, bvid = parts[0], parts[1]
                    # 过滤掉 NA 标题
                    if bvid and bvid.startswith('BV'):
                        videos.append({
                            'title': title if title != 'NA' else f'视频_{bvid}',
                            'bvid': bvid
                        })
        
        return videos
    except Exception as e:
        print(f"获取视频列表失败: {e}")
        return []

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    filename = ' '.join(filename.split())
    # 限制长度
    if len(filename) > 80:
        filename = filename[:80]
    return filename.strip()

def download_audio(bvid, title, index, total):
    """下载视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    safe_title = sanitize_filename(title)
    output_file = os.path.join(OUTPUT_DIR, f"{index:03d}_{safe_title}.mp3")
    
    # 检查文件是否已存在
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"[{index}/{total}] ✓ 已存在 ({file_size:.1f} MB): {safe_title[:50]}...")
        return True
    
    print(f"[{index}/{total}] 正在下载: {safe_title[:60]}...")
    print(f"    BV号: {bvid}")
    
    try:
        # 使用 yt-dlp 下载最佳音频并转换为 MP3
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # 最佳质量
            '--output', output_file,
            '--no-warnings',
            '--progress',
            '--newline',
            url
        ]
        
        # 使用 GBK 编码处理输出，避免中文乱码问题
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        
        # 尝试解码输出
        try:
            stdout = result.stdout.decode('utf-8', errors='ignore')
            stderr = result.stderr.decode('utf-8', errors='ignore')
        except:
            try:
                stdout = result.stdout.decode('gbk', errors='ignore')
                stderr = result.stderr.decode('gbk', errors='ignore')
            except:
                stdout = str(result.stdout)
                stderr = str(result.stderr)
        
        if result.returncode == 0:
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"    ✓ 成功 ({file_size:.1f} MB)")
                return True
            else:
                print(f"    ✗ 文件未生成")
                return False
        else:
            print(f"    ✗ 下载失败")
            # 显示错误信息
            if stderr:
                # 只显示前200个字符
                error_msg = stderr[:200].replace('\n', ' ')
                print(f"    错误: {error_msg}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"    ✗ 下载超时")
        return False
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return False

def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生视频转MP3")
    print("=" * 70)
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 获取视频列表
    videos = get_video_list()
    
    if not videos:
        print("未能获取到视频列表")
        sys.exit(1)
    
    print(f"\n共找到 {len(videos)} 个视频")
    print("-" * 70)
    
    # 显示前10个视频
    for i, video in enumerate(videos[:10], 1):
        print(f"{i}. {video['title']}")
    
    if len(videos) > 10:
        print(f"... 还有 {len(videos) - 10} 个视频")
    
    print("-" * 70)
    print(f"\n自动开始下载 {len(videos)} 个视频...")
    print()
    
    # 下载视频
    success_count = 0
    fail_count = 0
    
    for i, video in enumerate(videos, 1):
        if download_audio(video['bvid'], video['title'], i, len(videos)):
            success_count += 1
        else:
            fail_count += 1
        
        print()
    
    # 统计
    print("=" * 70)
    print("下载完成!")
    print(f"总计: {len(videos)}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"输出目录: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 70)

if __name__ == "__main__":
    main()
