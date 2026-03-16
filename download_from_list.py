#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频批量下载并转MP3 - 从已知列表下载
"""

import os
import sys
import subprocess

OUTPUT_DIR = "./downloads"

# 已知的视频BV号列表（从之前的获取结果）
VIDEO_LIST = [
    "BV12zPQzHEq7", "BV1iBPzzeE7K", "BV1djPLzhEv4", "BV1wuA1zREv5",
    "BV1NxfYBDEQL", "BV1PRfsBfEbr", "BV1MrFSzBEj1", "BV18BFSz6E5P",
    "BV1o5FozuEsT", "BV1cscTzVEmD", "BV1CUFPzKEzk", "BV1nRFPzwE8V",
    "BV1vV6JB2Enf", "BV19gzaBVEwA", "BV1XxzbBvEjA", "BV1rHkYBvEhk",
    "BV1UMkYB5EFM", "BV1pRroBTESA", "BV1V1rhBEE1b", "BV1NjiDB3EM4",
    "BV1hnifB6Ecd", "BV1mqikB9Ecr", "BV1LJvsBJESF", "BV1tNBSB2EWU",
    "BV12EBHBPEiW", "BV1NDmrBjEXi", "BV1QJmkBxEnH", "BV1fN2mB7Ed9",
    "BV16PSeBHEWk", "BV1HkSpBoEKk", "BV1hvS6BsEwC", "BV15xS7BAEoy",
    "BV1sVUSBqEdR", "BV1V7UDB9Efp", "BV1XTy7B2Ehi", "BV1ywCYBGEqR",
    "BV1ojkmBNE2m", "BV1wNkmBCEC7", "BV1N316BTECn", "BV1A516BNEfM",
    "BV12gy1BEE3t", "BV1ZGs1zME7x", "BV19Hs1zwE3X", "BV1KhsuznEQT",
    "BV18PsgzoE1L", "BV1SJn2zmEwY", "BV1C64Wz4E7s", "BV13sx6zUE6q",
    "BV1GWx6zJE5c", "BV16aHNzpEjX", "BV1nnHcz5ER7", "BV1zhn9zWEkP",
    "BV1CSJDzSEBR", "BV112JDzQEE6", "BV1x7JfzyEfd", "BV1GCpCzpEoC",
    "BV1A9pNzwErA", "BV1NDpNzPEWv", "BV1VZaCzLEHA", "BV1a5aEzBEhA",
    "BV1Q5ekzkEpS", "BV1YVekzVEJk", "BV1sPeTzYEbH", "BV1TkYWzmE9r",
    "BV127bzzLEkW", "BV1PrtXz5EAF", "BV1WVtBzKExN", "BV1VFtJzAErw",
    "BV1WztEz2Eut", "BV13mtgzuEdK", "BV1TP8DzmEUR", "BV1JB8LzqE7w",
    "BV17bgJzhEvh", "BV1jagJzbE7C", "BV1GNu4zTE4a", "BV1XJuWzFEFg",
    "BV1HFuvzkEtf", "BV141GEzmEDn", "BV1fv3rzfEev", "BV1w53YzGEHz",
    "BV1FzgUz7E5r", "BV14CK3z5E4Y", "BV1U6K3zjE9D", "BV1U4KxzHEg2",
    "BV1T1NjzsE7j", "BV11WNLzSEqp", "BV1vqJez9Ejr", "BV1AwEQzUEdZ",
    "BV1bcEvz5E2r", "BV1UwEvzCEWn", "BV1T3EjzREkP", "BV1Hn5GztERY",
    "BV1HaVyzjEnj", "BV1XDGSzyEbs", "BV1c4jPzuEgu", "BV16ZLxzYEvJ",
    "BV1arLTzaE7v", "BV1YBLTzeEUj", "BV1sKonYUExZ", "BV1HGonYyEy9",
    "BV1CKdGYXE8c", "BV1UadHYdEoj", "BV1NRRyYjEg2", "BV1C5ZJY7Edj",
    "BV1UNZJYWErP", "BV1R6ZGYjEZ2", "BV1NHZGY8ETB", "BV1ZWoeYCEXP",
    "BV1uuXVYfEoX", "BV19tDfYxERx", "BV1PrQ7Y8Emp", "BV1B2R3YkE4a",
    "BV1rVBqYVEE3", "BV1P6moYfENQ", "BV1c64y1V7TF", "BV1V54y1J7DR",
    "BV1vK4y1u7ki"
]

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")

def sanitize_filename(filename):
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    filename = ' '.join(filename.split())
    if len(filename) > 80:
        filename = filename[:80]
    return filename.strip()

def get_video_title(bvid):
    """获取视频标题"""
    try:
        cmd = [
            'yt-dlp',
            '--print', '%(title)s',
            '--no-warnings',
            f'https://www.bilibili.com/video/{bvid}'
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        try:
            title = result.stdout.decode('utf-8', errors='ignore').strip()
        except:
            title = result.stdout.decode('gbk', errors='ignore').strip()
        return title if title else bvid
    except:
        return bvid

def download_audio(bvid, index, total):
    """下载视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    
    # 获取标题
    print(f"[{index}/{total}] 获取视频信息: {bvid}")
    title = get_video_title(bvid)
    safe_title = sanitize_filename(title)
    output_file = os.path.join(OUTPUT_DIR, f"{index:03d}_{safe_title}.mp3")
    
    # 检查文件是否已存在
    if os.path.exists(output_file):
        file_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"    ✓ 已存在 ({file_size:.1f} MB): {safe_title[:50]}...")
        return True
    
    print(f"    标题: {safe_title[:60]}...")
    print(f"    正在下载...")
    
    try:
        # 使用 yt-dlp 下载最佳音频并转换为 MP3
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
        
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        
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
            try:
                stderr = result.stderr.decode('utf-8', errors='ignore')[:200]
            except:
                stderr = str(result.stderr)[:200]
            if stderr:
                print(f"    错误: {stderr}")
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
    
    videos = VIDEO_LIST
    print(f"\n共 {len(videos)} 个视频")
    print("-" * 70)
    print("自动开始下载...")
    print()
    
    # 下载视频
    success_count = 0
    fail_count = 0
    
    for i, bvid in enumerate(videos, 1):
        if download_audio(bvid, i, len(videos)):
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
