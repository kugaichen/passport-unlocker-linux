# Open-source readiness

更新日期：2026-07-16。

## 当前结论

项目已达到“可以公开源代码并接受审查”的 pre-alpha 阶段，但尚未达到“向普通用户发布稳定解锁工具”的阶段。

可以公开的内容包括：源码、单元测试、协议分析、安全模型、clean-room SG_IO 说明、Debian 打包文件和明确的未验证声明。

在真实 WD 测试完成前，不应发布稳定版二进制、不应宣传支持任何具体型号，也不应把本地 `.deb` 描述为生产可用版本。

## 已完成

- GPL-2.0-only LICENSE、NOTICE 与 Debian copyright；
- 危险操作未进入生产 GUI/CLI/helper；
- 固定 SG_IO allowlist、写后状态验证和稳定设备身份；
- 17 项协议与安全单元测试；
- Ubuntu 22.04 与 26.04 WSL 构建、安装、CLI、GUI、monitor 和 Polkit 冒烟；
- Jammy Lintian 无错误级问题；
- README、安全政策、贡献指南、行为准则、Issue/PR 模板与 CI 配置；
- `io.github.kugaichen.PassportUnlocker` 应用 ID、真实项目 URL 和匿名维护邮箱；
- CLI、GUI 和 helper 手册页；
- 本地 `main` Git 仓库与可审查的首次提交暂存区；
- 凭据特征扫描未发现 Token、私钥或敏感文件。

## 公开仓库前必须完成

1. 完成 GitHub CLI 设备授权；
2. 创建 `kugaichen/passport-unlocker-linux` Public 仓库并推送首次提交；
3. 启用 GitHub Private vulnerability reporting；
4. 确认 GitHub Actions 的 Ubuntu 22.04/24.04 工作流通过；
5. 复核公开后的 README、Issue 模板、Security 页面和仓库 Topics。

## 稳定发布前必须完成

1. Ubuntu 24.04 原生环境验证；
2. 按 `HARDWARE_TEST_PLAN.md` 对已备份测试盘进行只读状态查询和一次受控解锁；
3. 验证错误密码、取消授权、拔盘、blocked、多设备和节点变化；
4. 更新具体设备兼容性表；
5. 完成最终许可证复核；
6. 补齐发布说明、校验和与可复现构建记录。

## 建议发布策略

- 第一步：公开 GitHub 仓库，README 显著标记 pre-alpha，不创建 Binary Release；
- 第二步：通过 Issue 收集经过清理的设备信息和代码审查；
- 第三步：完成真机验证后发布 `v0.1.0` pre-release；
- 第四步：至少验证多个设备和桌面环境后再考虑稳定版本。
