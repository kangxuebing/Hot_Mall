# 肥猫商城（Hot_Mall）详细设计文档

> 文档版本：1.0  
> 适用范围：本仓库 `Hot_Mall` 工程（Django 后端 + 模板前端 + Redis + MySQL）  
> 说明：配置中的密钥、数据库口令等敏感信息以占位描述，部署文档中应单独管理。

---

## 1. 项目概述

### 1.1 建设目标

肥猫商城是一套 **B2C 类电商 Web 应用**，面向终端用户提供商品浏览、购物车、下单与支付流程；面向运营/管理员提供 **商品（SKU）管理**、**供应商与进货记录管理**、临期商品查看等能力。

### 1.2 典型用户角色

| 角色 | 说明 |
|------|------|
| 访客 | 可浏览首页、商品列表与详情（部分能力依赖业务配置） |
| 注册用户 | 注册、登录、维护个人信息与收货地址、购物车、下单、支付、订单与评价 |
| 商品/运营人员 | 通过「商品管理（gms）」维护 SKU、图片、条码检索等 |
| 采购/运营人员 | 维护供应商、进货记录（suppliers） |

### 1.3 工程边界

- **包含**：Web 服务端渲染、REST/JSON 混合接口、Redis 会话与购物车、验证码与短信对接、支付宝/微信支付对接（含演示模式）、Whoosh 商品检索（Haystack）。
- **不包含**（除非另行扩展）：独立移动端 App、微服务拆分、容器编排说明（可按部署环境补充）。

---

## 2. 技术栈与运行环境

### 2.1 核心技术栈

| 类别 | 技术 | 版本参考 |
|------|------|-----------|
| 语言 | Python | 3.7+（与依赖兼容） |
| Web 框架 | Django | 3.2.25 |
| 模板 | Django Templates + **Jinja2**（双引擎，`jinja2_env` 注入 `url`、`static`） |
| 数据库 | MySQL | 由 `mysqlclient` 驱动 |
| 缓存 / 结构存储 | Redis | `django-redis` 多库别名 |
| 异步任务 | Celery + Redis（依赖见 `requirements.txt`） | 5.2.x |
| 检索 | django-haystack + Whoosh + jieba | 中文分词检索 |
| 支付 | python-alipay-sdk；微信支付为自研 HTTP 调用 + 演示收银台 | — |
| 前端脚本 | Vue 2.x、Axios、jQuery（部分页面） | 以 `static/js` 为准 |

### 2.2 主要 Python 依赖（节选）

见仓库根目录 `requirements.txt`，主要包括：`Django`、`django-redis`、`Jinja2`、`Pillow`、`celery`、`django-haystack`、`python-alipay-sdk`、`cryptography` / `pycryptodomex` 等。

### 2.3 运行依赖服务

- **MySQL**：业务持久化。
- **Redis**：默认缓存、Session、验证码、浏览历史、购物车等多 DB 隔离。
- **Whoosh 索引目录**：Haystack 配置于 `settings` 中 `HAYSTACK_CONNECTIONS['PATH']`。

---

## 3. 系统总体架构

### 3.1 逻辑分层

```
┌─────────────────────────────────────────────────────────┐
│  浏览器（HTML + CSS + Vue/Axios 局部交互）                │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP(S)
┌───────────────────────────▼─────────────────────────────┐
│  Django（URL 路由 → 视图 → 模板/JSON）                    │
│  - 认证：Session + AUTH_USER_MODEL=users.User           │
│  - 中间件：CSRF、Session、Message、Security 等            │
└───────────┬───────────────────────────────┬─────────────┘
            │ ORM                          │ Redis / Celery
┌───────────▼──────────┐        ┌──────────▼──────────────┐
│  MySQL（业务表）       │        │  Redis（多别名库）       │
└──────────────────────┘        └─────────────────────────┘
```

### 3.2 请求处理链路（概要）

1. `hot_mall/urls.py` 将各业务应用 `include` 到站点根路径（多数业务无前缀命名空间路径）。
2. 视图层：`View` / `ListView` / `CreateView` / `LoginRequiredMixin` / 自定义 JSON Mixin 等组合。
3. 模板层：用户中心、供应商等大量使用 **Jinja2**（`hot_mall/templates` + 应用模板）；部分页面混用 Django 模板语法，以实际文件为准。
4. 静态资源：`STATIC_URL`、`STATICFILES_DIRS` 指向工程 `static` 目录；媒体资源 `MEDIA_*` 用于商品图片等。

