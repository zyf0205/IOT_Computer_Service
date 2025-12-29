# 上位机系统

一个基于 Python 的上位机控制系统，提供图形界面和网络通信功能。

## 项目结构

```
├── main.py          # 程序入口
├── gui.py           # 图形用户界面
├── server.py        # 服务器通信模块
├── protocol.py      # 通信协议定义
├── database.py      # 数据库操作
├── config.py        # 配置文件
└── .env/            # Python 虚拟环境
```

## 环境要求

- Python 3.x
- websockets 库（用于网络通信）


## 使用方法

1. **启动程序**
   ```bash
   python main.py
   ```

2. **配置说明**
   - 在 [config.py](config.py) 中配置服务器参数和系统设置
   - 根据需要修改数据库连接信息

## 功能模块

- **图形界面** ([gui.py](gui.py)): 提供用户交互界面
- **服务器通信** ([server.py](server.py)): 处理网络连接和数据传输
- **通信协议** ([protocol.py](protocol.py)): 定义数据格式和协议规范
- **数据库管理** ([database.py](database.py)): 数据存储和查询

