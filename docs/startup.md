# 启动说明

本文档用于在本地启动杭州活动规划 Agent 的后端和前端，并确认 `.env`、模型配置日志、端口和常见问题。

## 1. 前置检查

在项目根目录执行：

```powershell
cd "D:\meituan agent"
```

确认根目录存在 `.env`：

```powershell
Get-ChildItem -Force .env
```

后端会在读取 `AgentSettings.from_env()` 时自动加载 `.env`。如果系统环境变量和 `.env` 同时存在，系统环境变量优先，不会被 `.env` 覆盖。

`.env` 中不要把密钥打印到日志。后端启动日志只会记录：

```text
base_url
model
api_key_configured=True/False
temperature
timeout_seconds
data_mode
map_provider
```

## 2. 一键启动方式

后端：

```powershell
.\start-backend.bat
```

前端：

```powershell
.\start-frontend.bat
```

启动后访问：

```text
前端: http://localhost:3000
后端: http://localhost:8000
API 文档: http://localhost:8000/docs
```

## 3. 带日志后台启动方式

如果希望把启动日志写入文件，使用下面的命令。

启动后端：

```powershell
Start-Process `
  -FilePath "python" `
  -ArgumentList "backend\main.py" `
  -WorkingDirectory "D:\meituan agent" `
  -WindowStyle Hidden `
  -RedirectStandardOutput "D:\meituan agent\backend\backend.log" `
  -RedirectStandardError "D:\meituan agent\backend\backend.err.log"
```

启动前端：

```powershell
$env:BROWSER = "none"
Start-Process `
  -FilePath "cmd.exe" `
  -ArgumentList "/c", "npm start" `
  -WorkingDirectory "D:\meituan agent\frontend" `
  -WindowStyle Hidden `
  -RedirectStandardOutput "D:\meituan agent\frontend\frontend.log" `
  -RedirectStandardError "D:\meituan agent\frontend\frontend.err.log"
```

日志文件位置：

```text
backend\backend.err.log       后端模型配置读取日志 + uvicorn 启动日志
backend\backend.log           后端 stdout / 请求输出
frontend\frontend.log         前端启动与编译日志
frontend\frontend.err.log     前端 dev-server warning
```

后端成功启动时，`backend\backend.err.log` 会出现类似日志：

```text
model_config_loaded base_url=https://... model=... api_key_configured=True temperature=0.2 timeout_seconds=20.0 data_mode=hybrid map_provider=amap
```

## 4. 验证服务状态

检查端口监听：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
Get-NetTCPConnection -LocalPort 3000 -State Listen
```

检查后端健康状态：

```powershell
Invoke-RestMethod http://localhost:8000/docs
```

如果浏览器能打开前端，并且前端请求 `/api/sessions` 返回 200，说明前后端代理链路正常。

## 5. 停止服务

停止后端 8000 端口进程：

```powershell
$backendProcesses = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $backendProcesses) {
  Stop-Process -Id $processId -Force
}
```

停止前端 3000 端口进程：

```powershell
$frontendProcesses = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $frontendProcesses) {
  Stop-Process -Id $processId -Force
}
```

## 6. 常见问题

### 后端没有读取 `.env`

确认启动命令的工作目录是项目根目录：

```powershell
pwd
```

推荐从 `D:\meituan agent` 启动：

```powershell
python backend\main.py
```

如果要显式指定 `.env` 文件：

```powershell
$env:ACTIVITY_AGENT_ENV_FILE = "D:\meituan agent\.env"
python backend\main.py
```

### 8000 或 3000 端口被占用

先查看占用进程：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object LocalAddress,LocalPort,State,OwningProcess
```

如果确认是旧的本项目服务，可以按“停止服务”里的命令停止后再启动。

### 前端能打开但请求失败

确认后端已经监听 8000：

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

前端 `package.json` 已配置：

```json
"proxy": "http://localhost:8000"
```

因此本地开发时前端请求 `/api/...` 会代理到后端。

### 模型配置日志里 `api_key_configured=False`

说明当前进程没有读到 `ACTIVITY_AGENT_LLM_API_KEY`。检查：

```powershell
Get-Content .env |
  Where-Object { $_ -match "^ACTIVITY_AGENT_LLM_API_KEY=" } |
  ForEach-Object { "ACTIVITY_AGENT_LLM_API_KEY=***" }
```

不要把 key 值提交到代码仓库或贴到日志里。

## 7. 验证命令

配置和 SDK 相关测试：

```powershell
python -m unittest tests.test_config_dotenv tests.test_mvp_sdk
```

前端构建验证：

```powershell
cd frontend
npm run build
```