### 3.3 认证与授权

- **用户模型**：`AUTH_USER_MODEL = 'users.User'`，继承 `AbstractUser`，扩展 `mobile`、`email_active`、`default_address` 等。
- **登录态**：Session 存于 Redis（`SESSION_ENGINE` 使用 cache backend）。
- **登录校验**：`users.utils.UsernameModelBackend`（在 `settings` 中配置）支持用户名或手机号登录（以代码为准）。
- **接口保护**：`LoginRequiredMixin` / `LoginRequiredJSONMixin` 用于页面与 JSON 接口。

---

## 4. 子系统划分（Django Apps）

### 4.1 应用一览

| App | 职责概要 |
|-----|----------|
| **contents** | 站点首页聚合展示 |
| **users** | 注册/登录/用户中心、地址 CRUD、改密、订单列表入口、浏览历史等 |
| **verifications** | 图形验证码生成与存储、短信验证码发送与校验（依赖 Redis + 第三方短信） |
| **areas** | 省市区数据模型与接口（地址三级联动数据源） |
| **goods** | 商品分类、SPU/SKU、品牌、图片、详情访问统计、评价、条码搜索等 |
| **carts** | 购物车读写（Redis Hash + Set 结构，JSON 与 Cookie 合并逻辑见 `carts.utils`） |
| **orders** | 结算页、订单提交（事务 + 乐观锁扣减库存）、成功页参数 |
| **payment** | 支付宝网页支付、微信支付（Native/演示）、支付结果页、订单评价页路由等 |
| **gms** | 后台商品（SKU）管理：列表、增删改、图片上传、默认图、临期 SKU 列表等 |
| **suppliers** | 供应商 CRUD、供应商进货记录 CRUD/列表/删除 |

### 4.2 全局路由挂载（`hot_mall/urls.py`）

- `admin/`：Django 管理后台。
- `contents`、`users`、`verifications`、`areas`、`goods`、`gms`、`suppliers`、`carts`、`orders`、`payment`：均以 `''` 前缀挂载，注意 **URL 命名冲突需靠路径字符串区分**。
- `search/`：Haystack 自动检索视图。
- 静态与媒体：`static()` / `media()` 开发环境映射。

---

## 5. 核心业务流程设计

### 5.1 用户注册

1. 前端 `register.html` + `register.js`：用户名/手机号唯一性校验、**图形验证码**、短信验证码、协议勾选。
2. 密码策略：前后端与 `users.constants.USER_PASSWORD_REGEX` 对齐（长度、复杂度规则以代码为准）。
3. 服务端 `RegisterView`：校验参数 → 校验短信码（Redis）→ `User.objects.create_user` → 登录并写 Cookie `username`。

### 5.2 用户登录

1. `LoginView`：校验用户名格式与密码长度范围 → `authenticate` → `login` → 合并购物车（`merge_carts_cookies_redis`）→ 跳转 `next` 或首页。

### 5.3 购物车

1. Redis `carts` 库：按用户维度 Hash 存 SKU→数量，Set 存勾选集合（具体键名以 `carts` 视图代码为准）。
2. 支持全选、简单购物车查询等接口（见 `carts/urls.py`）。

### 5.4 下单与库存

1. `OrderSettlementView`：读取地址与勾选 SKU，渲染 `place_order.html`。
2. `OrderCommitView`：`transaction.atomic` 创建 `OrderInfo` / `OrderGoods`；SKU 使用 **乐观锁**（`filter(id, stock=origin).update(...)`）防止超卖；失败回滚并返回 JSON 错误码。
3. 订单号：时间戳 + 用户 ID 补零拼接（字符串主键）。
4. 支付方式：`OrderInfo.PAY_METHODS_ENUM` 包含货到付款、支付宝、**微信支付**；货到付款订单状态与在线支付待支付状态分支不同（见 `orders` 视图）。

### 5.5 支付

