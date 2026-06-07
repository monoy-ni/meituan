# Data 文件夹代码说明

## 概述

`data` 文件夹包含了杭州活动规划 Agent 的所有模拟/种子数据，用于演示和开发目的。这些数据是硬编码的，真实使用时需要接入真实的美团 API 或其他数据源。

## 文件结构

```
data/
├── __init__.py
├── hangzhou_catalog.py
└── supply_catalog.py
```

---

## 1. `__init__.py`

简单的模块初始化文件，将 `SUPPLY_CATALOG` 导出，供其他模块使用：

```python
from activity_agent.data.supply_catalog import SUPPLY_CATALOG

__all__ = ["SUPPLY_CATALOG"]
```

---

## 2. `hangzhou_catalog.py`

### 功能
定义了杭州的路线集群和主题模板，用于规划不同类型的行程。

### 主要数据

#### `HANGZHOU_DEMO_VERSION`
- 类型：字符串
- 含义：杭州演示数据的版本号
- 当前值：`"hangzhou_seed_v1.4.0"`

#### `HANGZHOU_ROUTE_CLUSTERS`
- 类型：字典列表
- 含义：杭州的地理片区/路线集群定义
- 包含的字段：
  - `id`: 片区唯一标识符
  - `city`: 城市名称
  - `name`: 片区展示名称
  - `transport_hint`: 交通建议

**片区列表**：
1. `hefang_old_town` - 河坊街/南宋御街
2. `canal_qiaoxi` - 京杭大运河/桥西
3. `westlake_hubin` - 西湖湖滨
4. `longwu_tea_hills` - 龙坞茶山
5. `xixi_wetland` - 西溪湿地
6. `liangzhu_culture` - 良渚文化
7. `xianghu_lake` - 湘湖
8. `wulin_kerry` - 武林/嘉里中心

#### `HANGZHOU_THEME_TEMPLATES`
- 类型：字典列表
- 含义：预设的主题行程模板
- 包含的字段：
  - `id`: 模板唯一标识符
  - `city`: 城市名称
  - `name`: 模板展示名称
  - `duration`: 行程时长（`half_day` 半日 / `full_day` 全日）
  - `route_cluster`: 所属路线集群
  - `experience_tags`: 体验标签
  - `description`: 模板描述
  - `version`: 模板版本号

**主题模板列表**：
1. `hz_old_town_fireworks` - 老城烟火半日局
2. `hz_canal_citywalk` - 运河人文 Citywalk
3. `hz_westlake_easy` - 西湖轻松打卡局
4. `hz_longwu_suburb` - 龙坞茶山近郊局
5. `hz_food_tour` - 杭州特色美食巡游
6. `hz_rainy_indoor` - 雨天室内低耗局

---

## 3. `supply_catalog.py`

### 功能
定义了完整的商家供给目录，包括景点、餐厅、活动、放松场所等。

### 主要数据

#### `SUPPLY_CATALOG`
- 类型：`MerchantSupply` 对象列表
- 含义：所有可用的供给资源
- `MerchantSupply` 包含的字段：
  - `id`: 供给唯一标识符
  - `name`: 供给名称
  - `type`: 供给类型（`ACTIVITY` 活动 / `DINING` 餐饮 / `RELAX` 放松 / `CHECKIN` 打卡 / `NIGHTLIFE` 夜生活 / `HOTEL` 酒店 / `GIFT` 礼物）
  - `price`: 价格
  - `duration_minutes`: 建议时长（分钟）
  - `distance_km`: 距离（公里）
  - `district`: 所属区域
  - `tags`: 标签列表
  - `scene_fit`: 适用场景（`FRIENDS` 朋友 / `COUPLE` 情侣）
  - `booking_modes`: 预订方式
  - `available`: 是否可用
  - `why`: 推荐理由
  - `source_id`: 数据来源标识（`seed_hz_*` 表示杭州种子数据）
  - `address`: 地址
  - `area_cluster`: 所属路线集群
  - `open_dayparts`: 开放时段
  - `weather_fit`: 适用天气
  - `checkin_value`: 打卡价值
  - `local_flavor_tags`: 本地特色标签
  - `transport_hint`: 交通建议

### 杭州特有供给示例

**餐饮类**：
- 河坊街老底子小吃集合点
- 桥西杭帮菜小馆
- 湖滨龙井茶点小馆
- 龙坞茶香农家菜

**活动类**：
- 南宋御街铜艺手作体验
- 西湖湖滨轻游船
- 龙坞茶山轻徒步
- 西溪湿地轻摇橹线
- 良渚文化室内慢逛

**打卡类**：
- 吴山城隍阁夜景打卡点
- 大运河桥西傍晚散步线
- 南山路梧桐夜色打卡

---

## 数据流程图

```
data/
├── supply_catalog.py  →  SUPPLY_CATALOG (商家供给)
└── hangzhou_catalog.py
    ├── HANGZHOU_ROUTE_CLUSTERS (地理片区)
    └── HANGZHOU_THEME_TEMPLATES (主题模板)
            ↓
    SeedLocalDataProvider (数据提供者)
            ↓
    SQLiteRepository (存储到数据库)
            ↓
    ActivityPlanningAgent (Agent 使用)
```

---

## 使用说明

这些数据是用于演示目的的种子数据，真实使用时需要：

1. 接入真实的美团 API 获取实时商家数据
2. 接入地图 API 获取路线和距离数据
3. 接入天气 API 获取实时天气数据
4. 接入交易 API 处理预订和支付

