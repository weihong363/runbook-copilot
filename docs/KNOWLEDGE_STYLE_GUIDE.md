# 知识库编写规范

这份规范用于约束 `knowledge/` 中的 Markdown 文档格式，目标是让 ingest、metadata 提取和 hybrid retrieval 更稳定。

## 适用范围

当前支持四类知识文档：

- `runbook`
- `incident`
- `service`
- `faq`

文件名、标题或正文前部应明确包含其中一种类型，便于系统识别 `doc_type`。

## 基本格式

每份文档建议遵循以下结构：

```md
# 文档标题
tags: service-name, dependency, topic

## 二级标题
正文内容
```

硬性要求：

- 第一行附近必须有一级标题 `# 标题`
- 前 20 行内必须有 `tags:` 行
- 至少有一个二级标题 `## ...`
- 文档内容必须是 UTF-8 编码

建议要求：

- `tags` 全部使用小写，使用英文逗号分隔
- `tags` 中包含服务名
- 标题直接写服务名和问题类型，不要写模糊标题
- 二级标题尽量表达“场景 / 操作 / 结论”，不要只写“其他”

## 推荐 metadata

当前系统会从文档中推断或抽取这些 metadata：

- `title`
- `doc_type`
- `path`
- `tags`
- `service`
- `heading`
- `heading_level`

推荐你在写文档时显式保证以下信息存在：

- 服务名：如 `order-service`、`checkout-api`
- 依赖名：如 `redis`、`postgres`
- 故障关键词：如 `timeout`、`deadlock`、`connection`
- 文档类型：runbook / incident / service / faq

## 各类型建议结构

### Runbook

推荐章节：

- `## 适用场景`
- `## 快速判断`
- `## 处理步骤`
- `## 后续沉淀`

适合写什么：

- 具体告警或错误模式
- 核心判断信号
- 可执行检查步骤
- 回滚、降级、缓解动作

### Incident

推荐章节：

- `## 事故背景`
- `## 影响范围`
- `## 处置过程`
- `## 根因`
- `## 改进项`

适合写什么：

- 已发生事故的复盘信息
- 时间线、影响面、真实根因

### Service

推荐章节：

- `## 服务职责`
- `## 核心依赖`
- `## 常见故障`
- `## 排查入口`

适合写什么：

- 服务介绍
- 依赖关系
- 常见排障入口

### FAQ

推荐章节：

- `## 常见问题标题`
- `## 另一个问题标题`

适合写什么：

- 高频、短答型问题
- 登录失败、401、配置错误、常见误用

## tags 约定

推荐至少包含 3 类标签：

- 服务名：如 `order-service`
- 依赖或中间件：如 `redis`、`postgres`
- 故障主题：如 `timeout`、`deadlock`、`latency`

示例：

```md
tags: order-service, redis, connection, timeout
```

不建议：

- 中文和英文标签混杂
- 过于宽泛的标签，如 `bug`、`problem`
- 不带服务名

## 文件命名建议

建议文件名遵循：

```text
runbook-<service>-<topic>.md
incident-<service>-<topic>.md
service-<service>.md
faq-<service>.md
```

示例：

- `runbook-order-service-redis.md`
- `incident-checkout-api-db-timeout.md`
- `service-search-api.md`
- `faq-auth-service.md`

## lint 使用方式

执行：

```bash
python scripts/lint_knowledge.py
```

lint 会检查：

- 标题是否存在
- `tags:` 是否存在
- 文档类型是否可识别
- 是否至少有一个二级标题
- 是否能提取出 service
- runbook 是否建议补齐常用章节

## 模板与示例

模板目录：

- [runbook_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/runbook_template.md)
- [incident_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/incident_template.md)
- [service_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/service_template.md)
- [faq_template.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_templates/faq_template.md)

示例目录：

- [incident-checkout-api-db-timeout.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_examples/incident-checkout-api-db-timeout.md)
- [service-order-service.md](/Users/ironion/workspace/runbook-copilot/docs/knowledge_examples/service-order-service.md)
