# 《山海经》视频制作全流程留痕系统 PRD

**版本**：v4.0
**日期**：2026-05-21
**作者**：AI 辅助生成
**文档状态**：评审稿
**核心变更**：精简冗余、新增 API 设计与错误处理策略、修正数据模型、收窄 MVP 范围


## 1. 项目概述

### 1.1 项目背景

个人创作者利用即梦AI与小云雀等工具的每日免费积分，长期制作《山海经》神兽与植物系列短视频。随着制作体量扩大，面临三大核心挑战：

1. **提示词质量与效率**：手动撰写提示词耗时且质量不稳定，需借助 DeepSeek 模型即时生成高质量、忠于原著的提示词。
2. **风格一致性维护**：系列视频需保持统一的视觉风格，但每次手工撰写提示词容易产生偏差。
3. **制作流程可追溯**：每日工具轮换、积分消耗、提示词版本等数据需系统化记录，否则难以复盘和迭代。

为此，构建一套以 **Hermes Agent 为智能大脑**、以 **Web 留痕系统为操作面板**、以 **本地文件为数据主权载体** 的全流程制作支持系统。

### 1.2 设计理念

**Hermes 负责"想"，留痕系统负责"记"，人负责"审"，数据归用户所有。**

Hermes Agent 是 Nous Research 于 2026 年 2 月发布的开源自进化 AI 智能体框架（GitHub 星标超 10 万），核心特色为内置学习闭环——完成任务后自动提炼经验为可复用 Skill 文件。它负责：调用 DeepSeek API 即时生成提示词、依据 Harmony 风格基线进行风格一致性校验、完成复杂任务后自动沉淀 Skill。

留痕系统负责：排期计划管理与每日任务展示、制作记录的录入查询与追溯、数据的一键导入导出与本地备份。

| 价值维度 | 说明 |
| -------- | ---- |
| **智能化提示词生产** | Hermes Agent 调用 DeepSeek，一键生成符合《山海经》原文、风格统一的图片/视频提示词 |
| **风格一致性守护** | Hermes 从 Harmony 基线出发生成提示词并执行风格审查；优质成果可手动固化为新基线 |
| **全链路可追溯** | 每条制作记录关联原始 AI 提示词、生成结果、手工调整及发布数据 |
| **经验自动沉淀** | Hermes 学习闭环自动将成功经验提炼为 Skill 文件 |
| **数据主权自主可控** | SQLite 存储，支持一键导出 JSON 到本地，离线备份随时恢复 |

### 1.3 产品定位

面向独立视频创作者的 **AI 辅助制作 + 知识管理一体化工作台**。以"计划 → 生成 → 记录 → 沉淀"为闭环。


## 2. 用户角色

| 角色 | 描述 |
| ---- | ---- |
| **主创作者（唯一用户）** | 系统唯一使用者，负责执行每日制作任务、审核 Hermes 生成的提示词、管理 Harmony 基线、定期导出数据备份 |
| **Hermes Agent（系统角色）** | 系统智能大脑，负责调用 DeepSeek 生成提示词、执行风格一致性校验、自动沉淀 Skill |


## 3. 系统架构

### 3.1 整体架构

```
浏览器 (PWA) → Nginx (SSL终端+静态文件) → Flask REST API
                                               ├── Hermes Agent (HTTP) → DeepSeek API
                                               └── SQLite + 文件系统
```

| 组件 | 职责 | 关键技术 |
| ---- | ---- | -------- |
| 留痕系统前端 | 排期管理、制作记录表单、Hermes 交互界面、数据导入导出 | Vue 3 + Naive UI，PWA 支持 |
| Flask 应用服务 | REST API，业务逻辑，用户与 Hermes Agent 的中间层 | Python Flask + SQLAlchemy |
| Hermes Agent | 接收提示词生成/审查请求，调用 DeepSeek API，管理 Skill 库和记忆系统 | Hermes Agent（Nous Research 开源框架） |
| DeepSeek API | 根据系统指令和风格基线即时生成提示词 | DeepSeek 开放平台 API |
| SQLite 数据库 | 存储 plans / records / hermes_logs / harmony_baselines / hermes_skills / daily_quotas | SQLite 3 (WAL 模式) |
| 文件系统 | Harmony 基线模板文件、自动备份文件、成品链接索引 | 服务器本地磁盘 |

