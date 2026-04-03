# 快速开始指南

## 一、服务器端（节点1）设置

### 1. 安装依赖

```bash
cd /mnt/disk1T/liyijuan/raspberry_camera_streaming/server
pip3 install -r requirements.txt
```

### 2. 启动服务器

```bash
# 方式1: 使用启动脚本
cd /mnt/disk1T/liyijuan/raspberry_camera_streaming
./start_server.sh

# 方式2: 直接运行
cd server
python3 server.py
```

服务器启动后会显示：
- WebSocket端口: 8765 (树莓派连接), 8766 (前端连接)
- HTTP端口: 5000 (前端访问)

### 3. 获取服务器IP地址

```bash
hostname -I
# 或
ip addr show | grep "inet " | grep -v 127.0.0.1
```

记住这个IP地址，需要在树莓派端配置。

---

## 二、树莓派端设置

### 1. 安装依赖

```bash
cd raspberry_pi
pip3 install -r requirements.txt
```

**注意**: 如果使用树莓派官方摄像头，推荐安装 `picamera2`:
```bash
sudo apt-get update
sudo apt-get install -y python3-picamera2
```

### 2. 配置服务器地址

编辑 `camera_client.py`，修改第18行：

```python
SERVER_URL = "ws://192.168.1.100:8765"  # 改为节点1的实际IP地址
```

### 3. 启动摄像头客户端

```bash
# 方式1: 使用启动脚本
cd /mnt/disk1T/liyijuan/raspberry_camera_streaming
./start_raspberry.sh

# 方式2: 直接运行
cd raspberry_pi
python3 camera_client.py
```

---

## 三、前端访问

在浏览器中打开（将IP替换为节点1的实际IP）：

```
http://节点1的IP:5000
```

例如：
```
http://192.168.1.100:5000
```

---

## 四、使用说明

### 查看视频流

打开前端页面后，如果树莓派已连接，会自动显示视频流。

### 调节分辨率

点击页面上的分辨率按钮即可实时调节：
- 640×480 (VGA) - 最低延迟
- 800×600 (SVGA)
- 1024×768 (XGA)
- 1280×720 (HD)
- 1920×1080 (Full HD) - 最高画质

### 状态指示

页面顶部显示：
- **连接状态**: 已连接/未连接/连接中
- **当前分辨率**: 显示当前使用的分辨率
- **帧率**: 实时显示视频帧率

---

## 五、常见问题

### 1. 树莓派无法连接服务器

- 检查服务器是否已启动
- 检查防火墙是否开放8765端口
- 检查IP地址是否正确

### 2. 前端无法显示视频

- 检查树莓派是否已连接
- 检查浏览器控制台是否有错误
- 检查防火墙是否开放8766和5000端口

### 3. 摄像头无法打开

- 检查摄像头是否正确连接
- 检查摄像头权限：`sudo usermod -a -G video $USER`
- 尝试重启树莓派

### 4. 视频卡顿

- 降低分辨率
- 检查网络带宽
- 降低帧率（修改 `camera_client.py` 中的 `FPS` 参数）

---

## 六、防火墙配置

如果使用防火墙，需要开放以下端口：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 5000/tcp
sudo ufw allow 8765/tcp
sudo ufw allow 8766/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --add-port=8765/tcp --permanent
sudo firewall-cmd --add-port=8766/tcp --permanent
sudo firewall-cmd --reload
```

---

## 七、系统服务（可选）

### 将服务器设置为系统服务

创建 `/etc/systemd/system/camera-server.service`:

```ini
[Unit]
Description=Camera Streaming Server
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/mnt/disk1T/liyijuan/raspberry_camera_streaming/server
ExecStart=/usr/bin/python3 /mnt/disk1T/liyijuan/raspberry_camera_streaming/server/server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl enable camera-server.service
sudo systemctl start camera-server.service
```

### 将树莓派客户端设置为系统服务

创建 `/etc/systemd/system/camera-client.service`:

```ini
[Unit]
Description=Raspberry Pi Camera Client
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/path/to/raspberry_camera_streaming/raspberry_pi
ExecStart=/usr/bin/python3 /path/to/raspberry_camera_streaming/raspberry_pi/camera_client.py
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 八、性能优化建议

1. **降低延迟**: 使用较低分辨率（640x480或800x600）
2. **提高画质**: 使用较高分辨率（1280x720或1920x1080）
3. **网络优化**: 确保树莓派和服务器在同一局域网
4. **硬件加速**: 树莓派使用picamera2可以获得更好的性能

---

## 技术支持

如遇问题，请检查：
1. 服务器日志输出
2. 树莓派端日志输出
3. 浏览器控制台（F12）

