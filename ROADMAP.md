# Python Xboard Admin API Wrapper — Roadmap

**创建日期:** 2026-07-22
**测试机:** 192.168.31.148 (Ubuntu 24.04, Xboard 非Docker部署)
**测试机 Base URL:** `http://192.168.31.148/api/v2/4ec3c529/`
**Python 环境:** conda `vpn` (Python 3.12.13)

---

## 项目结构

```
xboard-api/
├── xboard_api/                    # 核心包
│   ├── __init__.py
│   ├── client.py                 # XboardClient: HTTP 会话、认证、统一请求
│   ├── auth.py                   # Token 生成/加载/持久化
│   ├── exceptions.py             # 统一异常体系
│   ├── models.py                 # 可选: 响应数据类型
│   └── resources/                # 按 API 域分模块
│       ├── __init__.py
│       ├── base.py               # BaseResource: 共用 CRUD + 分页逻辑
│       ├── config.py             # 站点配置 (6 endpoints)
│       ├── plan.py               # 套餐 (5 endpoints)
│       ├── server.py             # 服务器组/路由/节点/机器 (24 endpoints)
│       ├── user.py               # 用户 (9 endpoints)
│       ├── order.py              # 订单 (5 endpoints)
│       ├── stat.py               # 统计 (8 endpoints)
│       ├── notice.py             # 公告 (4 endpoints)
│       ├── ticket.py             # 工单 (3 endpoints)
│       ├── coupon.py             # 优惠券 (5 endpoints)
│       ├── gift_card.py          # 礼品卡 (12 endpoints)
│       ├── knowledge.py          # 知识库 (5 endpoints)
│       ├── payment.py            # 支付 (7 endpoints)
│       ├── system.py             # 系统 (5 endpoints)
│       ├── theme.py              # 主题 (5 endpoints)
│       ├── plugin.py             # 插件 (10 endpoints)
│       ├── traffic_reset.py      # 流量重置 (4 endpoints)
│       ├── staff.py              # Staff 端点 (1 endpoint)
│       └── mail_template.py      # 邮件模板 (5 endpoints)
├── tests/                        # 测试脚本
│   └── test_logs/                # 测试日志归档
│       └── 2026-07-22/
│           └── ...
├── pyproject.toml
└── README.md
```

---

## Phase 1: 基础设施

| #   | 任务                                     | 验收标准                                                                           |
| --- | ---------------------------------------- | ---------------------------------------------------------------------------------- |
| 1.1 | **Token 生成**：在测试机上生成 Sanctum Bearer token，保存到 `~/.xboard_token` | `curl -H "Authorization: Bearer <token>" http://127.0.0.1/api/v2/4ec3c529/config/fetch` 返回 200 |
| 1.2 | **`XboardClient`** 基类：`_request(method, path, **body)` 统一入口，自动拼接 base_url | 单测过 |
| 1.3 | **`BaseResource`**：继承 `XboardClient`，提供 `_list()`, `_get()`, `_save()`, `_drop()`, `_paginate()` 通用方法 | 单测过 |
| 1.4 | **`exceptions.py`**：`XboardAPIError`, `AuthError`, `NotFound`, `ValidationError` | 异常能正确捕获 |

## Phase 2: 核心资源（高频使用）

| #   | 文件         | 端点                  | 测试重点                                   |
| --- | ------------ | --------------------- | ------------------------------------------ |
| 2.1 | `config.py`  | fetch, save, getEmailTemplate, getThemeTemplate, testSendMail | **读取当前配置 + 保存后还原**             |
| 2.2 | `plan.py`    | fetch, save, drop, update, sort | **创建测试套餐 → 查列表 → 删除**          |
| 2.3 | `server.py`  | 全部 24 个端点        | **查节点列表、查机器列表、创建/删除测试机器** |
| 2.4 | `user.py`    | fetch, update, getUserInfoById, generate, resetSecret | **查管理用户、生成测试用户、删除测试用户** |
| 2.5 | `order.py`   | fetch, detail         | 查询订单列表（只读验证）                   |

## Phase 3: 次级资源（中频使用）

| #   | 文件            | 端点    | 测试重点                   |
| --- | --------------- | ------- | -------------------------- |
| 3.1 | `stat.py`       | 全部 8 个 | 查统计仪表盘（只读）       |
| 3.2 | `notice.py`     | 全部 4 个 | 创建/删除测试公告          |
| 3.3 | `ticket.py`     | 全部 3 个 | 创建测试工单 → 回复 → 关闭 |
| 3.4 | `coupon.py`     | 全部 5 个 | 创建/删除测试优惠券        |
| 3.5 | `gift_card.py`  | 全部 12 个 | 模板+码全生命周期          |

## Phase 4: 外围资源（低频使用）

| #   | 文件            | 端点    |
| --- | --------------- | ------- |
| 4.1 | `knowledge.py`  | 全部 5 个 |
| 4.2 | `payment.py`    | 全部 7 个 |
| 4.3 | `system.py`     | 全部 5 个 |
| 4.4 | `theme.py`      | 全部 5 个 |
| 4.5 | `plugin.py`     | 全部 10 个 |

## Phase 5: 收尾

| #   | 任务                         |
| --- | ---------------------------- |
| 5.1 | `traffic_reset.py` + `staff.py` |
| 5.2 | `mail_template.py`           |
| 5.3 | 统一 CLI (`xbapi`)           |
| 5.4 | 更新 AGENTS.md：agent 如何调用 `xbapi` |

---

## 测试铁律

1. **每个函数必须经测试机实际验证** — 不能只靠单元测试
2. **测试日志统一保存**到 `tests/test_logs/<phase>-<module>.log`，每行标注时间戳
3. **增加资源的测试必须在测试后清理**（删除测试数据），只读端点无此要求
4. **日志格式**：`[PASS|FAIL] 时间 方法 路径 → HTTP状态码 关键响应字段`

## 技术约束

- 测试机 base_url: `http://192.168.31.148/api/v2/4ec3c529/`
- Token 生成: SSH 到测试机执行 `php artisan tinker`
- Python 3.12+ (conda env `vpn`)
- 依赖: `requests`（HTTP）
- 测试日志: `tests/test_logs/YYYY-MM-DD/<phase>-<module>.log`
- 无状态设计：每次调用独立，不维护 session
- 项目: `/home/pomni/code/VPN/xboard-api/`
