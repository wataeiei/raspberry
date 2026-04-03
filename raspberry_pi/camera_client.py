#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派摄像头客户端
采集视频并通过WebSocket发送到服务器
支持实时分辨率调节
"""

import cv2
import base64
import json
import time
import threading
import websocket
import logging
from typing import Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 服务器配置
SERVER_URL = "ws://192.168.1.100:8765"  # 修改为节点1的实际IP地址

# 分辨率预设
RESOLUTIONS = {
    "640x480": (640, 480),
    "800x600": (800, 600),
    "1024x768": (1024, 768),
    "1280x720": (1280, 720),
    "1920x1080": (1920, 1080),
}

DEFAULT_RESOLUTION = "640x480"
FPS = 30
FRAME_INTERVAL = 1.0 / FPS


class CameraClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.ws: Optional[websocket.WebSocketApp] = None
        self.camera: Optional[cv2.VideoCapture] = None
        self.current_resolution = DEFAULT_RESOLUTION
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.reconnect_interval = 5  # 重连间隔（秒）
        
    def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.ws = websocket.WebSocketApp(
                self.server_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            # 在新线程中运行WebSocket客户端
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.schedule_reconnect()
    
    def on_open(self, ws):
        """WebSocket连接打开"""
        logger.info("已连接到服务器")
        self.is_running = True
        # 发送初始分辨率信息
        self.send_resolution_info()
        # 启动摄像头采集线程
        self.start_capture()
    
    def on_message(self, ws, message):
        """接收服务器消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "set_resolution":
                resolution = data.get("resolution")
                if resolution in RESOLUTIONS:
                    logger.info(f"收到分辨率调节指令: {resolution}")
                    self.change_resolution(resolution)
                else:
                    logger.warning(f"不支持的分辨率: {resolution}")
            elif msg_type == "ping":
                # 心跳响应
                self.send_message({"type": "pong"})
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    def on_error(self, ws, error):
        """WebSocket错误"""
        logger.error(f"WebSocket错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket连接关闭"""
        logger.warning("与服务器断开连接")
        self.is_running = False
        self.stop_camera()
        self.schedule_reconnect()
    
    def send_message(self, data: dict):
        """发送消息到服务器"""
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
    
    def send_resolution_info(self):
        """发送当前分辨率信息"""
        self.send_message({
            "type": "resolution_info",
            "resolution": self.current_resolution,
            "available_resolutions": list(RESOLUTIONS.keys())
        })
    
    def start_capture(self):
        """启动摄像头采集"""
        if self.capture_thread and self.capture_thread.is_alive():
            return
        
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()
    
    def capture_loop(self):
        """摄像头采集循环"""
        self.init_camera()
        
        last_frame_time = time.time()
        
        while self.is_running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    logger.error("无法读取摄像头画面")
                    time.sleep(0.1)
                    continue
                
                # 控制帧率
                current_time = time.time()
                elapsed = current_time - last_frame_time
                if elapsed < FRAME_INTERVAL:
                    time.sleep(FRAME_INTERVAL - elapsed)
                last_frame_time = time.time()
                
                # 编码为JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_bytes = buffer.tobytes()
                frame_b64 = base64.b64encode(frame_bytes).decode('utf-8')
                
                # 发送到服务器
                self.send_message({
                    "type": "frame",
                    "data": frame_b64,
                    "timestamp": time.time(),
                    "resolution": self.current_resolution
                })
                
            except Exception as e:
                logger.error(f"采集帧失败: {e}")
                time.sleep(0.1)
    
    def init_camera(self):
        """初始化摄像头"""
        self.stop_camera()
        
        width, height = RESOLUTIONS[self.current_resolution]
        
        try:
            # 尝试使用picamera2（树莓派推荐）
            try:
                from picamera2 import Picamera2
                self.camera_pi = Picamera2()
                config = self.camera_pi.create_video_configuration(
                    main={"size": (width, height), "format": "RGB888"}
                )
                self.camera_pi.configure(config)
                self.camera_pi.start()
                self.use_picamera = True
                logger.info(f"使用picamera2，分辨率: {self.current_resolution}")
            except ImportError:
                # 回退到OpenCV
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    raise Exception("无法打开摄像头")
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                self.use_picamera = False
                logger.info(f"使用OpenCV，分辨率: {self.current_resolution}")
        except Exception as e:
            logger.error(f"初始化摄像头失败: {e}")
            raise
    
    def change_resolution(self, resolution: str):
        """改变分辨率"""
        if resolution == self.current_resolution:
            return
        
        logger.info(f"改变分辨率: {self.current_resolution} -> {resolution}")
        self.current_resolution = resolution
        self.init_camera()
        self.send_resolution_info()
    
    def stop_camera(self):
        """停止摄像头"""
        if hasattr(self, 'camera_pi') and self.use_picamera:
            try:
                self.camera_pi.stop()
                self.camera_pi.close()
            except:
                pass
        
        if self.camera:
            try:
                self.camera.release()
            except:
                pass
        
        self.camera = None
    
    def schedule_reconnect(self):
        """安排重连"""
        if not self.is_running:
            logger.info(f"{self.reconnect_interval}秒后尝试重连...")
            time.sleep(self.reconnect_interval)
            self.connect()
    
    def run(self):
        """运行客户端"""
        logger.info(f"启动摄像头客户端，连接服务器: {self.server_url}")
        self.connect()


def main():
    """主函数"""
    client = CameraClient(SERVER_URL)
    try:
        client.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
        client.is_running = False
        client.stop_camera()
        if client.ws:
            client.ws.close()


if __name__ == "__main__":
    main()

