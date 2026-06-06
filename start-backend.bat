
@echo off
echo ====================================
echo 启动活动规划 Agent 后端服务
echo ====================================
echo.

cd backend

if not exist venv (
    echo 创建虚拟环境...
    python -m venv venv
)

echo 激活虚拟环境...
call venv\Scripts\activate

echo 安装依赖...
pip install -r requirements.txt

echo.
echo ====================================
echo 后端服务即将启动...
echo 访问地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo ====================================
echo.

python main.py

pause

