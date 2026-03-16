/**
 * B站视频下载器 - Web UI 前端应用
 */

// ========================================
// 全局状态
// ========================================
const AppState = {
    currentPage: 'download',
    config: {},
    videos: [],
    tasks: {},
    selectedVideos: new Set(),
    isLoading: false
};

// ========================================
// API 接口
// ========================================
const API = {
    async getConfig() {
        const response = await fetch('/api/config');
        return response.json();
    },
    
    async updateConfig(config) {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return response.json();
    },
    
    async getUserVideos(userId) {
        const response = await fetch(`/api/videos/${userId}`);
        return response.json();
    },
    
    async getVideoInfo(bvid) {
        const response = await fetch(`/api/video/info/${bvid}`);
        return response.json();
    },
    
    async startDownload(bvid, title) {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bvid, title })
        });
        return response.json();
    },
    
    async startBatchDownload(videos) {
        const response = await fetch('/api/download/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videos })
        });
        return response.json();
    },
    
    async getTasks() {
        const response = await fetch('/api/tasks');
        return response.json();
    },
    
    async getTask(taskId) {
        const response = await fetch(`/api/task/${taskId}`);
        return response.json();
    },
    
    async getHistory() {
        const response = await fetch('/api/history');
        return response.json();
    },
    
    async getDownloads() {
        const response = await fetch('/api/downloads');
        return response.json();
    },
    
    async getStats() {
        const response = await fetch('/api/stats');
        return response.json();
    }
};

// ========================================
// UI 工具函数
// ========================================
const UI = {
    // 显示通知
    showToast(title, message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${icons[type]}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },
    
    // 显示/隐藏加载
    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        overlay.style.display = show ? 'flex' : 'none';
    },
    
    // 切换页面
    switchPage(pageName) {
        // 更新导航
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === pageName) {
                item.classList.add('active');
            }
        });
        
        // 更新页面内容
        document.querySelectorAll('.page').forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(`page-${pageName}`).classList.add('active');
        
        AppState.currentPage = pageName;
        
        // 页面特定初始化
        if (pageName === 'tasks') {
            this.loadTasks();
        } else if (pageName === 'history') {
            this.loadHistory();
        } else if (pageName === 'settings') {
            this.loadSettings();
        }
    },
    
    // 格式化文件大小
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // 格式化时长
    formatDuration(seconds) {
        if (!seconds) return '00:00';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
};