Hermes Agent 通过 HTTP REST API 与 Flask 通信，作为独立进程部署在同一 Docker 网络中。Skill 管理依赖文件系统（`~/.hermes/skills/`），记忆持久化使用 SQLite + Markdown 文件。

### 3.2 部署架构

| 项目 | 配置 |
| ---- | ---- |
| 云服务器 | 1 核 CPU / 1 GB 内存 / 20 GB SSD（阿里云/腾讯云，约 50 元/月） |
| 操作系统 | Alibaba Cloud Linux 3 (OpenAnolis Edition, RHEL-based) |
| 部署方式 | Docker Compose 一键部署 |
| SSL 证书 | Let's Encrypt + Certbot 自动续期 |
| 数据备份 | cron 定时任务 + 前端手动导出 |
| DeepSeek 费用 | 按量付费，基础套餐前 100 万次请求免费 |

### 3.3 Docker 资源分配 (1C/1G)

| 容器 | 镜像 | 内存硬限制 | 说明 |
| ---- | ---- | ---------- | ---- |
| Nginx | alpine | 64MB | SSL 终端 + 静态文件服务 |
| Flask | python:3-slim | 256MB | gunicorn -w 1 --threads 2 |
| Hermes Agent | python:3-slim | 512MB | 启用 --low-memory flag |
| **系统预留** | — | ~168MB | OS + Docker daemon |

Flask 必须单 worker（`-w 1`），禁止默认多 worker 复刻。三个容器总硬限制 ≤ 832MB。


## 4. 功能需求

### 4.1 工作台仪表盘

页面加载时自动拉取今日计划任务、计算制作统计、渲染近 7 天活动热力图，并提供快捷入口。

| 功能 | 描述 |
| ---- | ---- |
| 今日制作任务列表 | 从排期库拉取计划日期为今日的任务，按优先级排序 |
| 积分额度面板 | 展示即梦/小云雀当日已用/总额度，支持手动更新 |
| 快捷入口 | "开始制作"、"查询历史"、"导出数据" |
| 今日制作统计 | 已完成数/计划数、积分消耗汇总 |
| 近 7 天活动热力图 | 日历色块展示每日制作产出 |

### 4.2 排期计划管理

三列看板视图（待制作/制作中/已完成），支持拖拽调整状态和日期。

| 功能 | 描述 |
| ---- | ---- |
| 批量导入 | 上传 CSV/JSON 文件，字段：神兽名称、所属经卷、优先级(1-5)、计划日期、推荐工具 |
| 看板视图 | 三列看板，支持拖拽调整 |
| 手动新增 | 弹窗表单新增单个计划项 |
| 编辑与删除 | 单击卡片进入编辑模式 |
| 与制作记录联动 | 记录标记"已完成"后自动更新关联计划状态 |

CSV 导入模板：
```csv
creature,juan,priority,planned_date,recommended_tool
九尾狐,南山经,5,2026-05-21,即梦AI
凤凰,南山经,5,2026-05-22,小云雀
```

### 4.3 制作记录核心流程

制作记录是系统核心模块，每条记录对应一个神兽分镜或完整视频的制作单元，分为四个步骤。

**步骤一：任务绑定**

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| 关联排期计划 | 下拉选择 | 否 | 选择已有计划或"临时任务" |
| 神兽/植物名称 | 文本 | 是 | 若关联计划则自动填充 |
| 制作日期 | 日期 | 是 | 默认为今日 |
| 使用工具 | 多选 | 是 | 即梦AI、小云雀、DeepSeek、可灵、剪映等 |

**步骤二：Hermes Agent 辅助提示词生成**

用户点击"AI 生成提示词"后：Flask 向 Hermes 发送请求（含神兽名称、经卷、风格标签、Harmony 基线 ID）→ Hermes 读取基线 + 调用 DeepSeek → 返回图片提示词和视频动态提示词。

