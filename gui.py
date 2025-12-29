"""
图形用户界面模块
基于 Tkinter 实现上位机界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import asyncio
import socket
import datetime
import sys
from server import IoTServer
from config import WINDOW_TITLE, WINDOW_SIZE


class IoTServerGUI:
    """IoT 服务器图形界面类"""
    
    def __init__(self, root):
        """初始化GUI"""
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)
        
        # 创建服务器实例
        self.server = IoTServer(
            log_callback=self.log,
            update_display_callback=self.update_sensor_display
        )
        
        # 设置样式
        self._setup_styles()
        
        # 创建界面元素
        self._create_widgets()
        
        # 启动后台服务器线程
        self.server_thread = threading.Thread(
            target=self._run_server_thread,
            daemon=True  # 守护线程,主线程结束时自动退出
        )
        self.server_thread.start()
    
    def _setup_styles(self):
        """配置UI样式"""
        style = ttk.Style()
        style.configure("Big.TLabel", font=("Arial", 24, "bold"))
        style.configure("Info.TLabel", font=("Arial", 12))
    
    def _create_widgets(self):
        """创建所有界面组件"""
        # 1. 顶部状态栏
        self._create_status_bar()
        
        # 2. 数据仪表盘
        self._create_data_dashboard()
        
        # 3. 控制按钮区
        self._create_control_panel()
        
        # 4. 日志显示区
        self._create_log_panel()
    
    def _create_status_bar(self):
        """创建顶部状态栏"""
        top_frame = ttk.LabelFrame(self.root, text="服务器状态", padding=10)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # 显示监听地址
        ip_addr = self._get_local_ip()
        self.lbl_info = ttk.Label(
            top_frame,
            text=f"监听地址: ws://{ip_addr}:8765",
            style="Info.TLabel",
            foreground="black"
        )
        self.lbl_info.pack(side="left")
        
        # 显示运行状态
        self.lbl_status = ttk.Label(
            top_frame,
            text="状态: 正在启动...",
            style="Info.TLabel"
        )
        self.lbl_status.pack(side="right")
    
    def _create_data_dashboard(self):
        """创建数据仪表盘"""
        data_frame = ttk.LabelFrame(self.root, text="实时环境数据", padding=20)
        data_frame.pack(fill="x", padx=10, pady=5)
        
        # 温度显示
        temp_frame = ttk.Frame(data_frame)
        temp_frame.pack(side="left", expand=True)
        ttk.Label(temp_frame, text="温度 (Temperature)", font=("Arial", 12)).pack()
        self.lbl_temp = ttk.Label(
            temp_frame,
            text="-- °C",
            style="Big.TLabel",
            foreground="#FF5722"
        )
        self.lbl_temp.pack()
        
        # 湿度显示
        hum_frame = ttk.Frame(data_frame)
        hum_frame.pack(side="left", expand=True)
        ttk.Label(hum_frame, text="湿度 (Humidity)", font=("Arial", 12)).pack()
        self.lbl_hum = ttk.Label(
            hum_frame,
            text="-- %",
            style="Big.TLabel",
            foreground="#2196F3"
        )
        self.lbl_hum.pack()
    
    def _create_control_panel(self):
        """创建控制按钮区"""
        ctrl_frame = ttk.LabelFrame(self.root, text="设备控制 (LED)", padding=10)
        ctrl_frame.pack(fill="x", padx=10, pady=5)
        
        # 开启按钮
        btn_on = ttk.Button(
            ctrl_frame,
            text="开启 LED (ON)",
            command=lambda: self.send_command(True)
        )
        btn_on.pack(side="left", padx=20, expand=True, fill="x")
        
        # 关闭按钮
        btn_off = ttk.Button(
            ctrl_frame,
            text="关闭 LED (OFF)",
            command=lambda: self.send_command(False)
        )
        btn_off.pack(side="right", padx=20, expand=True, fill="x")
    
    def _create_log_panel(self):
        """创建日志显示区"""
        log_frame = ttk.LabelFrame(self.root, text="通信日志 (Protocol Log)", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 使用带滚动条的文本框
        self.txt_log = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            state="disabled",  # 只读
            font=("Consolas", 9)
        )
        self.txt_log.pack(fill="both", expand=True)
    
    def _get_local_ip(self):
        """
        获取本机局域网IP地址
        
        返回:
            IP地址字符串
        """
        try:
            # 创建UDP socket连接到外部地址(不实际发送数据)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def log(self, message):
        """
        输出日志到界面
        (线程安全,使用 after 调度到主线程)
        
        参数:
            message: 日志消息
        """
        self.root.after(0, self._append_log, message)
    
    def _append_log(self, message):
        """在主线程中追加日志"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, f"[{timestamp}] {message}\n")
        self.txt_log.see(tk.END)  # 自动滚动到底部
        self.txt_log.config(state="disabled")
    
    def update_sensor_display(self, temp, hum):
        """
        更新传感器数据显示
        (线程安全)
        
        参数:
            temp: 温度值
            hum: 湿度值
        """
        self.root.after(0, lambda: self.lbl_temp.config(text=f"{temp} °C"))
        self.root.after(0, lambda: self.lbl_hum.config(text=f"{hum} %"))
        self.root.after(
            0,
            lambda: self.lbl_status.config(
                text="状态: 运行中 (Running)",
                foreground="green"
            )
        )
    
    def send_command(self, is_on):
        """
        发送LED控制命令
        
        参数:
            is_on: True=开启, False=关闭
        """
        if self.server.loop is None or not self.server.loop.is_running():
            messagebox.showwarning("提示", "服务器尚未启动")
            return
        
        # 跨线程调用: 将协程提交到服务器线程的事件循环
        asyncio.run_coroutine_threadsafe(
            self.server.broadcast_command(0x01020304, is_on),
            self.server.loop
        )
    
    def _run_server_thread(self):
        """
        后台线程入口函数
        创建新的事件循环并运行服务器
        """
        # 创建新的事件循环
        self.server.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.server.loop)
        
        try:
            # 运行服务器
            self.server.loop.run_until_complete(self.server.start())
        except Exception as e:
            self.log(f"Server Thread Error: {e}")