- **支付宝**：`python-alipay-sdk` 生成 `alipay_url`，同步跳转；`PaymentStatusView` 验签后写 `Payment` 并更新订单状态。
- **微信支付**：
  - `PaymentView` 根据订单支付方式返回 `wechat_pay_url` 至收银台。
  - `WECHAT_PAY_USE_DEMO` 为真时：演示确认支付；为假且配置齐全时：调用微信 Native 下单并展示二维码；异步通知 `WeChatNotifyView`（解密逻辑见 `payment/wechat_pay.py`）。

### 5.6 供应商与进货

- **供应商**：`tb_supplier` 表，列表分页、创建/修改共用表单模板、删除支持 AJAX JSON。
- **进货记录**：`SupplierPurchaseRecord`，表名 **`tb_supplier_purchase`**（以模型 `Meta.db_table` 与迁移为准），列表 + 修改 + 删除与供应商列表交互风格一致。

### 5.7 商品检索（Haystack）

- 引擎：Whoosh，中文分词后端。
- 入口：`/search/` 与商品侧自动检索视图配置于根路由。

---

## 6. 数据设计（概要）

### 6.1 公共基类

多数业务表继承 `hot_mall.utils.models.BaseModel`，包含 `create_time`、`update_time` 审计字段（抽象模型）。

### 6.2 主要表（节选）

| 逻辑实体 | 表名（示例） | 说明 |
|----------|--------------|------|
| 用户 | `tb_users` | 自定义用户，含手机号等 |
| 地址 | `tb_address` | 省市区外键关联 `areas.Area` |
| 商品分类/品牌/SPU/SKU 等 | `tb_goods_category`、`tb_brand`、`tb_spu`、`tb_sku`… | 详见 `goods/models.py` |
| 订单 | `tb_order_info` | 主键字符串订单号，金额、运费、支付方式、状态 |
| 订单商品 | `tb_order_goods` | 行项目、价格快照、评价字段 |
| 支付流水 | `tb_payment` | 与订单关联，记录第三方交易号 |
| 供应商 | `tb_supplier` | 供应商主数据 |
| 进货记录 | **`tb_supplier_purchase`** | 供应商外键、商品信息、数量金额、时间等 |

> 完整字段定义以各 `models.py` 与迁移文件为准。

### 6.3 Redis 键空间设计（逻辑）

| Cache Alias | 典型用途 |
|-------------|----------|
| `default` | 通用缓存 |
| `session` | Session 后端 |
| `verify_code` | 图形验证码 `img_{uuid}`、短信验证码 `sms_{mobile}` 等 |
| `history` | 用户浏览历史 |
| `carts` | 购物车 Hash / 选中 SKU Set |

---

## 7. 安全设计

### 7.1 Web 安全

- **CSRF**：表单 POST 使用 `csrf_token` / `csrf_input`；Ajax 使用 `X-CSRFToken` 与 Cookie。
- **登录与权限**：`@login_required` 类混入；敏感操作校验资源归属（如订单属于当前用户）。
- **密码存储**：Django 默认 PBKDF2 哈希；注册/改密使用统一复杂度正则。

### 7.2 验证码与短信

- 图形验证码：PIL 生成，字符集剔除易混淆字符；弱干扰策略（见 `verifications/libs/captcha/captcha.py`）。
- 短信验证码：Redis 过期控制；发送前校验图形验证码防刷（见 `SMSCodeView`）。

### 7.3 支付安全

- 支付宝：RSA2 验签，公钥/私钥 PEM 存放于 `payment/keys/`（部署时需保护文件权限）。
- 微信支付：APIv3 签名与回调 AES-GCM 解密；演示模式仅开发环境开启。

---

## 8. 前端与模板设计

### 8.1 技术选择

- 服务端渲染 HTML + 局部 **Vue 2**（自定义分隔符 `[[ ]]` 避免与 Jinja2 `{{ }}` 冲突）。
- **Axios** 调用 JSON 接口；少量 **jQuery** 遗留用于通用组件。

### 8.2 模板引擎策略

- Jinja2 环境：`hot_mall/utils/jinja2_env.py` 注册全局 `url()`、`static()`。
- 业务模板集中于 `hot_mall/templates/` 与各 `apps/**/templates/`（以 `TEMPLATES` 配置加载顺序为准）。

### 8.3 静态与媒体

- 静态：`/static/`。
- 媒体：商品图片等到 `/media/`（具体 `MEDIA_ROOT`/`MEDIA_URL` 以 `settings` 为准）。

