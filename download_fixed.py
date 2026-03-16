#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频批量下载并转MP3 - 修复版
修复编码问题，添加代理支持
"""

import os
import sys
import subprocess
import json

OUTPUT_DIR = "./downloads"

# 视频BV号列表
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
    
    # 尝试多种编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
    
    for encoding in encodings:
        try:
            return text_bytes.decode(encoding)
        except:
            continue
    
    # 如果都失败，使用 utf-8 忽略错误
    return text_bytes.decode('utf-8', errors='ignore')

def get_video_info(bvid, proxy=None):
    """获取视频信息"""
    url = f"https://www.bilibili.com/video/{bvid}"
    
    cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
    
    # 添加代理
    if proxy:
        cmd.extend(['--proxy', proxy])
    
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            return None
        
        # 解码输出
        stdout = decode_text(result.stdout)
        
        # 解析JSON
        try:
            info = json.loads(stdout)
            return {
                'title': info.get('title', bvid),
                'uploader': info.get('uploader', ''),
                'duration': info.get('duration', 0),
            }
        except:
            return None
            
    except Exception as e:
        print(f"获取信息失败: {e}")
        return None

def download_audio(bvid, index, total, proxy=None):
    """下载视频音频"""
    url = f"https://www.bilibili.com/video/{bvid}"
    
    # 获取视频信息
    print(f"[{index}/{total}] 获取视频信息: {bvid}")
    info = get_video_info(bvid, proxy)
    
    if info:
        title = info['title']
    else:
        title = f"视频_{bvid}"
    
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
        # 使用 yt-dlp 下载
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',
            '--output', output_file,
            '--no-warnings',
        ]
        
        # 添加代理
        if proxy:
            cmd.extend(['--proxy', proxy])
        
        cmd.append(url)
        
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        
        # 解码错误输出
        stderr = decode_text(result.stderr) if result.stderr else ""
        
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
            if stderr:
                print(f"    错误: {stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"    ✗ 下载超时")
        return False
    except Exception as e:
        print(f"    ✗ 错误: {e}")
        return False

def main():
    print("=" * 70)
    print("B站视频下载器 - 薄世宁医生视频转MP3 (修复版)")
    print("=" * 70)
    
    # 检查磁盘空间
    try:
        stat = os.statvfs(OUTPUT_DIR) if hasattr(os, 'statvfs') else None
        if stat:
            free_space = stat.f_frsize * stat.f_bavail / (1024**3)
            print(f"剩余磁盘空间: {free_space:.2f} GB")
            if free_space < 1:
                print("警告: 磁盘空间不足!")
    except:
        pass
    
    # 创建输出目录
    ensure_dir(OUTPUT_DIR)
    
    # 代理设置 (可选)
    proxy = None
    # proxy = "http://127.0.0.1:7890"  # 如果需要代理，取消注释并修改
    
    if proxy:
        print(f"使用代理: {proxy}")
    
    videos = VIDEO_LIST
    print(f"\n共 {len(videos)} 个视频")
    print("-" * 70)
    print("开始下载...")
    print()
    
    # 下载视频
    success_count = 0
    fail_count = 0
    skipped_count = 0
    
    for i, bvid in enumerate(videos, 1):
        result = download_audio(bvid, i, len(videos), proxy)
        if result:
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
