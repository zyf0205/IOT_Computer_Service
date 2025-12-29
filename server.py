"""
WebSocket 服务器模块
负责处理客户端连接和数据通信
"""

import asyncio
import websockets
import struct
import datetime
from protocol import IotProtocol
from database import save_sensor_data
from config import CMD_HEARTBEAT, CMD_SENSOR_DATA, WS_HOST, WS_PORT


class IoTServer:
    """IoT WebSocket 服务器类"""
    
    def __init__(self, log_callback=None, update_display_callback=None, status_callback=None):
        """
        初始化服务器
        
        参数:
            log_callback: 日志回调函数 log(message)
            update_display_callback: 界面更新回调函数 update(temp, hum)
            status_callback: 状态更新回调函数 status(text, color)
        """
        self.loop = None                      # 异步事件循环
        self.connected_clients = set()        # 已连接的客户端集合
        self.log_callback = log_callback      # 日志输出回调
        self.update_display_callback = update_display_callback  # 界面更新回调
        self.status_callback = status_callback  # 新增状态回调
    
    def log(self, message):
        """输出日志"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(f"[Server] {message}")
    
    def update_status(self, text, color="black"):
        """更新状态"""
        if self.status_callback:
            self.status_callback(text, color)
    
    async def start(self):
        """启动 WebSocket 服务器"""
        self.log("正在启动 WebSocket 服务器...")
        
        # 使用 async with 启动服务器
        async with websockets.serve(self.ws_handler, WS_HOST, WS_PORT):
            self.log(f"服务器启动成功: ws://{WS_HOST}:{WS_PORT}")
            
            # 更新状态为监听中
            self.update_status("状态: 监听中", "green")
            
            # 保持服务器运行
            await asyncio.Future()
    
    async def ws_handler(self, websocket):
        """
        WebSocket 连接处理器
        
        参数:
            websocket: 客户端连接对象
        """
        # 添加到连接列表
        self.connected_clients.add(websocket)
        self.log(f"新设备接入: {websocket.remote_address}")
        
        try:
            # 持续接收消息
            async for message in websocket:
                # 只处理二进制数据
                if isinstance(message, bytes):
                    result, msg = IotProtocol.parse_packet(message)
                    
                    if result:
                        # 解析成功,处理数据
                        await self.process_data(result)
                    else:
                        # 解析失败,记录错误
                        self.log(f"解析失败: {msg} | Hex: {message.hex()}")
                else:
                    self.log("收到文本数据(已忽略)")
                    
        except websockets.exceptions.ConnectionClosed:
            self.log(f"设备断开连接: {websocket.remote_address}")
        except Exception as e:
            self.log(f"连接异常: {e}")
        finally:
            # 从连接列表移除
            self.connected_clients.discard(websocket)
    
    async def process_data(self, data):
        """
        处理接收到的数据
        
        参数:
            data: 解析后的数据字典
        """
        cmd = data["cmd"]
        dev_id = hex(data["dev_id"])
        
        # 心跳包
        if cmd == CMD_HEARTBEAT:
            self.log(f"[心跳] Dev:{dev_id}")
        
        # 温湿度数据
        elif cmd == CMD_SENSOR_DATA:
            if len(data["payload"]) == 16:
                # 解析载荷: 温度(4B) + 湿度(4B) + 时间戳低位(4B) + 时间戳高位(4B)
                temp, hum, time_low, time_high = struct.unpack("<IIII", data["payload"])
                
                # 合并为64位毫秒时间戳
                device_time_ms = (time_high << 32) | time_low
                
                # 转换为 datetime 对象
                device_time_dt = datetime.datetime.fromtimestamp(device_time_ms / 1000.0)
                device_time_str = device_time_dt.strftime("%Y-%m-%d %H:%M:%S")
                
                # 保存到数据库
                success, error = save_sensor_data(dev_id, temp, hum, device_time_str)
                if not success:
                    self.log(f"DB错误: {error}")
                
                # 更新界面显示
                if self.update_display_callback:
                    self.update_display_callback(temp, hum)
                
                self.log(f"[上报] 温度:{temp}°C 湿度:{hum}% 时间:{device_time_str}")
            else:
                self.log(f"数据长度错误: {len(data['payload'])} (期望16字节)")
    
    async def broadcast_command(self, dev_id, led_status):
        """
        广播控制命令到所有连接的设备
        
        参数:
            dev_id: 目标设备ID
            led_status: LED状态 (True/False)
        """
        if not self.connected_clients:
            self.log("警告: 无设备连接")
            return
        
        # 构建控制数据包
        packet = IotProtocol.build_control_packet(dev_id, led_status)
        action = "开启" if led_status else "关闭"
        
        # 发送到所有连接的设备
        for ws in self.connected_clients:
            try:
                await ws.send(packet)
                self.log(f"[下发] LED {action} -> {ws.remote_address}")
            except Exception as e:
                self.log(f"发送失败: {e}")