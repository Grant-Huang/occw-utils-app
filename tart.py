[1mdiff --git a/gunicorn.conf.py b/gunicorn.conf.py[m
[1mindex 3ca5a70..c7ee938 100644[m
[1m--- a/gunicorn.conf.py[m
[1m+++ b/gunicorn.conf.py[m
[36m@@ -2,7 +2,7 @@[m
 import os[m
 [m
 # 绑定地址和端口[m
[31m-bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"[m
[32m+[m[32mbind = f"0.0.0.0:{os.environ.get('PORT', 999)}"[m
 [m
 # 工作进程数量（免费套餐推荐1个）[m
 workers = 1[m
