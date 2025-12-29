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
        
        参数:
            data: 需要计算校验的字节数据
        
        返回:
            16位 CRC 校验值
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
        解析接收到的数据包
        
        数据包格式:
            [帧头:2B] [版本:1B] [命令:1B] [序号:1B] [设备ID:4B] [长度:2B] [数据:NB] [CRC:2B]
        
        参数:
            data: 接收到的原始字节数据
        
        返回:
            成功: (解析结果字典, "OK")
            失败: (None, 错误信息)
        """
        # 最小长度检查 (帧头2 + 版本1 + 命令1 + 序号1 + 设备ID4 + 长度2 + CRC2 = 13)
        if len(data) < 13:
            return None, "Length too short"

        try:
            # 解析固定头部 (11字节)
            # < 表示小端序
            # H=2字节 B=1字节 I=4字节
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
            "payload": payload,       # 载荷数据
            "raw_hex": data.hex().upper(),  # 原始16进制字符串
        }, "OK"

    @staticmethod
    def build_control_packet(dev_id: int, led_status: bool) -> bytes:
        """
        构建 LED 控制命令数据包
        
        参数:
            dev_id: 目标设备ID
            led_status: True=开启, False=关闭
        
        返回:
            完整的二进制数据包
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