"""
配置文件
存储全局配置参数
"""

# 数据库配置
DB_NAME = "iot_data.db"

# WebSocket 服务器配置
WS_HOST = "0.0.0.0"  # 监听所有网络接口
WS_PORT = 8765        # 监听端口

# 协议配置
PROTOCOL_HEADER = 0xAA55   # 协议帧头
PROTOCOL_VERSION = 0x12     # 协议版本号

# 命令类型定义
CMD_HEARTBEAT = 0x01       # 心跳包
CMD_SENSOR_DATA = 0x10     # 温湿度数据上报
CMD_LED_CONTROL = 0x80     # LED 控制命令

# GUI 配置
WINDOW_TITLE = "Computer Service"
WINDOW_SIZE = "800x600"