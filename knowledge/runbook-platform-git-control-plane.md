# platform-service Git 控制面 Runbook
tags: platform-service, git, control-plane, ssh, http, raw-file, dependency, runbook

## 适用场景

当 Git operations、SSH Git、HTTP Git、raw file access、push、clone、fetch、webhook 或 control plane 同时出现 elevated errors、timeout、unavailable、dependency failure 时，优先使用本 runbook。

## 快速判断

先确认失败是否覆盖所有 Git 操作，还是只影响 push、clone、raw file 或 webhook。若 SSH 和 HTTP Git 同时失败，应优先怀疑共享 control plane、鉴权、存储或边缘代理依赖。

## 处理步骤

1. 按协议拆分 SSH Git、HTTP Git、raw file access、API 和 webhook 错误率。
2. 检查 Git 前端、鉴权服务、对象存储、元数据数据库和边缘代理是否同时异常。
3. 如果所有 Git operations 失败，优先建立只读或降级路径，保护 clone/fetch。
4. 检查最近部署、配置变更、网络设备维护和依赖限流。
5. 若是共享依赖故障，先隔离或绕过该依赖，再逐步恢复写路径。
6. 恢复后补充按协议维度的 SLO、控制面依赖告警和只读降级演练。

## 常见根因

- Git control plane 共享依赖不可用。
- SSH 和 HTTP Git 前端依赖同一鉴权或元数据服务。
- raw file access 与 Git API 共用边缘代理或对象存储。
- 维护中的网络设备或配置变更造成 packet loss / timeout。

## 公开案例参考

- GitHub Availability Report: November 2025
- GitHub Availability Report: October 2025
