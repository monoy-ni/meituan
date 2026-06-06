
@echo off
echo ====================================
echo 启动活动规划 Agent 前端服务
echo ====================================
echo.

cd frontend

if not exist node_modules (
    echo 安装 npm 依赖...
    call npm install
)

echo.
echo ====================================
echo 前端服务即将启动...
echo 访问地址: http://localhost:3000
echo ====================================
echo.

call npm start

pause