可选勾选"风格审查"：Hermes 将新提示词与 Harmony 基线对比，返回一致性评分(0-100%)、四维度分析（光影/构图/色彩/细节）和修改建议。

用户可：直接采纳、采纳修改建议、手动编辑、重新生成。

| 字段 | 类型 | 来源 |
| ---- | ---- | ---- |
| 图片提示词 | 多行文本 | Hermes 生成 → 用户可编辑 |
| 视频动态提示词 | 多行文本 | Hermes 生成 → 用户可编辑 |
| 负面提示词 | 多行文本 | Hermes 生成（可选） |
| 风格审查结果 | 只读展示区 | Hermes 返回 |
| 使用的风格基线 | 只读标签 | 系统自动填充 |

**步骤三：产出关联与复盘**

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| 积分消耗 | 数字 | 是 | 本次制作实际消耗积分 |
| 成品链接 | URL/路径 | 否 | 最终视频成品链接 |
| 中间产物链接 | URL/路径 | 否 | AI 生成的原始图片/视频片段链接 |
| 制作笔记 | 多行文本 | 否 | 问题、效果评价、优化方向 |
| 完成状态 | 下拉 | 是 | 进行中/已完成/失败（注明原因） |

**步骤四：数据入库与 Hermes 知识沉淀**

| 功能 | 触发条件 | 说明 |
| ---- | -------- | ---- |
| 保存制作记录 | 用户点击"保存" | 所有表单数据写入 records 表 |
| 更新关联计划状态 | 关联计划且状态为"已完成" | plans.status 自动更新 |
| Hermes 调用日志保存 | 自动 | DeepSeek 调用的输入/输出写入 hermes_logs |
| Hermes Skill 自动沉淀 | Hermes 学习循环自动触发 | 完成 5+ 工具调用的复杂任务后自动提炼 Skill |

**界面原型（制作记录表单）**

```
┌──────────────────────────────────────────────────────────────┐
│  制作新记录                                     [关闭]        │
├──────────────────────────────────────────────────────────────┤
│  步骤 1：任务绑定                                            │
│  关联计划：[九尾狐 - 2026-05-21 ▼]  [🔄 临时任务]           │
│  神兽名称：[九尾狐__________________]                        │
│  工具选择：[✓ 即梦AI] [✓ DeepSeek] [  小云雀] [  剪映]       │
├──────────────────────────────────────────────────────────────┤
│  步骤 2：AI 提示词生成                         当前基线：史诗写实风 V2 │
│  风格选择：[史诗写实 ▼]                                      │
│  [✨ 用 Hermes Agent 生成提示词]  [ ] 生成后自动审查风格     │
│                                                              │
│  图片提示词：                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 九尾狐，上古神兽，全身像，白色毛发如丝缎般柔顺…       │   │
│  └──────────────────────────────────────────────────────┘   │
│  视频动态提示词：                                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 九条尾巴从蜷缩到完全展开，毛发在风中轻微飘动…         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ──── 📊 风格一致性审查（基线：史诗写实风 V2）────           │
│  │ ✅ 风格一致: 92%                                         │
│  │ 光影匹配度 88% | 构图一致性 95% | 色彩协调度 93%         │
│  │ ⚠️ 建议："背景雾气浓度可稍降 15%"  [采纳此建议] [忽略]   │
│                                                              │
│  [✅ 采纳并继续]  [✏️ 手动调整]  [🔄 重新生成]              │
├──────────────────────────────────────────────────────────────┤
│  步骤 3：产出与复盘                                         │
│  积分消耗：[30___]  成品链接：[https://...______________]    │
│  制作笔记：[本次毛发质感很棒，下次尝试减少雾气浓度___]       │
│  完成状态：[✅ 已完成 ▼]                                    │
├──────────────────────────────────────────────────────────────┤
│  [💾 保存记录]  [💾 保存并返回工作台]                        │
└──────────────────────────────────────────────────────────────┘
```

### 4.4 Harmony 风格基线管理

Harmony 是用户手动管理的"完美模板"集合——区别于 Hermes 自动沉淀的 Skill 库，Harmony 存放经过人工验证、能定义整个视频系列视觉基调的"美学锚点"。每条基线存储为 Markdown 文件（含 YAML frontmatter 元数据 + 提示词模板）。