// ========================================
// 页面功能
// ========================================
const PageDownload = {
    init() {
        // 标签切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const clickedElement = e.currentTarget;
                const tabName = clickedElement.dataset.tab;
                
                console.log('切换到标签:', tabName);
                
                // 移除所有活动状态
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
                
                // 激活当前标签
                clickedElement.classList.add('active');
                const tabContent = document.getElementById(`tab-${tabName}`);
                if (tabContent) {
                    tabContent.classList.add('active');
                    console.log('显示标签内容:', tabContent);
                }
            });
        });
        
        // 获取视频按钮
        document.getElementById('fetch-videos-btn').addEventListener('click', () => this.fetchVideos());
        
        // 下载全部按钮
        document.getElementById('download-all-btn').addEventListener('click', () => this.downloadAll());
        
        // 单个视频下载
        document.getElementById('download-single-btn').addEventListener('click', () => this.downloadSingle());
        
        // 批量下载
        document.getElementById('download-batch-btn').addEventListener('click', () => this.downloadBatch());
        
        // 视频URL输入框失去焦点时获取信息
        document.getElementById('video-url-input').addEventListener('blur', (e) => {
            if (e.target.value) {
                this.previewVideo(e.target.value);
            }
        });
        
        // 全选/取消全选
        document.getElementById('select-all').addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('.video-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = e.target.checked;
                const card = cb.closest('.video-card');
                const bvid = card.dataset.bvid;
                
                if (e.target.checked) {
                    AppState.selectedVideos.add(bvid);
                    card.classList.add('selected');
                } else {
                    AppState.selectedVideos.delete(bvid);
                    card.classList.remove('selected');
                }
            });
        });
        
        // 下载选中
        document.getElementById('download-selected-btn').addEventListener('click', () => this.downloadSelected());
    },
    
    async fetchVideos() {
        const userId = document.getElementById('user-id-input').value.trim();
        if (!userId) {
            UI.showToast('错误', '请输入用户ID', 'error');
            return;
        }
        
        UI.showLoading(true);
        
        try {
            const data = await API.getUserVideos(userId);
            
            if (data.videos && data.videos.length > 0) {
                AppState.videos = data.videos;
                this.renderVideos(data.videos);
                
                // 显示用户信息
                document.getElementById('user-info-card').style.display = 'flex';
                document.getElementById('video-count').textContent = data.count;
                document.getElementById('videos-section').style.display = 'block';
                
                UI.showToast('成功', `获取到 ${data.count} 个视频`, 'success');
            } else {
                UI.showToast('提示', '未找到视频', 'warning');
            }
        } catch (error) {
            UI.showToast('错误', '获取视频列表失败', 'error');
            console.error(error);
        } finally {
            UI.showLoading(false);
        }
    },
    
    renderVideos(videos) {
        const grid = document.getElementById('videos-grid');
        grid.innerHTML = '';
        
        videos.forEach((video, index) => {
            const card = document.createElement('div');
            card.className = 'video-card';
            card.dataset.bvid = video.bvid;
            card.dataset.index = index;
            
            card.innerHTML = `
                <div class="video-thumbnail">
                    <input type="checkbox" class="video-checkbox" data-bvid="${video.bvid}">
                    <div class="video-duration">--:--</div>
                </div>
                <div class="video-info">
                    <div class="video-title">${video.title}</div>
                    <div class="video-meta">
                        <span>${video.bvid}</span>
                    </div>
                </div>
                <div class="video-actions">
                    <button class="btn-secondary btn-small" onclick="PageDownload.downloadSingleVideo('${video.bvid}', '${video.title.replace(/'/g, "\\'")}')">
                        <i class="fas fa-download"></i>
                        下载
                    </button>
                </div>
            `;
            
            // 复选框事件
            const checkbox = card.querySelector('.video-checkbox');
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    AppState.selectedVideos.add(video.bvid);
                    card.classList.add('selected');
                } else {
                    AppState.selectedVideos.delete(video.bvid);
                    card.classList.remove('selected');
                }
            });
            
            grid.appendChild(card);
        });
    },
    
    async previewVideo(urlOrBvid) {
        // 提取BV号
        let bvid = urlOrBvid;
        if (urlOrBvid.includes('bilibili.com')) {
            const match = urlOrBvid.match(/BV[a-zA-Z0-9]+/);
            if (match) bvid = match[0];
        }
        
        if (!bvid || !bvid.startsWith('BV')) {
            return;
        }
        
        try {
            const data = await API.getVideoInfo(bvid);
            
            if (data.success) {
                const info = data.info;
                document.getElementById('video-preview').style.display = 'flex';
                document.getElementById('preview-thumb').src = info.thumbnail || '';
                document.getElementById('preview-title').textContent = info.title;
                document.getElementById('preview-author').textContent = info.uploader;
                document.getElementById('preview-views').textContent = this.formatNumber(info.view_count);
                document.getElementById('preview-likes').textContent = this.formatNumber(info.like_count);
                document.getElementById('preview-duration').textContent = UI.formatDuration(info.duration);
            }
        } catch (error) {
            console.error('获取视频信息失败:', error);
        }
    },
    
    formatNumber(num) {
        if (!num) return '0';
        if (num >= 10000) {
            return (num / 10000).toFixed(1) + '万';
        }
        return num.toString();
    },
    
    async downloadSingle() {
        const input = document.getElementById('video-url-input').value.trim();
        if (!input) {
            UI.showToast('错误', '请输入视频链接或BV号', 'error');
            return;
        }
        
        let bvid = input;
        if (input.includes('bilibili.com')) {
            const match = input.match(/BV[a-zA-Z0-9]+/);
            if (match) bvid = match[0];
        }
        
        await this.downloadSingleVideo(bvid, '视频_' + bvid);
    },
    
    async downloadSingleVideo(bvid, title) {
        try {
            const data = await API.startDownload(bvid, title);
            
            if (data.success) {
                UI.showToast('成功', '下载任务已创建', 'success');
                AppState.tasks[data.task_id] = { id: data.task_id, status: 'pending' };
                this.updateTaskBadge();
            } else {
                UI.showToast('错误', data.error || '创建下载任务失败', 'error');
            }
        } catch (error) {
            UI.showToast('错误', '网络错误', 'error');
            console.error(error);
        }
    },
    
    async downloadBatch() {
        const input = document.getElementById('batch-input').value.trim();
        if (!input) {
            UI.showToast('错误', '请输入BV号列表', 'error');
            return;
        }
        
        const lines = input.split('\n').filter(line => line.trim());
        const videos = lines.map(line => {
            let bvid = line.trim();
            if (bvid.includes('bilibili.com')) {
                const match = bvid.match(/BV[a-zA-Z0-9]+/);
                if (match) bvid = match[0];
            }
            return { bvid, title: '视频_' + bvid };
        }).filter(v => v.bvid.startsWith('BV'));
        
        if (videos.length === 0) {
            UI.showToast('错误', '未找到有效的BV号', 'error');
            return;
        }
        
        UI.showLoading(true);
        
        try {
            const data = await API.startBatchDownload(videos);
            
            if (data.success) {
                UI.showToast('成功', `已创建 ${data.count} 个下载任务`, 'success');
                data.task_ids.forEach(id => {
                    AppState.tasks[id] = { id, status: 'pending' };
                });
                this.updateTaskBadge();
            } else {
                UI.showToast('错误', data.error || '创建批量下载失败', 'error');
            }
        } catch (error) {
            UI.showToast('错误', '网络错误', 'error');
            console.error(error);
        } finally {
            UI.showLoading(false);
        }
    },
    
    async downloadAll() {
        if (AppState.videos.length === 0) {
            UI.showToast('错误', '没有视频可下载', 'error');
            return;
        }
        
        const confirm = window.confirm(`确定要下载全部 ${AppState.videos.length} 个视频吗？`);
        if (!confirm) return;
        
        UI.showLoading(true);
        
        try {
            const data = await API.startBatchDownload(AppState.videos);
            
            if (data.success) {
                UI.showToast('成功', `已创建 ${data.count} 个下载任务`, 'success');
                data.task_ids.forEach(id => {
                    AppState.tasks[id] = { id, status: 'pending' };
                });
                this.updateTaskBadge();
            }
        } catch (error) {
            UI.showToast('错误', '创建下载任务失败', 'error');
            console.error(error);
        } finally {
            UI.showLoading(false);
        }
    },
    
    async downloadSelected() {
        if (AppState.selectedVideos.size === 0) {
            UI.showToast('提示', '请先选择视频', 'warning');
            return;
        }
        
        const selectedVideos = AppState.videos.filter(v => AppState.selectedVideos.has(v.bvid));
        
        UI.showLoading(true);
        
        try {
            const data = await API.startBatchDownload(selectedVideos);
            
            if (data.success) {
                UI.showToast('成功', `已创建 ${data.count} 个下载任务`, 'success');
                data.task_ids.forEach(id => {
                    AppState.tasks[id] = { id, status: 'pending' };
                });
                this.updateTaskBadge();
            }
        } catch (error) {
            UI.showToast('错误', '创建下载任务失败', 'error');
            console.error(error);
        } finally {
            UI.showLoading(false);
        }
    },
    
    updateTaskBadge() {
        const badge = document.getElementById('task-badge');
        const count = Object.keys(AppState.tasks).length;
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
};

