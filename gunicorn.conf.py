# Gunicorn配置文件
import os

# 绑定地址和端口
bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"

# 工作进程数量（免费套餐推荐1个）
workers = 1

# 工作线程数量
threads = 2

# 超时设置
timeout = 120
keepalive = 2

# 日志配置
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# 进程配置
worker_class = 'sync'
worker_connections = 1000

# 预加载应用
preload_app = True

# 确保目录存在
def on_starting(server):
    """启动时创建必要的目录"""
    import os
    directories = ['uploads', 'data', 'upload']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"创建目录: {directory}")

# 启动后回调
def when_ready(server):
    """服务器准备就绪后的回调"""
    print("Gunicorn服务器已启动并准备接受请求")

# 工作进程启动回调
def on_reload(server):
    """重新加载时的回调"""
    print("Gunicorn服务器正在重新加载") 