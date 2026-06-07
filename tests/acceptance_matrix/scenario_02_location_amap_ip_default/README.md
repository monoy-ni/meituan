# 02 集合位置、高德 IP 定位与默认位置验收

## 目标

验证用户信息中包含集合位置；高德 Web 服务 client 支持可 mock 的 IP 定位调用；当用户不给集合点时，系统默认使用奥映世纪轩。

默认集合点：

- 名称：奥映世纪轩
- 地址：住宅区民祥路与平澜路交汇处(地铁6号线丰北站C出口)
- 高德链接：https://surl.amap.com/4sRsg3c1oa7b

## 覆盖点

- `AmapWebServiceClient.ip_location()` 调用 `/v3/ip`
- IP、output、key 参数正确传给高德 client
- 用户不给位置时 `UserRequest` 使用默认集合点、地址、链接和坐标

## 运行

```powershell
python -m unittest discover tests/acceptance_matrix/scenario_02_location_amap_ip_default
```
