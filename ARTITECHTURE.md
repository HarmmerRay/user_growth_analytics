# ARTITECHTURE — 技术选型与架构

> 文件名按仓库约定保留为 `ARTITECHTURE.md`。

## 技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| 框架 | Frappe v15 | DocType / Report / Page / 权限 / Desk |
| 语言 | Python 3 + JavaScript | 后端聚合与 Desk 前端 |
| 数据库 | MariaDB 11.8 | Frappe 默认持久化 |
| 缓存 / 队列 | Redis | cache + queue（Docker 独立服务） |
| 本地运行 | Docker（frappe_docker + bench 镜像） | 本机不强制安装 bench |
| 图表 | frappe.Chart | 报表内嵌图 + 大屏图表 |
| 包管理 | 仓库根目录即为 App（pyproject.toml） | `bench install-app` 可装 |

不依赖 ERPNext。

## 逻辑架构

```text
┌─────────────────────────────────────────────────────┐
│                   Frappe Desk                        │
│  List: User Service Event                            │
│  Report: User Growth Summary                         │
│  Page: user-growth-dashboard                         │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
                ▼                     ▼
        Script Report            Whitelisted API
   user_growth_summary.py    api/dashboard.get_dashboard_data
                │                     │
                └──────────┬──────────┘
                           ▼
              ┌────────────────────────┐
              │  User Service Event    │
              │  (单一事实表 / DocType) │
              └────────────────────────┘
                           ▲
                           │
              install.after_install / seed_mock_data
```

## 模块边界

| 模块 | 职责 | 不负责 |
|------|------|--------|
| `doctype/user_service_event` | 事件模型、校验、权限 | 复杂分析 |
| `report/user_growth_summary` | 按月分析、筛选、图表数据 | 投屏 UI |
| `page/user_growth_dashboard` + CSS | 大屏展示与刷新 | 写库 |
| `api/dashboard.py` | 大屏聚合 API | 页面样式 |
| `install.py` | 安装后示例数据 | 运行时业务写入 |

## 数据模型（核心）

**User Service Event**

- `event_type`：开通 | 流失  
- `event_date`、`user_id`、`user_name`  
- `service_plan`、`region`、`channel`、`device`  
- `mrr_amount`、`remark`  
- 命名：`naming_series` → `USE-.YYYY.-.#####`

活跃用户为衍生指标：按时间序用开通减流失估算期末活跃，不单独落「当前活跃」表。

## 运行时拓扑（Docker）

```text
Host
 └── docker compose (.devcontainer)
      ├── mariadb
      ├── redis-cache
      ├── redis-queue
      └── frappe (bench 镜像)
           volume: 项目根 → /workspace
           apps/user_growth_analytics → /workspace
           bench: /workspace/development/frappe-bench
           site: development.localhost:8000
```

关键文件：

- `docker/docker-compose.yml`：挂载与端口  
- `docker/apps-frappe-only.json`：仅装 Frappe  
- `scripts/dev-up.sh`：拉取 frappe_docker 并起容器  

## 前端资产

- 大屏样式：`user_growth_analytics/public/css/user_growth_dashboard.css`  
- hooks 中 `app_include_css` 引入；Page JS 内也会挂 stylesheet  
- 变更后需 `bench build --app user_growth_analytics` 与清缓存  

## 扩展原则

1. 新分析维度优先加 DocType 字段 + 报表/API 聚合，避免新事实表。  
2. 大屏新图表走 `get_dashboard_data` 扩展返回结构，Page 只负责渲染。  
3. 保持 App 可独立安装：不引入未声明的外部 App 依赖。
