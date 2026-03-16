#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频批量下载并转MP3 - 智能续传版
自动跳过已存在的文件，修复编码问题
"""

import os
import sys
import subprocess
import json
import re

OUTPUT_DIR = "./downloads"

# 完整的视频BV号列表 (117个)
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
    """确保目录存在"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"创建目录: {path}")


def get_existing_files():
    """获取已存在的文件列表"""
    existing = set()
    if not os.path.exists(OUTPUT_DIR):
        return existing
    
    for filename in os.listdir(OUTPUT_DIR):
        if filename.endswith('.mp3'):
            # 提取序号
            match = re.match(r'(\d+)_.*\.mp3', filename)
            if match:
                existing.add(int(match.group(1)))
    return existing


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


def decode_text(text_bytes):
    """智能解码文本"""
    if isinstance(text_bytes, str):
        return text_bytes
    
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    for encoding in encodings:
        try:
            return text_bytes.decode(encoding)
        except:
            continue
    return text_bytes.decode('utf-8', errors='ignore')


def get_video_title(bvid):
    """获取视频标题"""
    url = f"https://www.bilibili.com/video/{bvid}"
    cmd = ['yt-dlp', '--print', '%(title)s', '--no-warnings', url]
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            return decode_text(result.stdout).strip()
    except:
        pass
    return None


def download_audio(bvid, index, total):
    """下载视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    
    # 先尝试获取标题
    print(f"[{index}/{total}] 处理: {bvid}")
    title = get_video_title(bvid)
    
    if title:
        safe_title = sanitize_filename(title)
        output_file = os.path.join(OUTPUT_DIR, f"{index:03d}_{safe_title}.mp3")
    else:
        # 如果获取标题失败，使用BV号作为文件名
        output_file = os.path.join(OUTPUT_DIR, f"{index:03d}_{bvid}.mp3")
    
    # 检查文件是否已存在（包括任何可能的文件名）
    existing_files = [f for f in os.listdir(OUTPUT_DIR) 
                     if f.startswith(f"{index:03d}_") and f.endswith('.mp3')]
    
    if existing_files:
        existing_file = os.path.join(OUTPUT_DIR, existing_files[0])
        file_size = os.path.getsize(existing_file) / (1024 * 1024)
        print(f"    ✓ 已存在 ({file_size:.1f} MB): {existing_files[0][:60]}")
        return True, "exists"
    
    print(f"    标题: {title[:50]}..." if title else f"    标题: {bvid}")
    print(f"    正在下载...")
    
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
        
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        
        if result.returncode == 0:
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"    ✓ 成功 ({file_size:.1f} MB)")
                return True, "success"
            else:
                print(f"    ✗ 文件未生成")
                return False, "no_file"
        else:
            stderr = decode_text(result.stderr) if result.stderr else ""
            print(f"    ✗ 下载失败")
            if stderr:
                print(f"    错误: {stderr[:150]}")
            return False, "download_failed"
            
    except subprocess.TimeoutExpired:
        print(f"    ✗ 下载超时")
        return False, "timeout"
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return False, "error"


def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生视频转MP3 (智能续传版)")
    print("=" * 70)
    
    # 检查磁盘空间
    try:
        import shutil
        total, used, free = shutil.disk_usage(OUTPUT_DIR if os.path.exists(OUTPUT_DIR) else ".")
        free_gb = free / (1024**3)
        print(f"磁盘剩余空间: {free_gb:.2f} GB")
        if free_gb < 2:
            print("警告: 磁盘空间可能不足!")
            confirm = input("是否继续? (y/n): ").strip().lower()
            if confirm != 'y':
                return
    except Exception as e:
        print(f"无法检查磁盘空间: {e}")
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 获取已存在的文件
    existing = get_existing_files()
    print(f"\n总视频数: {len(VIDEO_LIST)}")
    print(f"已下载: {len(existing)}")
    print(f"待下载: {len(VIDEO_LIST) - len(existing)}")
    print("-" * 70)
    
    # 统计
    success_count = 0
    fail_count = 0
    skip_count = len(existing)
    failed_bvids = []
    
    # 下载视频
    for i, bvid in enumerate(VIDEO_LIST, 1):
        # 检查是否已存在
        if i in existing:
            continue
        
        success, status = download_audio(bvid, i, len(VIDEO_LIST))
        
        if success:
            success_count += 1
        else:
            fail_count += 1
            failed_bvids.append((i, bvid, status))
        
        print()
    
    # 最终统计
    print("=" * 70)
    print("下载完成!")
    print(f"总计: {len(VIDEO_LIST)}")
    print(f"已存在: {skip_count}")
    print(f"新下载成功: {success_count}")
    print(f"失败: {fail_count}")
    
    if failed_bvids:
        print("\n失败的视频:")
        for idx, bvid, status in failed_bvids:
            print(f"  [{idx}] {bvid} - {status}")
    
    print(f"\n输出目录: {os.path.abspath(OUTPUT_DIR)}")
    
    # 列出所有下载的文件
    mp3_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.mp3')]
    print(f"目录中共有 {len(mp3_files)} 个 MP3 文件")
    print("=" * 70)


if __name__ == "__main__":
    main()
