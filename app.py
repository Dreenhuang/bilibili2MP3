#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站视频下载器 - Web UI 版本
使用 Flask 提供后端 API
"""

import os
import sys
import json
import re
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__, template_folder='templates', static_folder='static')

CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'download_path': './downloads',
    'audio_quality': '0',
    'audio_format': 'mp3',
    'proxy': '',
    'concurrent_downloads': 1,
    'auto_rename': True,
    'theme': 'dark',
    'language': 'zh-CN',
    'notification_sound': True,
    'auto_check_update': True
}

download_tasks = {}
download_history = []


def get_app_dir():
    """获取应用目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def extract_user_id(input_str):
    """从输入中提取用户ID"""
    input_str = input_str.strip()
    
    if input_str.isdigit():
        return input_str
    
    match = re.search(r'space\.bilibili\.com/(\d+)', input_str)
    if match:
        return match.group(1)
    
    match = re.search(r'/(\d{5,})', input_str)
    if match:
        return match.group(1)
    
    return input_str


def extract_bvid(input_str):
    """从输入中提取BV号"""
    input_str = input_str.strip()
    
    if input_str.startswith('BV') and len(input_str) >= 10:
        return input_str
    
    match = re.search(r'(BV[a-zA-Z0-9]+)', input_str)
    if match:
        return match.group(1)
    
    return input_str