// ========================================
// 任务页面
// ========================================
const PageTasks = {
    refreshInterval: null,
    
    init() {
        // 开始自动刷新
        this.startAutoRefresh();
    },
    
    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (AppState.currentPage === 'tasks') {
                this.loadTasks();
            }
        }, 2000);
    },
    
    async loadTasks() {
        try {
            const data = await API.getTasks();
            this.renderTasks(data.tasks);
        } catch (error) {
            console.error('加载任务失败:', error);
        }
    },
    
    renderTasks(tasks) {
        const container = document.getElementById('tasks-container');
        
        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-tasks"></i>
                    <p>暂无下载任务</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = tasks.map(task => {
            const statusClass = task.status;
            const statusText = {
                'pending': '等待中',
                'downloading': '下载中',
                'completed': '已完成',
                'failed': '失败'
            }[task.status] || task.status;
            
            const iconClass = {
                'pending': 'fa-clock',
                'downloading': 'fa-spinner fa-spin',
                'completed': 'fa-check',
                'failed': 'fa-times'
            }[task.status] || 'fa-question';
            
            return `
                <div class="task-item">
                    <div class="task-icon ${statusClass}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <div class="task-info">
                        <div class="task-title">${task.title}</div>
                        <div class="task-meta">${task.bvid}</div>
                    </div>
                    ${task.status === 'downloading' ? `
                        <div class="task-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${task.progress || 0}%"></div>
                            </div>
                            <div class="progress-text">${(task.progress || 0).toFixed(1)}%</div>
                        </div>
                    ` : ''}
                    <div class="task-status ${statusClass}">${statusText}</div>
                </div>
            `;
        }).join('');
    }
};

