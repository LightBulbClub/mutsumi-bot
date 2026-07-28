# ZZZeroUID → mutsumi-bot 模块移植方案

> **日期**: 2026-07-21
> **目标**: 将 ZZZeroUID 完整移植为 mutsumi-bot 的 `modules/zzzerouid`，不依赖 `gsuid_core`。

---

## 全局约束

- Python `>=3.12,<3.14`（跟随 mutsumi-bot）。
- 数据库使用 Tortoise ORM，模型放在 `modules/zzzerouid/database/models.py`。
- 配置使用 `core.config.Config` / `@module.config`，配置键统一小写。
- 消息使用 `core.builtins.message.internal.Image` / `Plain` / `I18NContext` + `MessageSession.finish()`。
- 日志使用 `core.logger.Logger`。
- 调度使用 `core.scheduler.Scheduler` + `@module.schedule`。
- HTTP 优先使用 `core.utils.http.get_url/post_url/download`；米游社自定义 header 场景可内部用 `httpx.AsyncClient`。
- 代码风格：跟随 mutsumi-bot（Ruff line-length 120，double quotes）。
- 资源根目录：`assets/modules/zzzerouid/`。
- 所有命令均为英文。

---

## 英文命令设计

| 原中文命令 | 英文命令 | 说明 |
|---|---|---|
| 绑定uid | `~zzz bind uid <uid>` | UID 绑定 |
| 切换uid | `~zzz switch uid [uid]` | 切换主 UID |
| 删除uid | `~zzz unbind uid <uid>` | 解绑 UID |
| 查询 | `~zzz info` | 玩家信息汇总 |
| mr / 便签 | `~zzz stamina` / `~zzz note` | 体力/每日 |
| 刷新面板 | `~zzz refresh card` | 刷新角色面板 |
| 查询 <角色> | `~zzz card <character>` / `~zzz character <character>` | 查询角色面板 |
| 练度统计 | `~zzz roster` / `~zzz characters` | 角色练度统计 |
| 抽卡记录 | `~zzz gacha` / `~zzz gacha log` | 抽卡记录 |
| 刷新抽卡记录 | `~zzz refresh gacha` | 刷新抽卡记录 |
| 深渊 | `~zzz abyss` / `~zzz challenge` | 式舆防卫战 |
| 零号空洞 | `~zzz hollow` / `~zzz zero` | 零号空洞 |
| 危局强袭战 | `~zzz mem` / `~zzz dangerous` | 危局强袭战 |
| 临界推演 | `~zzz void` / `~zzz critical` | 临界推演 |
| 签到 | `~zzz sign` | 米游社签到 |
| 全部重签 | `~zzz resign` | 全部重签 |
| 绳网月报 | `~zzz monthly` / `~zzz ledger` | 月报 |
| 角色攻略 <角色> | `~zzz guide <character>` | 角色攻略 |
| 清空公告红点 | `~zzz ann` | 清空公告红点 |
| 下载全部资源 | `~zzz download` / `~zzz update assets` | 下载资源 |
| 帮助 | `~zzz help` | 帮助 |

---

## 目录结构

```
modules/zzzerouid/
├── __init__.py
├── config.py
├── locales/
│   └── zh_cn.json
├── database/
│   ├── __init__.py
│   └── models.py
├── api/
│   ├── __init__.py
│   ├── api.py
│   ├── models.py
│   ├── base_request.py
│   ├── request.py
│   └── sign_request.py
├── utils/
│   ├── __init__.py
│   ├── event_adapter.py
│   ├── bot_adapter.py
│   ├── uid.py
│   ├── hint.py
│   ├── message.py
│   ├── logger.py
│   ├── image.py
│   ├── fonts.py
│   ├── name_convert.py
│   ├── alias.py
│   └── resource.py
├── commands/
│   ├── __init__.py
│   ├── user.py
│   ├── stamina.py
│   ├── roleinfo.py
│   ├── char_detail.py
│   ├── char_list.py
│   ├── gachalog.py
│   ├── challenge.py
│   ├── abyss.py
│   ├── mem.py
│   ├── void.py
│   ├── sign.py
│   ├── month_info.py
│   ├── wiki.py
│   ├── ann.py
│   ├── help.py
│   └── resource.py
└── assets/
```

资源实际位置：

```
assets/modules/zzzerouid/
├── texture2d/
├── fonts/
├── resource/
│   ├── weapon/
│   ├── role/
│   ├── role_circle/
│   ├── role_general/
│   ├── suit/
│   ├── 3d_suit/
│   ├── camp/
│   ├── mind/
│   └── square_bangbo/
├── guide/
│   ├── cat/
│   └── flower/
├── custom/
├── wiki/
├── zzz_data/
│   └── char/
└── players/
```

---

## 数据库模型

参考 `modules/maimai/database/models.py`，定义：

- `ZzzUidBind`：用户 -> UID 绑定（支持多 UID，主 UID 标记）。
- `ZzzCookie`：UID -> Cookie / SToken / device_id / device_fp / mys_id。
- `ZzzPush`：推送订阅（体力、签到、公告红点）。

---

## 米游社 API 重写策略

1. 从 `gsuid_core/utils/api/mys/tools.py` 迁移 DS Token 生成。
2. 从 `gsuid_core/utils/api/mys/base_request.py` 改写 HTTP 基类。
3. 从 `gsuid_core/utils/api/mys/request.py` 迁移游戏数据 API。
4. 从 `gsuid_core/utils/api/mys/sign_request.py` 迁移签到 API。
5. 将 `ZZZeroUID/utils/api/request.py` 中的 `ZzzApi` 改为继承本地 `BaseMysApi`。

---

## 分阶段实施计划

| 阶段 | 内容 | 产出 |
|---|---|---|
| P1 | 模块骨架 + 配置 + 数据库模型 + 资源路径 | `~zzz` 可加载，绑定命令可用 |
| P2 | 米游社 API 基类（DS、header、cookie、错误码） | `ZzzApi` 可请求官方接口 |
| P3 | UID 绑定/切换/删除 + 玩家信息查询 | `~zzz bind uid`, `~zzz info` |
| P4 | 体力、深渊、零号空洞、危局、临界、月报 | 查询类命令全部可用 |
| P5 | 角色面板 + 练度统计 | `~zzz refresh card`, `~zzz card <char>`, `~zzz roster` |
| P6 | 抽卡记录 | `~zzz gacha`, `~zzz refresh gacha` |
| P7 | 签到 + 推送 | `~zzz sign`, `~zzz resign`, 自动签到/体力推送 |
| P8 | Wiki/攻略 + 帮助 + 资源下载 | `~zzz guide <char>`, `~zzz help`, `~zzz download` |
| P9 | 清理 gsuid_core 残留、Ruff、测试 | 全部命令通过测试 |

---

## 关键风险

1. DS Token / Salt 可能随米游社版本更新而失效。
2. Cookie 与 SToken 需用户手动提供。
3. 验证码/风控逻辑需简化处理。
4. 资源 CDN 稳定性。
5. PIL 图片生成在 Pillow 12 下的兼容性。
