"""
IoT 上位机服务程序
主入口文件
"""

import tkinter as tk
from tkinter import messagebox
import asyncio
import sys
import os

from database import init_db
from gui import IoTServerGUI


def main():
    """程序主入口"""
    # Windows 系统特殊配置
    if sys.platform == "win32":
        # 设置事件循环策略,避免某些情况下的兼容性问题
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # 初始化数据库
    init_db()
    
    # 创建主窗口
    root = tk.Tk()
    
    # 创建GUI应用
    app = IoTServerGUI(root)
    
    def on_closing():
        """窗口关闭事件处理"""
        if messagebox.askokcancel("退出", "确定退出服务器?"):
            root.destroy()
            # 强制退出整个进程(包括后台守护线程)
            os._exit(0)
    
    # 绑定窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # 启动 Tkinter 主事件循环
    root.mainloop()


if __name__ == "__main__":
    main()