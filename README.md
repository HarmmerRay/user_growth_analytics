# User Growth Analytics

Frappe 自定义 App（笔试交付）：用户服务开通/流失单据、增长报表、投屏大屏。

仓库根目录即为可安装 App；本地用 Docker 跑 Frappe，无需本机安装 bench。

## 交付内容

| # | 内容 | 说明 |
|---|------|------|
| 1 | DocType `User Service Event` | 开通/流失事件；安装后自动灌入约 12 个月 mock 数据 |
| 2 | Report `User Growth Summary` | 按月开通/流失/净增长/流失率/MRR，含图表与筛选 |
| 3 | Page `user-growth-dashboard` | 大屏 KPI + 趋势/地区/渠道/套餐分布 |

## 快速启动（Docker）

**前置：** Docker Desktop（建议内存 ≥ 4GB）

```bash
# 启动依赖容器（自动 clone frappe_docker）
./scripts/dev-up.sh

# 首次：进入容器初始化 bench、安装本 App 并启动
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

- 地址：http://development.localhost:8000  
- 账号：`Administrator` / `admin`

若本机无法解析 `development.localhost`，可在 `/etc/hosts` 增加：`127.0.0.1 development.localhost`

### 功能入口

- 单据：Desk 搜索 **User Service Event**
- 报表：Desk 搜索 **User Growth Summary**
- 大屏：Desk 搜索 **用户增长数据大屏**，或打开 `/app/user-growth-dashboard`

### 重新灌 mock 数据

```bash
docker compose -f frappe_docker/.devcontainer/docker-compose.yml exec frappe bash -lc '
  cd /workspace/development/frappe-bench &&
  bench --site development.localhost mariadb -e "DELETE FROM \`tabUser Service Event\`" &&
  bench --site development.localhost execute user_growth_analytics.install.seed_mock_data
'
```

## 目录结构

```
.
├── user_growth_analytics/     # App 代码
│   ├── hooks.py
│   ├── install.py             # after_install 灌数
│   ├── api/dashboard.py       # 大屏聚合 API
│   └── user_growth_analytics/
│       ├── doctype/user_service_event/
│       ├── report/user_growth_summary/
│       └── page/user_growth_dashboard/
├── docker/                    # 开发用 compose 与 apps 清单
├── scripts/dev-up.sh
└── README.md
```

## 设计要点

- 开通与流失统一为事件流 DocType，报表/大屏只做只读聚合
- Script Report 提供连续月份轴与期末活跃估算，便于看增长质量
- 大屏面向投屏：深色氛围、KPI 卡片、自动刷新（60s）

## License

MIT