| 功能 | 描述 |
| ---- | ---- |
| 基线列表 | 卡片展示所有基线，含名称、版本、风格标签、适用工具、创建时间 |
| 新建基线 | 手动填写基线名称、风格描述、完整提示词模板 |
| 设为当前基线 | 点击"启用"，自动将同类型其他基线取消激活 |
| 基线编辑 | 修改内容自动递增版本号，保留历史版本 |
| 版本历史 | 展示某条基线的所有历史版本，支持查看差异和回滚 |
| 从制作记录导入 | 将效果出色的提示词一键导入为新基线 |

### 4.5 Hermes Agent 集成

系统部署后需预置两个核心 Skill：
- **`DeepSeek 提示词生成`**：读取 Harmony 基线 + 神兽信息 → 拼装系统提示词 → 调用 DeepSeek → 返回图片/视频提示词
- **`风格一致性校验`**：将新提示词与基线从光影/构图/色彩/细节四维度对比 → 返回评分和修改建议

详细的 Skill YAML 定义和 Markdown 正文见技术设计文档。

Hermes 自动沉淀触发条件：完成 5+ 工具调用的复杂任务、修复棘手错误、或发现非平凡工作流。生成的 Skill 遵循 agentskills.io 开放标准，含 YAML frontmatter + Markdown 正文。

### 4.6 查询与追溯

| 功能 | 描述 |
| ---- | ---- |
| 列表查询 | 按日期范围、神兽名称、工具、状态、经卷筛选，支持分页 |
| 关键词搜索 | 全文搜索提示词文本、制作笔记 |
| 时间线视图 | 日历形式展示每日制作产出，点击跳转详情 |
| 详情页 | 展示完整记录：基本信息、提示词、风格审查结果、Hermes 调用日志、成品链接 |
| 统计面板 | 神兽制作进度、工具使用频率、积分消耗趋势、风格一致性评分趋势 |

### 4.7 数据导入导出与备份

| 功能 | 触发方式 | 说明 |
| ---- | -------- | ---- |
| 全量导出 | 点击"导出全部数据" | 生成含所有表的 JSON 文件，文件名含时间戳 |
| 选择性导出 | 筛选结果页点击"导出" | 按条件导出子集 |
| 导入恢复 | 上传 JSON 文件 | 校验格式后合并到现有数据库（去重策略：id + created_at） |
| 自动备份 | cron 每日 03:00 | `sqlite3 .backup` 到 `/backups/` |
| 备份管理 | 前端数据管理页 | 展示备份文件列表，支持下载或删除 |


## 5. API 设计

### 5.1 通用约定

- 前缀：`/api/v1/`
- 统一错误格式：`{"error": {"code": "ERROR_CODE", "message": "人类可读描述"}}`
- 成功响应：`{"data": ...}` 或 `{"data": ..., "pagination": {"page": 1, "per_page": 20, "total": 127}}`

### 5.2 端点清单

| 资源组 | 方法 | 端点 | 说明 |
| ------ | ---- | ---- | ---- |
| **Plans** | GET | `/api/v1/plans` | 计划列表（支持 ?status=&date_from=&date_to=） |
| | POST | `/api/v1/plans` | 创建计划 |
| | GET | `/api/v1/plans/:id` | 计划详情 |
| | PUT | `/api/v1/plans/:id` | 更新计划 |
| | DELETE | `/api/v1/plans/:id` | 删除计划 |
| | POST | `/api/v1/plans/import` | CSV 批量导入 |
| | PATCH | `/api/v1/plans/:id/status` | 更新状态（看板拖拽） |
| **Records** | GET | `/api/v1/records` | 记录列表（分页+筛选） |
| | POST | `/api/v1/records` | 创建记录 |
| | GET | `/api/v1/records/:id` | 记录详情（含关联 hermes_logs） |
| | PUT | `/api/v1/records/:id` | 更新记录 |
| | DELETE | `/api/v1/records/:id` | 删除记录 |
| **Hermes** | POST | `/api/v1/hermes/generate-prompt` | 触发提示词生成 |
| | POST | `/api/v1/hermes/review-style` | 触发风格审查 |
| | GET | `/api/v1/hermes/logs` | 查询 Hermes 调用日志 |
| **Baselines** | GET | `/api/v1/baselines` | 基线列表 |
| | POST | `/api/v1/baselines` | 创建基线 |
| | GET | `/api/v1/baselines/:id` | 基线详情 |
| | PUT | `/api/v1/baselines/:id` | 更新基线（自动递增版本） |
| | DELETE | `/api/v1/baselines/:id` | 软删除基线 |
| | POST | `/api/v1/baselines/:id/activate` | 激活为当前基线 |
| | GET | `/api/v1/baselines/:id/versions` | 版本历史 |
| **Data** | GET | `/api/v1/data/export` | 全量导出 JSON（?scope=filtered 选择性导出） |
| | POST | `/api/v1/data/import` | 上传 JSON 导入 |
| | GET | `/api/v1/data/backups` | 备份文件列表 |
| **Health** | GET | `/api/v1/health` | 健康检查（含 Hermes 连通性状态） |
| **Stats** | GET | `/api/v1/stats` | 仪表盘统计数据 |


