# User Growth Analytics

Frappe 自定义 App（笔试交付）：用户服务开通/流失单据、增长报表、投屏大屏。

- 仓库根目录即为可安装 App（`bench get-app` / `install-app` 可直接使用）
- 本地通过 Docker（官方 `frappe_docker`）运行，**无需本机安装** MariaDB / Redis / bench
- 远程仓库：https://github.com/HarmmerRay/user_growth_analytics

---

## 1. 题目要求与交付物

| # | 要求 | 本仓库实现 |
|---|------|------------|
| 1 | 用户服务开通/流失信息单据（DocType）+ 预设 mock 数据 | `User Service Event` + `install.py` 自动灌数 |
| 2 | 用户增长数据报表（Report） | Script Report：`User Growth Summary` |
| 3 | 用户增长数据大屏（Page） | Desk Page：`user-growth-dashboard` |

三者共用同一数据源：`User Service Event`（开通/流失事件流）。

---

## 2. 整体开发路径（从 0 到可演示）

下面按**实际实施顺序**说明整条链路，方便评审复现，也方便二次开发。

```text
本机只有 Docker
    │
    ▼
① 准备项目仓库（本 App 在仓库根目录）
    │
    ▼
② clone frappe_docker + 自定义 compose（挂载仓库根目录）
    │
    ▼
③ 启动容器：MariaDB / Redis / frappe(bench 镜像)
    │
    ▼
④ 容器内 installer.py 初始化 bench + site（Frappe v15，不装 ERPNext）
    │
    ▼
⑤ 将本仓库软链到 apps/user_growth_analytics 并 install-app
    │
    ▼
⑥ 实现 DocType → migrate → after_install 灌 mock
    │
    ▼
⑦ 实现 Script Report（基于 DocType 聚合）
    │
    ▼
⑧ 实现 Page + API（大屏只读聚合）
    │
    ▼
⑨ bench start → 浏览器验证 → 推送 GitHub
```

### 阶段 A：环境选型

本机未预装 Frappe/bench。可选路线：

| 方案 | 结论 |
|------|------|
| 本机裸装 bench | 依赖多（MariaDB/Redis/Node/Python），macOS 成本高 |
| 只交静态 App 代码、不跑环境 | 能交卷，但难自测 |
| **Docker（本仓库采用）** | 官方 `frappe_docker` 开发容器，可完整跑通 Desk/报表/大屏 |

技术版本（当前开发环境）：

- Frappe：**version-15**
- 站点：`development.localhost`
- 数据库：MariaDB 11.8（容器内，root 密码 `123`）
- 缓存/队列：Redis（独立容器）

### 阶段 B：仓库与目录约定

为方便笔试提交，**Git 仓库 = App 本体**，而不是整个 bench：

```text
user_growth_analytics/          ← git root = Frappe App
├── user_growth_analytics/       ← Python 包
├── pyproject.toml
├── docker/                      ← 可复现的 compose / apps 清单
├── scripts/dev-up.sh            ← 一键拉起容器
├── frappe_docker/               ← 本地 clone，已 gitignore，不入库
└── development -> frappe_docker/development   ← 兼容 bench venv 路径
```

容器内关键挂载（见 `docker/docker-compose.yml`）：

| 容器路径 | 含义 |
|----------|------|
| `/workspace` | 宿主机项目根目录（本 App） |
| `/workspace/development` | 指向 `frappe_docker/development`（bench 所在） |
| `/workspace/development/frappe-bench/apps/user_growth_analytics` | 软链到 `/workspace`，改代码即生效 |

### 阶段 C：拉起 Docker 与初始化 bench

**前置：** 安装并启动 Docker Desktop（建议内存 ≥ 4GB）。

```bash
# 1) 克隆本仓库
git clone https://github.com/HarmmerRay/user_growth_analytics.git
cd user_growth_analytics

# 2) 启动依赖容器（自动 clone frappe_docker、拷贝 compose、建兼容软链）
./scripts/dev-up.sh

# 3) 首次：初始化 bench + 安装 App + 启动（约数分钟）
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

说明：

1. `installer.py -j apps-frappe-only.json`：只装 Frappe，**不装 ERPNext**，启动更快、依赖更少  
2. `apps-frappe-only.json` 内容为 `[]`（见 `docker/apps-frappe-only.json`）  
3. `install-app` 会触发 `hooks.after_install` → 自动写入 mock 数据  
4. 默认管理员：`Administrator` / `admin`

### 阶段 D：实现 DocType（数据底座）

路径：

```text
user_growth_analytics/user_growth_analytics/doctype/user_service_event/
├── user_service_event.json   # 字段、权限、命名规则
└── user_service_event.py     # 校验逻辑
```

字段设计（开通/流失统一事件）：

- 用户：`user_id` / `user_name`
- 事件：`event_type`（开通 / 流失）、`event_date`
- 维度：`service_plan`、`region`、`channel`、`device`
- 金额：`mrr_amount`（开通记新增 MRR，流失记流失 MRR）

命名：`USE-.YYYY.-.#####`

同步到站点：

```bash
bench --site development.localhost migrate
```

### 阶段 E：预设 mock 数据

路径：`user_growth_analytics/install.py`

- 在 `hooks.py` 注册：`after_install = "user_growth_analytics.install.after_install"`
- 生成近 **12 个月**开通/流失事件（地区、渠道、套餐、MRR 带权重）
- 若库中已有数据则跳过，避免重复安装重复灌数

手动重灌：

```bash
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development/frappe-bench &&
  bench --site development.localhost mariadb -e "DELETE FROM \`tabUser Service Event\`" &&
  bench --site development.localhost execute user_growth_analytics.install.seed_mock_data
'
```

