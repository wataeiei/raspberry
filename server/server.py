#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频流服务器
接收树莓派视频流并转发给前端
处理分辨率控制指令
"""

import asyncio
import websockets
import json
import logging
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from typing import Set, Optional
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
WS_PORT = 8765
HTTP_PORT = 5000

# 全局变量
raspberry_pi_ws: Optional[websockets.WebSocketServerProtocol] = None
frontend_clients: Set[websockets.WebSocketServerProtocol] = set()
current_frame_data: Optional[dict] = None
current_resolution = "640x480"

# Flask应用
app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app)


@app.route('/')
def index():
    """主页面"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """静态文件服务"""
    return send_from_directory('../frontend', path)


async def handle_raspberry_pi(websocket, path):
    """处理树莓派连接"""
    global raspberry_pi_ws, current_frame_data, current_resolution
    
    logger.info("树莓派已连接")
    raspberry_pi_ws = websocket
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "frame":
                    # 接收视频帧，转发给所有前端客户端
                    current_frame_data = data
                    current_resolution = data.get("resolution", current_resolution)
                    
                    # 广播给所有前端客户端（直接转发原始消息）
                    disconnected = set()
                    for client in frontend_clients:
                        try:
                            await client.send(message)
                        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError):
                            disconnected.add(client)
                    
                    # 移除断开的客户端
                    frontend_clients -= disconnected
                    
                elif msg_type == "resolution_info":
                    # 更新分辨率信息
                    current_resolution = data.get("resolution", current_resolution)
                    logger.info(f"树莓派分辨率: {current_resolution}")
                    
                elif msg_type == "pong":
                    # 心跳响应
                    pass
                    
            except json.JSONDecodeError:
                logger.error("无效的JSON消息")
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.warning("树莓派断开连接")
    finally:
        raspberry_pi_ws = None
        current_frame_data = None


async def handle_frontend(websocket, path):
    """处理前端连接"""
    global frontend_clients
    
    logger.info("前端客户端已连接")
    frontend_clients.add(websocket)
    
    # 发送当前分辨率信息
    if raspberry_pi_ws:
        await websocket.send(json.dumps({
            "type": "resolution_info",
            "resolution": current_resolution,
            "available_resolutions": ["640x480", "800x600", "1024x768", "1280x720", "1920x1080"]
        }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "set_resolution":
                    # 转发分辨率控制指令到树莓派
                    resolution = data.get("resolution")
                    if raspberry_pi_ws:
                        await raspberry_pi_ws.send(json.dumps({
                            "type": "set_resolution",
                            "resolution": resolution
                        }))
                        logger.info(f"转发分辨率调节指令: {resolution}")
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "树莓派未连接"
                        }))
                
                elif msg_type == "get_status":
                    # 返回当前状态
                    await websocket.send(json.dumps({
                        "type": "status",
                        "raspberry_pi_connected": raspberry_pi_ws is not None,
                        "current_resolution": current_resolution
                    }))
                    
            except json.JSONDecodeError:
                logger.error("无效的JSON消息")
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info("前端客户端断开连接")
    finally:
        frontend_clients.discard(websocket)


async def start_websocket_server():
    """启动WebSocket服务器"""
    # 树莓派连接端点
    raspberry_pi_server = await websockets.serve(
        handle_raspberry_pi,
        "0.0.0.0",
        WS_PORT,
        ping_interval=20,
        ping_timeout=10
    )
    logger.info(f"WebSocket服务器启动 (树莓派): ws://0.0.0.0:{WS_PORT}")
    
    # 前端连接端点
    frontend_server = await websockets.serve(
        handle_frontend,
        "0.0.0.0",
        WS_PORT + 1,  # 8766
        ping_interval=20,
        ping_timeout=10
    )
    logger.info(f"WebSocket服务器启动 (前端): ws://0.0.0.0:{WS_PORT + 1}")
    
    await asyncio.gather(
        raspberry_pi_server.wait_closed(),
        frontend_server.wait_closed()
    )


def run_flask():
    """运行Flask服务器"""
    app.run(host='0.0.0.0', port=HTTP_PORT, debug=False, threaded=True)


def main():
    """主函数"""
    # 在新线程中运行Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"HTTP服务器启动: http://0.0.0.0:{HTTP_PORT}")
    
    # 运行WebSocket服务器
    try:
        asyncio.run(start_websocket_server())
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")


if __name__ == "__main__":
    main()

