# Release checklist

## 仓库身份

- [ ] GitHub owner 与仓库名已确认；
- [ ] 仓库可见性已明确设为 Public；
- [ ] 应用 ID 使用维护者控制的反向域名；
- [ ] README、AppStream、Debian Maintainer 和项目 URL 均指向真实渠道；
- [ ] GitHub Private vulnerability reporting 已启用；
- [ ] 默认分支保护和所需 CI 已配置。

## 法律与安全

- [ ] LICENSE、NOTICE、Debian copyright 与上游 commit 一致；
- [ ] 未提交 Token、密码、私钥、完整序列号或未清理日志；
- [ ] 生产入口不包含擦除、改密、密钥重置、格式化、分区或 raw SCSI 功能；
- [ ] GUI 不以 root 运行，helper 只能执行固定 operation；
- [ ] 安全报告渠道经过实际验证。

## 自动化验证

- [ ] Ubuntu 22.04 Phase 1/2 通过；
- [ ] Ubuntu 24.04 Phase 1/2 通过；
- [ ] Ruff、Mypy 和全部单元测试通过；
- [ ] Desktop 与 AppStream 严格验证通过；
- [ ] `.deb` 构建与 Lintian 无错误级问题；
- [ ] 安装、覆盖安装与卸载测试通过；
- [ ] 最终产物 SHA-256 已记录。

## 真机门禁

- [ ] 测试盘数据已有独立备份；
- [ ] 只读 status 与上游行为一致；
- [ ] 错误密码只尝试一次且无自动重试；
- [ ] 正确密码解锁后重新查询状态；
- [ ] 重扫描后按 stable ID 找回设备；
- [ ] 拔盘、blocked、多设备和授权取消已验证；
- [ ] 兼容性表只列出真实验证型号。

## GitHub 发布

- [ ] CHANGELOG 与版本号一致；
- [ ] Git tag、Python 版本、Debian 版本和 AppStream release 一致；
- [ ] Release 标记为 pre-release，直到真机与兼容性门禁完成；
- [ ] Release assets 仅包含最终 `.deb`、source archive 和 SHA-256；
- [ ] 发布说明包含非官方声明、备份要求、支持范围和已知限制。