---

## 9. 异步任务与日志

### 9.1 Celery

- 邮件异步发送等任务位于 `celery_tasks/email/tasks.py`（具体 Broker/Backend 以运行配置为准）。

### 9.2 日志

- `LOGGING` 在 `settings/dev.py` 中配置格式化与级别；生产环境应输出到文件/采集系统并脱敏。

---

## 10. 配置与环境

### 10.1 多环境设置

- `hot_mall/settings/dev.py`：开发默认配置（含数据库、Redis、Haystack、支付宝沙箱、微信演示开关等）。
- `hot_mall/settings/prod.py`：生产模板（部署时需覆盖 `SECRET_KEY`、`DEBUG`、`ALLOWED_HOSTS`、数据库与支付回调公网 URL 等）。

### 10.2 关键可配置项（示例）

- **数据库**：`DATABASES['default']`。
- **Redis**：`CACHES` 多别名。
- **支付宝**：`ALIPAY_APPID`、`ALIPAY_DEBUG`、`ALIPAY_URL`、`ALIPAY_RETURN_URL`。
- **微信支付**：`WECHAT_PAY_USE_DEMO`、`WECHAT_PAY_MCHID`、`WECHAT_PAY_APPID`、`WECHAT_PAY_API_V3_KEY`、`WECHAT_PAY_SERIAL_NO`、`WECHAT_PAY_PRIVATE_KEY_PATH`、`WECHAT_PAY_NOTIFY_URL`。

---

## 11. 目录结构（高层）

```
Hot_Mall/
├── hot_mall/                 # Django 配置包
│   ├── settings/             # dev / prod
│   ├── urls.py               # 根路由
│   ├── wsgi.py
│   ├── utils/                # 通用工具（Jinja2、响应码、Mixin 等）
│   ├── templates/            # 全局模板（Jinja2 为主）
│   └── apps/                 # 业务应用
│       ├── contents/
│       ├── users/
│       ├── verifications/
│       ├── areas/
│       ├── goods/
│       ├── carts/
│       ├── orders/
│       ├── payment/
│       ├── gms/
│       └── suppliers/
├── static/ 或 hot_mall/static/  # 以 STATICFILES_DIRS 为准
├── celery_tasks/             # Celery 任务包
├── requirements.txt
├── manage.py
└── DESIGN.md                 # 本文档
```

---

## 12. 部署与运维要点（建议）

1. **迁移**：`python manage.py migrate` 同步数据库结构；生产变更需备份与回滚方案。
2. **静态文件**：`collectstatic` 后由 Nginx/CDN 托管；关闭 `DEBUG`。
3. **密钥**：`SECRET_KEY`、支付密钥、数据库口令使用环境变量或密钥管理服务。
4. **监控**：应用日志、MySQL 慢查询、Redis 内存、Celery 队列堆积、支付回调失败率。
5. **索引**：商品检索 Whoosh 索引目录需随数据变更重建策略（实时信号已配置时仍建议定期校验）。

---

## 13. 扩展与演进建议

- **API 化**：逐步将 Vue 页面数据改为统一 REST + JWT/Session，便于多端复用。
- **配置中心**：将硬编码 URL 与密钥迁移到环境变量。
- **测试**：为核心链路（注册、下单、支付回调、库存扣减）补充自动化测试与压测脚本。
- **权限细分**：运营后台路由增加基于角色/组的权限控制（Django Admin 或自定义 RBAC）。

---

## 14. 文档维护

- 代码变更涉及表结构、支付、缓存键约定时，应同步更新本文档对应章节与版本号。
- 若需 **UML/时序图**，可在本仓库另附 `docs/` 下图或链接，本文件保持为文字级「详细设计」主文档。

---

---

## 15. 扩展版交付物（UML / OpenAPI / Word）

- **Word（.docx）**：`docs/Hot_Mall_详细设计说明_扩展.docx` — 含用例、类图、时序图（Mermaid 文本）、OpenAPI 摘要及 **.doc 另存为说明**。重新生成命令：`python3 scripts/generate_design_docx.py`
- **OpenAPI**：`docs/openapi.yaml`
- **Mermaid 图源**：`docs/design_diagrams_mermaid.md`
- **索引**：`docs/README.md`

---

**文档结束**