### 阶段 F：实现增长报表（Report）

路径：

```text
.../report/user_growth_summary/
├── user_growth_summary.json   # Script Report 元数据
├── user_growth_summary.py     # execute() 聚合
└── user_growth_summary.js     # 筛选器
```

能力：

- 按月统计：开通数、流失数、净增长、期末活跃(估)、流失率、MRR
- 筛选：日期范围、地区、套餐
- 返回折线图 + 顶部 summary 指标

验证：

```bash
bench --site development.localhost execute \
  user_growth_analytics.user_growth_analytics.report.user_growth_summary.user_growth_summary.execute
```

### 阶段 G：实现大屏 Page

路径：

```text
user_growth_analytics/api/dashboard.py          # 白名单 API 聚合
.../page/user_growth_dashboard/
├── user_growth_dashboard.json
└── user_growth_dashboard.js                   # frappe.Chart 渲染
public/css/user_growth_dashboard.css           # 投屏样式
```

数据流：

```text
Page JS ──xcall──▶ api.dashboard.get_dashboard_data
                         │
                         ▼
                 查询 User Service Event
                         │
                         ▼
              KPI / 趋势 / 地区 / 渠道 / 套餐
```

大屏特性：深色投屏布局、KPI 卡片、多图联动、约 60 秒自动刷新。

验证：

```bash
bench --site development.localhost execute user_growth_analytics.api.dashboard.get_dashboard_data
```

### 阶段 H：日常开发与自测循环

代码改完后常用命令（均在容器内 `frappe-bench` 目录）：

```bash
# 进入容器
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash
cd /workspace/development/frappe-bench

# DocType / Report / Page JSON 变更后
bench --site development.localhost migrate
bench --site development.localhost clear-cache
bench build --app user_growth_analytics

# 重启（若已在跑 bench start，前端 watch 多数情况会热更新）
bench start
```

浏览器验证清单：

1. 登录 http://development.localhost:8000 （`Administrator` / `admin`）  
2. Desk 打开 **User Service Event**，确认 mock 列表  
3. 打开报表 **User Growth Summary**，看月度曲线与汇总  
4. 打开 **/app/user-growth-dashboard**，确认大屏图表  

若本机无法解析域名，在 `/etc/hosts` 增加：

```text
127.0.0.1 development.localhost
```

### 阶段 I：提交远程

```bash
git add .
git commit -m "Describe your change"
git push origin main
```

本仓库已推送至：https://github.com/HarmmerRay/user_growth_analytics

---

## 3. 评审快速复现（最短路径）

```bash
git clone https://github.com/HarmmerRay/user_growth_analytics.git
cd user_growth_analytics
./scripts/dev-up.sh

docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development
  python installer.py -j apps-frappe-only.json -t version-15 -a admin
  cd frappe-bench
  ln -sfn /workspace apps/user_growth_analytics
  ./env/bin/python -m pip install -e apps/frappe -e /workspace
  echo user_growth_analytics >> sites/apps.txt
  bench --site development.localhost install-app user_growth_analytics
  bench --site development.localhost set-config developer_mode 1
  bench start
'
```

然后打开：

| 功能 | 入口 |
|------|------|
| 单据 | Desk 搜索 `User Service Event` |
| 报表 | Desk 搜索 `User Growth Summary` |
| 大屏 | `/app/user-growth-dashboard` |

---

## 4. 目录结构（对照开发路径）

```text
.
├── README.md                          # 本文：需求 / 路径 / 复现
├── pyproject.toml                     # App 包装
├── license.txt
├── scripts/dev-up.sh                  # 阶段 C：拉起 Docker
├── docker/
│   ├── docker-compose.yml             # 挂载项目根、端口 8000
│   └── apps-frappe-only.json          # 仅 Frappe，不装 ERPNext
└── user_growth_analytics/
    ├── hooks.py                       # after_install、静态资源
    ├── install.py                     # 阶段 E：mock 数据
    ├── api/dashboard.py               # 阶段 G：大屏 API
    └── user_growth_analytics/
        ├── doctype/user_service_event/    # 阶段 D
        ├── report/user_growth_summary/    # 阶段 F
        └── page/user_growth_dashboard/    # 阶段 G
```

本地运行时才会出现（已 gitignore，勿提交）：

```text
frappe_docker/                 # 官方开发环境 clone
development -> ...             # 路径兼容软链
frappe-bench/                  # bench、sites、env、日志
```

---

## 5. 设计要点

1. **单一事实来源**：开通/流失都落在 `User Service Event`，报表与大屏只做只读聚合，避免双写不一致。  
2. **报表侧重分析**：连续月份轴 + 期末活跃估算 + 流失率 + MRR，便于看增长质量。  
3. **大屏侧重展示**：KPI + 多维分布（地区/渠道/套餐），适合投屏；样式独立 CSS，不依赖 ERPNext。  
4. **可复现优先**：Docker + 脚本 + README 路径说明，评审机器只需 Docker。

---

## 6. 常见问题

**Q: `bench` 报找不到 `frappe` 模块？**  
多为 venv 路径与挂载不一致。确保存在软链 `development -> frappe_docker/development`，并在 bench 内执行：

```bash
./env/bin/python -m pip install -e apps/frappe -e /workspace
```

**Q: 安装 App 后没有 mock 数据？**  

```bash
bench --site development.localhost execute user_growth_analytics.install.seed_mock_data
```

**Q: 改了 JS/CSS 页面没更新？**  

```bash
bench build --app user_growth_analytics
bench --site development.localhost clear-cache
```

**Q: 端口被占用？**  
默认映射 `8000-8005`、`9000-9005`，可在 `docker/docker-compose.yml` 调整。

---

## License

MIT
