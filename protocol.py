"""
IoT 通信协议处理模块
负责数据包的解析和构建
"""

import struct
from config import PROTOCOL_HEADER, PROTOCOL_VERSION


class IotProtocol:
    """IoT 通信协议处理类"""
    
    @staticmethod
    def calc_crc(data: bytes) -> int:
        """
        计算 CRC-16 校验值 (Modbus 标准)
        """
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    @staticmethod
    def parse_packet(data: bytes):
        """
        解析接收到的数据包基础结构
        """
        # 最小长度检查 (帧头2 + 版本1 + 命令1 + 序号1 + 设备ID4 + 长度2 + CRC2 = 13)
        if len(data) < 13:
            return None, "Length too short"

        try:
            # 解析固定头部 (11字节)
            head, ver, cmd, seq, dev_id, pay_len = struct.unpack("<HBBBIH", data[:11])
        except struct.error:
            return None, "Struct unpack error"

        # 验证帧头
        if head != PROTOCOL_HEADER:
            return None, f"Invalid Header: {hex(head)}"

        # 验证总长度
        expected_len = 11 + pay_len + 2  # 头部 + 载荷 + CRC
        if len(data) != expected_len:
            return None, f"Length Mismatch: Real={len(data)}, Expected={expected_len}"

        # 提取载荷数据
        payload = data[11 : 11 + pay_len]
        
        # 提取并验证 CRC
        recv_crc = struct.unpack("<H", data[11 + pay_len:])[0]
        calc_crc = IotProtocol.calc_crc(data[:-2])  # 计算除CRC外的所有数据

        if recv_crc != calc_crc:
            return None, f"CRC Error: Recv={hex(recv_crc)}, Calc={hex(calc_crc)}"

        # 返回解析结果
        return {
            "cmd": cmd,               # 命令类型
            "seq": seq,               # 序列号
            "dev_id": dev_id,         # 设备ID
            "payload": payload,       # 载荷数据 (原始字节)
            "raw_hex": data.hex().upper(),
        }, "OK"

    @staticmethod
    def decode_sensor_payload(payload: bytes):
        """
        [新增] 解析传感器上报的具体业务数据
        
        格式: [温度:4B float] [湿度:4B float] [光照:4B uint] [时间戳:8B uint64]
        总长度: 20 字节
        """
        if len(payload) != 20:
            return None
            
        try:
            # < = 小端序
            # f = float (4 bytes)
            # I = unsigned int (4 bytes)
            # Q = unsigned long long (8 bytes)
            temp, hum, light, ts = struct.unpack("<ffIQ", payload)
            
            return {
                "temp": round(temp, 1), # 保留1位小数
                "hum": round(hum, 1),   # 保留1位小数
                "light": light,         # 原始光照值 (0-4095)
                "ts": ts
            }
        except struct.error:
            return None

    @staticmethod
    def build_control_packet(dev_id: int, led_status: bool) -> bytes:
        """
        构建 LED 控制命令数据包
        """
        cmd = 0x80  # LED 控制命令
        seq = 0x01  # 序列号
        
        # 载荷: 1字节状态值 (1=开, 0=关)
        payload = struct.pack("B", 1 if led_status else 0)
        length = len(payload)

        # 构建数据包头部
        header = struct.pack(
            "<HBBBIH",
            PROTOCOL_HEADER,    # 帧头
            PROTOCOL_VERSION,   # 版本
            cmd,                # 命令
            seq,                # 序号
            dev_id,             # 设备ID
            length              # 载荷长度
        )
        
        # 拼接头部和载荷
        packet = header + payload
        
        # 计算并追加 CRC
        crc_val = IotProtocol.calc_crc(packet)
        packet += struct.pack("<H", crc_val)
        
        return packet