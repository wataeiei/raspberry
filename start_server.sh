#!/bin/bash
# 启动服务器脚本

cd "$(dirname "$0")/server"
echo "启动视频流服务器..."
echo "WebSocket端口: 8765 (树莓派), 8766 (前端)"
echo "HTTP端口: 5000"
echo "访问地址: http://$(hostname -I | awk '{print $1}'):5000"
echo ""

python3 server.py