// ========================================
// 历史记录页面
// ========================================
const PageHistory = {
    async loadHistory() {
        try {
            const data = await API.getDownloads();
            this.renderHistory(data.files);
            
            // 更新存储空间显示
            this.updateStorageInfo(data.files);
        } catch (error) {
            console.error('加载历史记录失败:', error);
        }
    },
    
    renderHistory(files) {
        const container = document.getElementById('files-list');
        
        if (files.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-music"></i>
                    <p>暂无下载记录</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-icon">
                    <i class="fas fa-music"></i>
                </div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">${file.size} MB · ${new Date(file.modified).toLocaleString()}</div>
                </div>
                <div class="file-actions">
                    <button class="btn-icon" onclick="PageHistory.downloadFile('${file.name}')" title="下载">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-icon" onclick="PageHistory.playFile('${file.name}')" title="播放">
                        <i class="fas fa-play"></i>
                    </button>
                </div>
            </div>
        `).join('');
    },
    
    updateStorageInfo(files) {
        const totalSize = files.reduce((sum, f) => sum + (f.size * 1024 * 1024), 0);
        document.getElementById('storage-used').textContent = UI.formatFileSize(totalSize);
        
        // 获取总空间（这里简化处理）
        const totalSpace = 100 * 1024 * 1024 * 1024; // 假设100GB
        document.getElementById('storage-total').textContent = '100 GB';
        
        const percentage = (totalSize / totalSpace) * 100;
        document.getElementById('storage-progress').style.width = `${Math.min(percentage, 100)}%`;
    },
    
    downloadFile(filename) {
        window.open(`/api/download/file/${encodeURIComponent(filename)}`, '_blank');
    },
    
    playFile(filename) {
        // 创建音频播放器
        const audio = new Audio(`/api/download/file/${encodeURIComponent(filename)}`);
        audio.play();
        UI.showToast('播放', `正在播放: ${filename}`, 'info');
    }
};

// ========================================
// 设置页面
// ========================================
const PageSettings = {
    async loadSettings() {
        try {
            const config = await API.getConfig();
            AppState.config = config;
            
            // 填充表单
            document.getElementById('setting-download-path').value = config.download_path || './downloads';
            document.getElementById('setting-quality').value = config.audio_quality || '0';
            document.getElementById('setting-format').value = config.audio_format || 'mp3';
            document.getElementById('setting-proxy').value = config.proxy || '';
            document.getElementById('setting-notification').checked = config.notification_sound !== false;
            
            // 主题
            const theme = config.theme || 'dark';
            document.querySelector(`input[name="theme"][value="${theme}"]`).checked = true;
            document.documentElement.setAttribute('data-theme', theme);
        } catch (error) {
            console.error('加载设置失败:', error);
        }
    },
    
    async saveSettings() {
        const config = {
            download_path: document.getElementById('setting-download-path').value,
            audio_quality: document.getElementById('setting-quality').value,
            audio_format: document.getElementById('setting-format').value,
            proxy: document.getElementById('setting-proxy').value,
            notification_sound: document.getElementById('setting-notification').checked,
            theme: document.querySelector('input[name="theme"]:checked').value
        };
        
        try {
            await API.updateConfig(config);
            AppState.config = config;
            
            // 应用主题
            document.documentElement.setAttribute('data-theme', config.theme);
            
            UI.showToast('成功', '设置已保存', 'success');
        } catch (error) {
            UI.showToast('错误', '保存设置失败', 'error');
            console.error(error);
        }
    },
    
    resetSettings() {
        if (confirm('确定要恢复默认设置吗？')) {
            document.getElementById('setting-download-path').value = './downloads';
            document.getElementById('setting-quality').value = '0';
            document.getElementById('setting-format').value = 'mp3';
            document.getElementById('setting-proxy').value = '';
            document.getElementById('setting-notification').checked = true;
            document.querySelector('input[name="theme"][value="dark"]').checked = true;
            
            this.saveSettings();
        }
    }
};

// ========================================
// 初始化
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // 初始化页面
    PageDownload.init();
    PageTasks.init();
    
    // 导航切换
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            UI.switchPage(page);
        });
    });
    
    // 主题切换
    document.getElementById('theme-toggle').addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // 保存主题设置
        API.updateConfig({ theme: newTheme });
        
        // 更新图标
        const icon = document.querySelector('#theme-toggle i');
        icon.className = newTheme === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
    });
    
    // 刷新按钮
    document.getElementById('refresh-btn').addEventListener('click', () => {
        location.reload();
    });
    
    // 设置页面事件
    document.getElementById('save-settings-btn').addEventListener('click', () => PageSettings.saveSettings());
    document.getElementById('reset-settings-btn').addEventListener('click', () => PageSettings.resetSettings());
    
    // 浏览按钮
    document.getElementById('browse-path-btn').addEventListener('click', () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                const path = e.target.files[0].path || e.target.files[0].webkitRelativePath;
                document.getElementById('setting-download-path').value = path;
            }
        });
        input.click();
    });
    
    // 主题选择
    document.querySelectorAll('input[name="theme"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.documentElement.setAttribute('data-theme', e.target.value);
        });
    });
    
    // 加载配置
    API.getConfig().then(config => {
        AppState.config = config;
        document.documentElement.setAttribute('data-theme', config.theme || 'dark');
    });
    
    // 显示欢迎消息
    setTimeout(() => {
        UI.showToast('欢迎', 'B站视频下载器已就绪', 'success');
    }, 500);
});

// 暴露到全局
window.PageDownload = PageDownload;
window.PageHistory = PageHistory;
