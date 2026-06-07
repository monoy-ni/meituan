
@echo off
echo ====================================
echo 启动活动规划 Agent 后端服务
echo ====================================
echo.

:: 默认端口为 8000，如果需要修改端口，请修改下面的 PORT 变量
set PORT=8000

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
echo 访问地址: http://localhost:%PORT%
echo API 文档: http://localhost:%PORT%/docs
echo.
echo 提示: 如需修改端口，请编辑此文件中的 set PORT=8000 行
echo ====================================
echo.

:: 设置环境变量
set HOST=0.0.0.0
set PORT=%PORT%

:: 启动服务
python main.py

pause

