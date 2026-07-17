# PROGRESS — 开发进度

> Coding Agent 每次阶段性工作前后应阅读并更新本文件。

## 当前状态

**阶段：MVP 已完成，可本地演示与远程浏览代码。**

远程：https://github.com/HarmmerRay/user_growth_analytics  
本地站点（Docker 运行时）：http://development.localhost:8000  
账号：`Administrator` / `admin`

## 已完成

- [x] 仓库初始化（根目录 = Frappe App）
- [x] Docker 开发路径（`docker/`、`scripts/dev-up.sh`、frappe_docker 挂载约定）
- [x] DocType：`User Service Event`
- [x] 安装灌数：`install.py` / `after_install`（近 12 个月示例数据）
- [x] Script Report：`User Growth Summary`
- [x] Page + API：`user-growth-dashboard` + `api/dashboard.py`
- [x] 大屏 CSS 与 Desk 入口
- [x] README 产品与启动说明
- [x] 推送 GitHub `main`
- [x] 根目录文档：`PRODUCT.md` / `AGENTS.md` / `ARTITECHTURE.md` / `PROGRESS.md`
- [x] `.agents/` 目录占位（内容暂空）

## 入口 URL（本地）

| 功能 | URL |
|------|-----|
| 单据 | `/app/user-service-event` |
| 报表 | `/app/query-report/User%20Growth%20Summary` |
| 大屏 | `/app/user-growth-dashboard` |

## 进行中

- 无（等待下一轮需求）

## 待办（可选增强，未排期）

- [ ] Workspace / 桌面快捷入口，降低 Desk 内搜索成本
- [ ] 报表与大屏共用更薄的聚合函数，进一步去重
- [ ] 导出 / 定时邮件订阅增长摘要
- [ ] 权限角色细分（只读分析角色 vs 录入角色）
- [ ] `.agents/skills`、`.agents/tasks` 按需补充

## 验证记录（最近一次）

- migrate 成功，DocType / Report / Page 已注册  
- `get_dashboard_data` 与 Report `execute` 可返回聚合结果  
- `bench start` 下站点 HTTP 200  
- 示例事件数量量级：约数百条（开通 + 流失）

## Agent 接续提示

1. 先读 `PRODUCT.md`、`ARTITECHTURE.md`、本文件。  
2. 遵守 `AGENTS.md`（复用优先、一种简洁实现、不写笼统兜底）。  
3. `.agents/` 目前为空，技能与任务文件有需要再补。  
4. 改完功能后更新本文件的「已完成 / 进行中 / 待办」与验证方式。
