// 获取服务器地址（从当前页面URL）
const SERVER_HOST = window.location.hostname;
const WS_PORT = 8766;  // 前端WebSocket端口
const video = document.getElementById('video-stream');
const noSignal = document.getElementById('no-signal');
const connectionStatus = document.getElementById('connection-status');
const resolutionStatus = document.getElementById('resolution-status');
const currentResolutionSpan = document.getElementById('current-resolution');
const fpsSpan = document.getElementById('fps');

let ws = null;
let frameCount = 0;
let lastFpsTime = Date.now();
let currentFps = 0;

// 初始化
init();

function init() {
    connectWebSocket();
    setupResolutionButtons();
    updateConnectionStatus('connecting', '连接中...');
}

function connectWebSocket() {
    const wsUrl = `ws://${SERVER_HOST}:${WS_PORT}`;
    console.log('连接WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        console.log('WebSocket连接已建立');
        updateConnectionStatus('connected', '已连接');
        requestStatus();
    };
    
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleMessage(data);
        } catch (e) {
            console.error('解析消息失败:', e);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        updateConnectionStatus('disconnected', '连接错误');
    };
    
    ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        updateConnectionStatus('disconnected', '已断开');
        noSignal.classList.remove('hidden');
        
        // 5秒后尝试重连
        setTimeout(() => {
            if (ws.readyState === WebSocket.CLOSED) {
                connectWebSocket();
            }
        }, 5000);
    };
}

function handleMessage(data) {
    const type = data.type;
    
    switch (type) {
        case 'frame':
            handleVideoFrame(data);
            break;
        case 'resolution_info':
            updateResolutionInfo(data.resolution);
            break;
        case 'status':
            if (data.raspberry_pi_connected) {
                updateConnectionStatus('connected', '已连接');
            } else {
                updateConnectionStatus('disconnected', '树莓派未连接');
            }
            break;
        case 'error':
            console.error('服务器错误:', data.message);
            break;
    }
}

function handleVideoFrame(data) {
    let imageData;
    
    if (typeof data === 'string') {
        // JSON格式，包含base64数据
        const frameData = JSON.parse(data);
        imageData = frameData.data;
    } else {
        // 直接是base64字符串
        imageData = data;
    }
    
    // 显示视频帧
    video.src = `data:image/jpeg;base64,${imageData}`;
    noSignal.classList.add('hidden');
    
    // 计算FPS
    frameCount++;
    const now = Date.now();
    if (now - lastFpsTime >= 1000) {
        currentFps = frameCount;
        frameCount = 0;
        lastFpsTime = now;
        fpsSpan.textContent = currentFps;
    }
}

function setupResolutionButtons() {
    const buttons = document.querySelectorAll('.resolution-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const resolution = btn.dataset.resolution;
            setResolution(resolution);
            
            // 更新按钮状态
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function setResolution(resolution) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'set_resolution',
            resolution: resolution
        }));
        console.log('发送分辨率调节指令:', resolution);
    } else {
        alert('WebSocket未连接，无法调节分辨率');
    }
}

function requestStatus() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'get_status'
        }));
    }
}

function updateConnectionStatus(status, text) {
    connectionStatus.className = `status-indicator ${status}`;
    connectionStatus.textContent = text;
}

function updateResolutionInfo(resolution) {
    currentResolutionSpan.textContent = resolution;
    resolutionStatus.textContent = `分辨率: ${resolution}`;
    
    // 更新对应按钮状态
    const buttons = document.querySelectorAll('.resolution-btn');
    buttons.forEach(btn => {
        if (btn.dataset.resolution === resolution) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// 页面卸载时关闭WebSocket
window.addEventListener('beforeunload', () => {
    if (ws) {
        ws.close();
    }
});