## 6. 数据模型

### 6.1 核心表关系

```
plans ────< records >──── hermes_logs
               │
               ├────────── harmony_baselines
               │
               └────────── hermes_skills
```

### 6.2 表结构

#### `plans` — 排期计划

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| creature | TEXT | NOT NULL | 神兽/植物名称 |
| juan | TEXT | — | 所属经卷 |
| priority | INTEGER | DEFAULT 3 | 优先级 1-5 |
| planned_date | DATE | NOT NULL | 计划制作日期 |
| recommended_tool | TEXT | — | 推荐工具 |
| status | TEXT | DEFAULT 'pending' | pending / in_progress / completed / cancelled |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |
| updated_at | DATETIME | — | — |

**索引**：`idx_plans_status_date` (status, planned_date)

#### `records` — 制作记录

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| plan_id | INTEGER | FK → plans(id) | 关联排期计划（可空） |
| work_date | DATE | NOT NULL | 制作日期 |
| creature_name | TEXT | NOT NULL | 神兽/植物名称 |
| tools_used | TEXT (JSON) | — | 工具列表 |
| baseline_id_used | INTEGER | FK → harmony_baselines(id) | 使用的风格基线 |
| prompt_image | TEXT | — | 最终图片提示词 |
| prompt_video | TEXT | — | 最终视频动态提示词 |
| negative_prompt | TEXT | — | 负面提示词 |
| style_review_score | REAL | — | 风格一致性评分 (0-100) |
| style_review_suggestions | TEXT | — | 风格审查修改建议 |
| points_consumed | INTEGER | — | 消耗积分 |
| output_url | TEXT | — | 成品链接 |
| intermediate_urls | TEXT (JSON) | — | 中间产物链接 |
| notes | TEXT | — | 制作笔记 |
| status | TEXT | DEFAULT 'in_progress' | in_progress / completed / failed |
| hermes_skill_version | TEXT | — | Hermes 生成的 Skill 版本号 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |
| updated_at | DATETIME | — | — |

**索引**：`idx_records_creature` (creature_name), `idx_records_date` (work_date), `idx_records_status` (status)

#### `hermes_logs` — Hermes 调用日志

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| record_id | INTEGER | FK → records(id) | 关联制作记录 |
| request_type | TEXT | NOT NULL | 'prompt_generation' / 'style_review' |
| system_prompt | TEXT | — | 发送给 DeepSeek 的系统提示词 |
| user_input | TEXT | — | 发送给 DeepSeek 的用户输入 |
| response_body | TEXT | — | DeepSeek 原始返回 |
| baseline_id_used | INTEGER | FK → harmony_baselines(id) | 使用的基线 |
| tokens_input | INTEGER | — | 输入 token 数 |
| tokens_output | INTEGER | — | 输出 token 数 |
| api_cost | REAL | — | API 费用（元） |
| duration_ms | INTEGER | — | 调用耗时 |
| adopted | BOOLEAN | DEFAULT 0 | 结果是否被采纳 |
| user_edited | BOOLEAN | DEFAULT 0 | 用户是否编辑了结果 |
| error_message | TEXT | — | 错误信息 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |

**索引**：`idx_logs_record` (record_id), `idx_logs_type` (request_type)

#### `harmony_baselines` — 风格基线

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| name | TEXT | NOT NULL | 基线名称 |
| version | INTEGER | DEFAULT 1 | 版本号 |
| tool_type | TEXT | NOT NULL | 适用工具 |
| style_tags | TEXT (JSON) | — | 风格标签列表 |
| prompt_template | TEXT | NOT NULL | 完整提示词模板 |
| file_path | TEXT | — | 对应 Markdown 文件路径 |
| is_active | BOOLEAN | DEFAULT 0 | 是否为当前基线 |
| previous_id | INTEGER | FK → harmony_baselines(id) | 上一版本 |
| source_record_id | INTEGER | FK → records(id) | 来源记录 |
| rating | INTEGER | — | 效果评分 1-5 |
| usage_count | INTEGER | DEFAULT 0 | 被使用次数 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |

**索引**：`idx_baselines_active` (is_active)

#### `hermes_skills` — Skill 注册表

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| skill_name | TEXT | NOT NULL | Skill 名称 |
| version | TEXT | — | 版本号 |
| source | TEXT | DEFAULT 'manual' | 'manual' / 'auto' |
| file_path | TEXT | NOT NULL | Skill 文件路径 |
| description | TEXT | — | 功能描述 |
| trigger_record_id | INTEGER | FK → records(id) | 触发自动生成的记录 |
| is_active | BOOLEAN | DEFAULT 1 | 是否启用 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |

#### `daily_quotas` — 每日额度

| 字段 | 类型 | 约束 | 说明 |
| ---- | ---- | ---- | ---- |
| id | INTEGER | PK AUTOINCREMENT | — |
| date | DATE | NOT NULL UNIQUE | 日期 |
| jimeng_total | INTEGER | DEFAULT 100 | 即梦总额度 |
| jimeng_used | INTEGER | DEFAULT 0 | 即梦已用 |
| seedance_total | INTEGER | DEFAULT 130 | 小云雀总额度 |
| seedance_used | INTEGER | DEFAULT 0 | 小云雀已用 |
| notes | TEXT | — | 备注 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | — |

**索引**：`idx_quotas_date` (date UNIQUE)

### 6.3 数据模型修正说明（相对 v3.0）

1. 删除 `records.hermes_request_id` — `hermes_logs.record_id` 已提供反向关联
2. 所有 FK 约束显式声明（v3.0 仅在 ER 图中标注但表定义中缺失）
3. `harmony_baselines.previous_id` 显式声明自引用 FK


## 7. 非功能需求

### 7.1 性能

| 指标 | 目标 | 说明 |
| ---- | ---- | ---- |
| 页面首屏加载 | < 2s | 含仪表盘渲染 |
| API 查询响应 | < 500ms | 列表查询、详情 |
| API 生成响应 | < 20s | 含 Hermes + DeepSeek 完整链路 |
| Hermes 调用超时 | 30s | 超时后返回错误，允许重试 |
| 并发用户 | 1 | 单用户场景 |

### 7.2 安全

