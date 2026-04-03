# KataGo围棋人机对弈程序安装指南

## 项目结构

```
Project_six/
├── main.py          # Flask应用主文件
├── templates/
│   └── index.html   # 前端界面
├── README.md        # 项目说明
├── INSTALL.md       # 安装指南
├── katago.exe       # KataGo引擎（需要下载）
├── default_model.bin.gz  # 神经网络模型（需要下载）
└── default_gtp.cfg  # KataGo配置文件（需要复制）
```

## 安装步骤

### 1. 下载KataGo引擎

1. 访问 [KataGo Releases](https://github.com/lightvector/KataGo/releases/latest)
2. 下载 Windows OpenCL 版本：`katago-v1.16.4-opencl-windows-x64.zip`
3. 解压后将 `katago.exe` 文件复制到项目根目录

### 2. 下载神经网络模型

1. 访问 [katagotraining.org](https://katagotraining.org/)
2. 下载最新的神经网络模型（推荐使用 b18c384nbt 系列）
3. 将下载的模型文件重命名为 `default_model.bin.gz` 并复制到项目根目录

### 3. 复制配置文件

1. 从 `KataGo-master/cpp/configs/` 目录复制 `gtp_example.cfg` 文件
2. 将其重命名为 `default_gtp.cfg` 并复制到项目根目录
3. （可选）根据需要修改配置文件中的参数

### 4. 安装Python依赖

```bash
pip install flask
```

### 5. 修改main.py中的KataGo启动命令

打开 `main.py` 文件，取消注释以下代码：

```python
katago_process = subprocess.Popen(
    ['katago', 'gtp', '-model', 'default_model.bin.gz', '-config', 'default_gtp.cfg'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
time.sleep(1)
```

并注释掉模拟实现：

```python
# 模拟KataGo的响应
if command.startswith('genmove'):
    # 随机生成一个合法的落子位置
    import random
    while True:
        x = random.randint(0, 18)
        y = random.randint(0, 18)
        if board[x][y] == 0:
            return '= ' + chr(ord('A') + y) + str(19 - x)
return '= ok'
```

## 运行程序

```bash
python main.py
```

然后在浏览器中访问 `http://localhost:5000`

## 使用说明

1. 点击棋盘落子，黑棋为人类玩家
2. 系统会自动让KataGo（白棋）落子
3. 点击「重置棋盘」按钮可以重新开始游戏

## 故障排除

### 常见问题

1. **KataGo启动失败**
   - 检查 `katago.exe` 是否存在
   - 检查 `default_model.bin.gz` 是否存在
   - 检查 `default_gtp.cfg` 是否存在
   - 确保GPU驱动已安装（对于OpenCL版本）

2. **Flask启动失败**
   - 检查Python是否安装
   - 检查Flask是否已安装
   - 确保端口5000未被占用

3. **落子无响应**
   - 检查浏览器控制台是否有错误
   - 检查Flask服务器日志
   - 确保KataGo进程正在运行

### 性能优化

- 在 `default_gtp.cfg` 中调整 `numSearchThreads` 参数以匹配您的CPU核心数
- 对于GPU版本，可以调整 `maxVisits` 参数以平衡性能和强度

## 技术支持

如果遇到问题，请参考：
- [KataGo官方文档](https://github.com/lightvector/KataGo/blob/master/README.md)
- [KataGo Discord频道](https://discord.gg/bqkZAz3)