def load_config():
    """加载配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_video_info(bvid):
    """获取视频信息"""
    bvid = extract_bvid(bvid)
    url = f"https://www.bilibili.com/video/{bvid}"
    try:
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            info = json.loads(result.stdout.decode('utf-8', errors='ignore'))
            return {
                'title': info.get('title', ''),
                'uploader': info.get('uploader', ''),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'view_count': info.get('view_count', 0),
                'like_count': info.get('like_count', 0),
                'upload_date': info.get('upload_date', '')
            }
    except Exception as e:
        print(f"获取视频信息失败: {e}")
    return None


def get_user_videos(user_id):
    """获取用户所有视频"""
    user_id = extract_user_id(user_id)
    print(f"正在获取用户 {user_id} 的视频列表...")
    
    cookies_file = os.path.join(get_app_dir(), 'bilibili_cookies.txt')
    
    base_cmd = ['yt-dlp', '--flat-playlist']
    if os.path.exists(cookies_file):
        base_cmd.extend(['--cookies', cookies_file])
    
    try:
        cmd = base_cmd + ['--dump-json', f'https://space.bilibili.com/{user_id}']
        result = subprocess.run(cmd, capture_output=True, timeout=180)
        
        print(f"yt-dlp 返回码: {result.returncode}")
        
        if result.returncode == 0:
            stdout = result.stdout.decode('utf-8', errors='ignore')
            videos = []
            
            for line in stdout.strip().split('\n'):
                if not line.strip():
                    continue
                try:
                    info = json.loads(line)
                    title = info.get('title', '')
                    bvid = info.get('id', '') or info.get('url', '').split('/')[-1]
                    
                    if bvid and bvid.startswith('BV'):
                        if not title or title == 'NA':
                            title = f'视频_{bvid}'
                        videos.append({
                            'title': title,
                            'bvid': bvid
                        })
                except json.JSONDecodeError:
                    continue
            
            print(f"获取到 {len(videos)} 个视频")
            return videos
        else:
            stderr = result.stderr.decode('utf-8', errors='ignore')
            print(f"yt-dlp 错误: {stderr}")
            
            cmd2 = base_cmd + ['--print', '%(title)s\t%(id)s', f'https://space.bilibili.com/{user_id}']
            result2 = subprocess.run(cmd2, capture_output=True, timeout=180)
            
            if result2.returncode == 0:
                stdout = result2.stdout.decode('utf-8', errors='ignore')
                videos = []
                for line in stdout.strip().split('\n'):
                    if '\t' in line:
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            title, bvid = parts[0], parts[1]
                            if bvid and bvid.startswith('BV'):
                                if not title or title == 'NA':
                                    title = f'视频_{bvid}'
                                videos.append({
                                    'title': title,
                                    'bvid': bvid
                                })
                print(f"获取到 {len(videos)} 个视频")
                return videos
    except Exception as e:
        print(f"获取视频列表失败: {e}")
    return []


def download_video_task(task_id, bvid, title, config):
    """后台下载任务"""
    bvid = extract_bvid(bvid)
    url = f"https://www.bilibili.com/video/{bvid}"
    output_dir = config.get('download_path', './downloads')
    
    os.makedirs(output_dir, exist_ok=True)
    
    safe_title = "".join(c if c.isalnum() or c in '._- ' else '_' for c in title)[:80]
    output_file = os.path.join(output_dir, f"{safe_title}.mp3")
    
    download_tasks[task_id].update({
        'status': 'downloading',
        'progress': 0,
        'output_file': output_file
    })
    
    try:
        cmd = [
            'yt-dlp',
            '-f', 'bestaudio/best',
            '--extract-audio',
            '--audio-format', config.get('audio_format', 'mp3'),
            '--audio-quality', config.get('audio_quality', '0'),
            '--output', output_file,
            '--no-warnings',
            '--progress',
            '--newline',
            url
        ]
        
        if config.get('proxy'):
            cmd.extend(['--proxy', config['proxy']])
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='ignore'
        )
        
        for line in process.stdout:
            line = line.strip()
            if '[download]' in line and '%' in line:
                try:
                    percent_str = line.split('%')[0].split()[-1]
                    progress = float(percent_str)
                    download_tasks[task_id]['progress'] = progress
                except:
                    pass
        
        process.wait()
        
        if process.returncode == 0 and os.path.exists(output_file):
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            download_tasks[task_id].update({
                'status': 'completed',
                'progress': 100,
                'file_size': round(file_size, 2),
                'completed_at': datetime.now().isoformat()
            })
            
            download_history.append({
                'task_id': task_id,
                'bvid': bvid,
                'title': title,
                'file_size': round(file_size, 2),
                'download_path': output_file,
                'completed_at': datetime.now().isoformat()
            })
        else:
            download_tasks[task_id].update({
                'status': 'failed',
                'error': '下载失败'
            })
            
    except Exception as e:
        download_tasks[task_id].update({
            'status': 'failed',
            'error': str(e)
        })


# ============ API 路由 ============

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    return jsonify(load_config())


@app.route('/api/config', methods=['POST'])
def update_config():
    """更新配置"""
    config = load_config()
    new_config = request.json
    config.update(new_config)
    save_config(config)
    return jsonify({'success': True, 'config': config})


@app.route('/api/videos/<path:user_input>')
def api_get_user_videos(user_input):
    """获取用户视频列表"""
    user_id = extract_user_id(user_input)
    videos = get_user_videos(user_id)
    return jsonify({'videos': videos, 'count': len(videos), 'user_id': user_id})


@app.route('/api/video/info/<path:bvid_input>')
def api_get_video_info(bvid_input):
    """获取视频信息"""
    bvid = extract_bvid(bvid_input)
    info = get_video_info(bvid)
    if info:
        return jsonify({'success': True, 'info': info})
    return jsonify({'success': False, 'error': '无法获取视频信息'})


@app.route('/api/download', methods=['POST'])
def start_download():
    """开始下载"""
    data = request.json
    bvid = extract_bvid(data.get('bvid', ''))
    title = data.get('title', bvid)
    
    if not bvid:
        return jsonify({'success': False, 'error': '缺少BV号'})
    
    task_id = f"task_{int(time.time() * 1000)}_{bvid}"
    config = load_config()
    
    download_tasks[task_id] = {
        'id': task_id,
        'bvid': bvid,
        'title': title,
        'status': 'pending',
        'progress': 0,
        'created_at': datetime.now().isoformat()
    }
    
    thread = threading.Thread(
        target=download_video_task,
        args=(task_id, bvid, title, config)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'task_id': task_id})


@app.route('/api/download/batch', methods=['POST'])
def start_batch_download():
    """批量下载"""
    data = request.json
    videos = data.get('videos', [])
    
    if not videos:
        return jsonify({'success': False, 'error': '没有视频'})
    
    task_ids = []
    config = load_config()
    
    for video in videos:
        bvid = extract_bvid(video.get('bvid', ''))
        title = video.get('title', bvid)
        
        if not bvid:
            continue
        
        task_id = f"task_{int(time.time() * 1000)}_{bvid}"
        download_tasks[task_id] = {
            'id': task_id,
            'bvid': bvid,
            'title': title,
            'status': 'pending',
            'progress': 0,
            'created_at': datetime.now().isoformat()
        }
        
        thread = threading.Thread(
            target=download_video_task,
            args=(task_id, bvid, title, config)
        )
        thread.daemon = True
        thread.start()
        
        task_ids.append(task_id)
    
    return jsonify({'success': True, 'task_ids': task_ids, 'count': len(task_ids)})


@app.route('/api/tasks')
def get_tasks():
    """获取所有任务状态"""
    return jsonify({'tasks': list(download_tasks.values())})


@app.route('/api/task/<task_id>')
def get_task(task_id):
    """获取单个任务状态"""
    task = download_tasks.get(task_id)
    if task:
        return jsonify({'success': True, 'task': task})
    return jsonify({'success': False, 'error': '任务不存在'})


@app.route('/api/history')
def get_history():
    """获取下载历史"""
    return jsonify({'history': download_history})


@app.route('/api/downloads')
def list_downloads():
    """列出已下载的文件"""
    config = load_config()
    download_path = config.get('download_path', './downloads')
    
    files = []
    if os.path.exists(download_path):
        for filename in os.listdir(download_path):
            if filename.endswith(('.mp3', '.m4a', '.wav')):
                filepath = os.path.join(download_path, filename)
                files.append({
                    'name': filename,
                    'size': round(os.path.getsize(filepath) / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                })
    
    files.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify({'files': files, 'path': os.path.abspath(download_path)})


@app.route('/api/download/file/<path:filename>')
def download_file(filename):
    """下载文件"""
    config = load_config()
    download_path = config.get('download_path', './downloads')
    return send_from_directory(download_path, filename, as_attachment=True)


@app.route('/api/stats')
def get_stats():
    """获取统计信息"""
    config = load_config()
    download_path = config.get('download_path', './downloads')
    
    total_files = 0
    total_size = 0
    
    if os.path.exists(download_path):
        for filename in os.listdir(download_path):
            if filename.endswith(('.mp3', '.m4a', '.wav')):
                total_files += 1
                filepath = os.path.join(download_path, filename)
                total_size += os.path.getsize(filepath)
    
    return jsonify({
        'total_files': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'total_tasks': len(download_tasks),
        'completed_tasks': sum(1 for t in download_tasks.values() if t['status'] == 'completed'),
        'pending_tasks': sum(1 for t in download_tasks.values() if t['status'] == 'pending'),
        'downloading_tasks': sum(1 for t in download_tasks.values() if t['status'] == 'downloading')
    })


if __name__ == '__main__':
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    
    print("=" * 60)
    print("B站视频下载器 - Web UI")
    print("=" * 60)
    print("访问地址: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