| 需求 | 实现 |
| ---- | ---- |
| 传输安全 | HTTPS (Let's Encrypt) |
| 访问控制 | HTTP Basic Auth 或简单 Token 登录 |
| API Key 保护 | DeepSeek API Key 存服务器环境变量，不暴露前端 |
| 数据隔离 | SQLite 文件权限仅应用用户可读写 |
| 输入校验 | 前后端双重校验，防注入 |

### 7.3 可用性

| 需求 | 实现 |
| ---- | ---- |
| 移动端适配 | 响应式布局，手机竖屏可完成记录填写 |
| PWA 支持 | Service Worker 缓存静态资源（生产环境启用，开发环境禁用） |
| 离线提示 | 网络断开时显示离线提示；Hermes 调用需联网 |
| 错误处理 | API 失败展示明确错误信息 + 重试按钮 |

### 7.4 错误处理与降级策略

**DeepSeek API 调用**：三层防护
1. 重试层：3 次指数退避重试 (1s / 2s / 4s)，超时 30s
2. 降级层：全部重试失败后，返回错误给前端，展示"AI 暂不可用，请手动输入提示词"——核心 CRUD 功能不受影响
3. 熔断层：连续 5 次失败后熔断 60s，期间直接返回降级响应，避免持续无效请求

**Hermes Agent 不可用**：Flask `/health` 返回降级状态，前端展示提示并提供"跳过 AI 辅助"入口。Docker 配置 `restart: unless-stopped`。

**数据库**：所有写操作包裹事务。迁移前自动执行 `sqlite3 .backup`。

### 7.5 可维护性

| 需求 | 实现 |
| ---- | ---- |
| 日志记录 | Flask 日志写入文件，按天轮转，保留 30 天 |
| 数据库迁移 | Flask-Migrate (Alembic) 管理版本 |
| 配置管理 | 所有配置通过环境变量注入，Docker Compose 统一管理 |
| 健康检查 | `/api/v1/health` 返回应用状态和 Hermes Agent 连通性 |

### 7.6 可移植性

| 需求 | 实现 |
| ---- | ---- |
| 数据格式通用 | 导出为 JSON，不依赖特定数据库格式 |
| 无供应商锁定 | SQLite 可跨平台；Hermes 支持多模型提供商切换 |
| 一键部署 | Docker Compose 含全量服务 |
| 数据迁移 | 导入 JSON 即可在新服务器恢复全部数据 |


## 8. 技术选型

| 层次 | 技术 | 版本 | 选型理由 |
| ---- | ---- | ---- | -------- |
| 前端框架 | Vue 3 | 3.4+ | 组合式 API，上手平缓，适合独立开发者快速迭代 |
| UI 组件库 | Naive UI | 2.x | 组件丰富，TypeScript 友好，暗色模式支持 |
| 前端构建 | Vite | 5.x | 极速冷启动，HMR 热更新 |
| 后端框架 | Flask | 3.x | 轻量灵活，SQLAlchemy 集成文档丰富 |
| ORM | SQLAlchemy | 2.x | 模型定义清晰，支持迁移 |
| 数据库 | SQLite | 3.x (WAL) | 零配置，单文件备份，适合单用户场景 |
| 迁移工具 | Alembic (Flask-Migrate) | — | 版本化数据库变更 |
| 智能体框架 | Hermes Agent | latest | 自进化 AI 智能体，学习闭环，Skill 自动沉淀 |
| AI 模型 | DeepSeek (deepseek-chat) | — | 高性价比，中文理解出色 |
| Web 服务器 | Nginx | 1.25+ (alpine) | 反向代理 + SSL 终端 + 静态文件 |
| SSL | Let's Encrypt (Certbot) | — | 免费，自动续期 |
| 容器化 | Docker + Docker Compose | — | 环境一致性，一键部署 |
| Python 依赖管理 | uv | latest | Hermes Agent 推荐，高速依赖解析 |
| 备份 | cron + sqlite3 .backup | — | 简单可靠 |


## 9. 实施路线图

### 9.1 第一阶段：MVP（第 1 周）

**目标**：跑通"排期 → Hermes 生成提示词 → 制作记录保存 → 列表查询"最小闭环并上线。

| 任务 | 产出物 |
| ---- | ------ |
| 项目脚手架搭建 | Flask + Vue 项目骨架 + Docker Compose 配置 |
| 数据库建模（plans, records, hermes_logs） | Alembic 迁移脚本 |
| 排期管理 CRUD API + CSV 导入 | REST API |
| 制作记录 CRUD API | REST API |
| Hermes Agent 部署与连通 + DeepSeek 提示词生成 Skill | 连通性测试通过 |
| 前端核心页面（工作台 + 制作记录表单 + 列表查询） | 可交互页面 |
| Docker 部署上线 + HTTPS 配置 | 域名可访问 |

**MVP 明确不包含**：Harmony 基线管理、风格审查、数据导入导出、自动备份、统计面板、PWA。

### 9.2 第二阶段：增强（第 2 周）

**目标**：上线 Harmony 基线管理 + 风格审查 + 详情页 + 移动端适配。

| 任务 | 产出物 |
| ---- | ------ |
| Harmony 基线 CRUD + 版本管理 + 激活 | 完整功能 |
| 风格审查 Skill 创建 + 集成到制作流程 | 审查结果展示 |
| Hermes 自动沉淀监控面板 | hermes_skills 注册追踪 |
| 制作记录详情页 | 含 Hermes 日志和审查结果展示 |
| 响应式布局优化 | 手机端可完成记录填写 |

### 9.3 第三阶段：打磨（第 3 周）

**目标**：数据管理 + 统计 + PWA + 体验优化。

| 任务 | 产出物 |
| ---- | ------ |
| 数据全量导出 + 选择性导出 + JSON 导入 | 数据管理页 |
| cron 自动备份 + 备份文件管理 | 备份系统 |
| 统计面板（图表可视化） | 统计页 |
| PWA Service Worker + 添加到主屏幕 | 离线缓存 |
| 每日额度管理 + 自动扣减 | 额度面板升级 |


## 10. 风险与应对

| 风险 | 影响 | 概率 | 应对 |
| ---- | ---- | ---- | ---- |
| DeepSeek API 费用超预期 | 制作成本上升 | 中 | 月度预算上限 50 元，系统自动预警；利用免费额度 |
| Hermes Agent 版本升级不兼容 | 功能异常 | 低 | 固定版本号，升级前测试环境验证 |
| 服务器宕机数据丢失 | 记录丢失 | 低 | 双重备份：服务器每日自动 + 用户定期下载 JSON |
| 即梦/小云雀积分政策调整 | 额度变化 | 中 | 每日额度支持手动覆盖，不受硬编码限制 |
| 风格基线偏差积累 | 风格漂移 | 中 | 每次生成执行风格审查；用户定期检查基线 |
| 1G 内存不足 | 服务 OOM | 中 | 严格容器内存限制；Hermes 低内存模式；Flask 单 worker |


## 11. 附录

### 11.1 术语表

| 术语 | 说明 |
| ---- | ---- |
| Hermes Agent | Nous Research 开源的自进化 AI 智能体框架，核心特色为学习闭环与 Skill 自动沉淀 |
| DeepSeek | 深度求索大语言模型，通过 API 提供文本生成服务 |
| Harmony | 风格基线库模块，存放用户手动验证的"完美模板"，作为系列视频视觉锚点 |
| Skill | Hermes Agent 中的可复用程序性知识单元，Markdown 文件存储，可手动创建或自动生成 |
| PWA | Progressive Web App，支持离线缓存和添加到主屏幕 |
| WAL | Write-Ahead Logging，SQLite 日志模式，提升并发写入性能 |
| agentskills.io | 开放 Skill 标准格式，Hermes 自动生成的 Skill 遵循此标准 |

### 11.2 关键依赖与资源

| 资源 | 来源 | 说明 |
| ---- | ---- | ---- |
| Hermes Agent 仓库 | github.com/NousResearch/hermes-agent | 开源框架 |
| DeepSeek 开放平台 | platform.deepseek.com | API 文档与 Key 管理 |
| 即梦 AI | jimeng.jianying.com | 图片/视频生成 |
| 小云雀 Seedance | 对应平台 | 视频生成 |
| 可灵 AI | kling.kuaishou.com | 首尾帧视频生成（备选） |

### 11.3 文档修订记录

| 版本 | 日期 | 修订内容 |
| ---- | ---- | -------- |
| v1.0 | 2026-05-21 | 初稿 |
| v2.0 | 2026-05-21 | 新增 Hermers 知识库设计 |
| v3.0 | 2026-05-21 | 集成 Hermes Agent 开源框架 |
| v4.0 | 2026-05-21 | 精简冗余、新增 API 设计与错误处理策略、修正数据模型、收窄 MVP |

---

**文档交付说明**：本 PRD v4.0 在保留 v3.0 全部架构决策的基础上，精简了冗余内容、补充了 API 设计和错误处理策略、修正了数据模型中的 FK 缺失问题、重新划分了 3 阶段实施路线并收窄了 MVP 范围。可直接交付开发。
