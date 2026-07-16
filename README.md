# User Growth Analytics

基于 Frappe 的**用户增长分析**应用：沉淀用户服务开通/流失事件，提供增长报表与投屏大屏，帮助观察获客、留存与 MRR 变化。

仓库：https://github.com/HarmmerRay/user_growth_analytics

---

## 产品能力

| 模块 | 名称 | 做什么 |
|------|------|--------|
| 单据 | `User Service Event` | 记录用户开通 / 流失事件（套餐、地区、渠道、终端、MRR 等） |
| 报表 | `User Growth Summary` | 按月看开通、流失、净增长、流失率与 MRR，支持筛选与图表 |
| 大屏 | `user-growth-dashboard` | 投屏看板：KPI、趋势、地区 / 渠道 / 套餐分布，定时刷新 |

数据统一落在 `User Service Event`，报表与大屏只做只读聚合。安装后会自动写入近 12 个月示例数据，便于开箱查看效果。

---

## 快速开始

**环境：** Docker Desktop（建议内存 ≥ 4GB）。无需本机安装 MariaDB / Redis / bench。

```bash
git clone https://github.com/HarmmerRay/user_growth_analytics.git
cd user_growth_analytics
./scripts/dev-up.sh

docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development
  if [ ! -d frappe-bench ]; then
    python installer.py -j apps-frappe-only.json -t version-15 -a admin
  fi
  cd frappe-bench
  ln -sfn /workspace apps/user_growth_analytics
  ./env/bin/python -m pip install -e apps/frappe -e /workspace
  grep -q user_growth_analytics sites/apps.txt || echo user_growth_analytics >> sites/apps.txt
  bench --site development.localhost install-app user_growth_analytics || true
  bench --site development.localhost set-config developer_mode 1
  bench --site development.localhost migrate
  bench start
'
```

- 访问：http://development.localhost:8000  
- 账号：`Administrator` / `admin`  
- 若域名无法解析，在 `/etc/hosts` 增加：`127.0.0.1 development.localhost`

### 使用入口

- 单据：Desk 搜索 **User Service Event**
- 报表：Desk 搜索 **User Growth Summary**
- 大屏：`/app/user-growth-dashboard`

### 重新生成示例数据

```bash
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development/frappe-bench &&
  bench --site development.localhost mariadb -e "DELETE FROM \`tabUser Service Event\`" &&
  bench --site development.localhost execute user_growth_analytics.install.seed_mock_data
'
```

---

## 开发路径

从本机只有 Docker，到跑通三套能力，完整链路如下。

```text
Docker 环境
    │
    ▼
clone 本仓库（仓库根目录 = Frappe App）
    │
    ▼
scripts/dev-up.sh
  · 拉取 frappe_docker
  · 使用 docker/docker-compose.yml（挂载项目根到 /workspace）
  · 启动 MariaDB / Redis / frappe 容器
    │
    ▼
容器内 installer.py
  · 初始化 bench + site（Frappe v15，不装 ERPNext）
  · 站点 development.localhost
    │
    ▼
软链 App 到 apps/user_growth_analytics 并 install-app
  · after_install 自动灌入示例数据
    │
    ▼
实现 / 迭代
  · DocType：User Service Event
  · Report：User Growth Summary
  · Page + API：用户增长大屏
    │
    ▼
bench start → 浏览器验证
```

### 运行时目录约定

| 路径 | 含义 |
|------|------|
| 仓库根目录 | 可安装的 Frappe App |
| `/workspace`（容器内） | 宿主机项目根 |
| `/workspace/development` | → `frappe_docker/development`（bench 所在） |
| `apps/user_growth_analytics` | → `/workspace`，改代码即生效 |

`frappe_docker/`、本地 `frappe-bench` 运行时数据已 gitignore，不进入远程仓库。

### 日常开发命令

在容器内 `frappe-bench` 目录：

```bash
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash
cd /workspace/development/frappe-bench

bench --site development.localhost migrate
bench --site development.localhost clear-cache
bench build --app user_growth_analytics
bench start
```

---

## 模块说明

### 1. User Service Event（事件单据）

路径：`user_growth_analytics/user_growth_analytics/doctype/user_service_event/`

- 事件类型：开通 / 流失  
- 维度：套餐、地区、渠道、终端  
- 金额：`mrr_amount`  
- 编号：`USE-.YYYY.-.#####`

### 2. User Growth Summary（增长报表）

路径：`user_growth_analytics/user_growth_analytics/report/user_growth_summary/`

- 按月聚合开通 / 流失 / 净增长 / 期末活跃(估) / 流失率 / MRR  
- 筛选：日期、地区、套餐  
- 附带折线图与顶部汇总指标  

### 3. 用户增长数据大屏

路径：

- API：`user_growth_analytics/api/dashboard.py`
- Page：`.../page/user_growth_dashboard/`
- 样式：`public/css/user_growth_dashboard.css`

```text
大屏 Page ──xcall──▶ get_dashboard_data ──▶ User Service Event
                              │
                              ▼
                   KPI / 趋势 / 地区 / 渠道 / 套餐
```

约 60 秒自动刷新，面向投屏展示。

### 4. 示例数据

路径：`user_growth_analytics/install.py`（`hooks.after_install`）

近 12 个月开通 / 流失样本，带地区、渠道、套餐权重，便于直接看报表和大屏。

---

## 目录结构

```text
.
├── README.md
├── pyproject.toml
├── scripts/dev-up.sh
├── docker/
│   ├── docker-compose.yml
│   └── apps-frappe-only.json      # 仅安装 Frappe
└── user_growth_analytics/
    ├── hooks.py
    ├── install.py                 # 示例数据
    ├── api/dashboard.py           # 大屏聚合
    └── user_growth_analytics/
        ├── doctype/user_service_event/
        ├── report/user_growth_summary/
        └── page/user_growth_dashboard/
```

---

## 设计说明

1. **单一数据源**：开通与流失都记为事件，分析层不另建事实表。  
2. **报表偏分析**：连续月份轴、活跃估算、流失率与 MRR。  
3. **大屏偏展示**：KPI + 多维分布，深色投屏样式，不依赖 ERPNext。  
4. **环境可复现**：Docker + 脚本即可本地跑通。

当前开发栈：Frappe version-15、MariaDB 11.8、Redis（容器内）。

---

## 常见问题

**找不到 `frappe` 模块**

```bash
# 确保存在 development -> frappe_docker/development
./env/bin/python -m pip install -e apps/frappe -e /workspace
```

**安装后没有示例数据**

```bash
bench --site development.localhost execute user_growth_analytics.install.seed_mock_data
```

**改了前端没生效**

```bash
bench build --app user_growth_analytics
bench --site development.localhost clear-cache
```

---

## License

MIT
