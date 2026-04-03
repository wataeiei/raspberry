#!/bin/bash
# 启动树莓派客户端脚本

cd "$(dirname "$0")/raspberry_pi"

# 检查是否在树莓派上
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "警告: 这可能不是树莓派设备"
fi

echo "启动树莓派摄像头客户端..."
echo "请确保已修改 camera_client.py 中的 SERVER_URL"
echo ""

python3 camera_client.py

