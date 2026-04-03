# 树莓派摄像头视频传输与实时控制项目

## 项目简介

本项目实现树莓派摄像头视频流实时传输到服务器节点，并通过Web前端实时显示视频和控制摄像头分辨率。

## 系统架构

```
树莓派 (摄像头)  --WebSocket-->  节点1 (服务器)  --WebSocket-->  前端浏览器
     ↑                                                              ↓
     └────────────────── 控制指令 (分辨率调节) ───────────────────┘
```

## 项目结构

```
raspberry_camera_streaming/
├── raspberry_pi/          # 树莓派端代码
│   ├── camera_client.py   # 摄像头采集和WebSocket客户端
│   └── requirements.txt   # 依赖包
├── server/                # 服务器端代码
│   ├── server.py          # WebSocket服务器和HTTP API
│   └── requirements.txt   # 依赖包
├── frontend/               # 前端代码
│   ├── index.html         # 主页面
│   ├── style.css         # 样式文件
│   └── app.js             # JavaScript逻辑
└── README.md              # 本文件
```

## 功能特性

- ✅ 实时视频流传输（WebSocket）
- ✅ 前端实时显示视频
- ✅ 实时调节摄像头分辨率
- ✅ 支持多种分辨率预设
- ✅ 低延迟传输
- ✅ 自动重连机制

## 安装和运行

### 1. 树莓派端设置

```bash
cd raspberry_pi
pip install -r requirements.txt
```

编辑 `camera_client.py`，修改服务器地址：
```python
SERVER_URL = "ws://节点1的IP:8765"
```

运行：
```bash
python camera_client.py
```

### 2. 服务器端设置

```bash
cd server
pip install -r requirements.txt
```

运行：
```bash
python server.py
```

服务器默认监听：
- WebSocket: `ws://0.0.0.0:8765`
- HTTP API: `http://0.0.0.0:5000`

### 3. 前端访问

在浏览器中打开：
```
http://节点1的IP:5000
```

## 支持的分辨率

- 640x480 (VGA)
- 800x600 (SVGA)
- 1024x768 (XGA)
- 1280x720 (HD)
- 1920x1080 (Full HD)

## 配置说明

### 树莓派端配置

在 `camera_client.py` 中可以配置：
- `SERVER_URL`: 服务器WebSocket地址
- `DEFAULT_RESOLUTION`: 默认分辨率
- `FPS`: 帧率（默认30）

### 服务器端配置

在 `server.py` 中可以配置：
- `WS_PORT`: WebSocket端口（默认8765）
- `HTTP_PORT`: HTTP端口（默认5000）
- `MAX_CLIENTS`: 最大连接数

## 故障排除

1. **连接失败**: 检查防火墙设置，确保端口8765和5000开放
2. **视频卡顿**: 降低分辨率或帧率
3. **摄像头无法打开**: 检查树莓派摄像头连接和权限

## 技术栈

- **树莓派端**: Python, OpenCV/picamera2, websocket-client
- **服务器端**: Python, Flask, websockets, asyncio
- **前端**: HTML5, JavaScript, WebSocket API

## 许可证

MIT License

