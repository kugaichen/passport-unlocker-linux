# Validation status

验证日期：2026-07-16。

## 自动化与静态验证

- Ruff 0.15.21 通过；
- Mypy 在 Ubuntu 22.04/26.04 通过；
- 17 项 Pytest/标准库单元测试通过；
- 黄金密码派生、状态解析、解锁 CDB/payload 和写后状态验证通过 fake transport；
- stable ID、stdin 密码帧和 SG_IO allowlist 测试通过；
- 32 个 Python 文件语法解析通过；
- Desktop entry、安全扫描和 Debian Build-Depends 检查通过；
- 凭据特征扫描未发现 GitHub token、云密钥、私钥或敏感文件。

## GitHub Actions

- 首次公开 CI 运行：`29465626580`；
- `Quality (ubuntu-22.04)`：通过；
- `Quality (ubuntu-24.04)`：通过；
- `Debian package` 构建与 Lintian：通过；
- 运行地址：https://github.com/kugaichen/passport-unlocker-linux/actions/runs/29465626580

## Ubuntu 22.04 WSL

- Python 3.10.12、pyudev 0.22、GTK 4.6、Libadwaita 1.1；
- Phase 1 与 Phase 2 全部通过；
- Setuptools 59.6/Pybuild 原生构建 `.deb` 成功；
- 构建期 17 项测试通过；
- Lintian 无错误级问题；
- 安装、覆盖安装、CLI、Python 导入、Desktop、GUI 和 monitor 冒烟通过；
- 非 root helper 在接触设备前返回 `permission_denied`；
- Polkit action 注册与按需激活通过。

## Ubuntu 26.04 WSL

- Python 3.14.4；
- Ruff、Mypy、17 项测试、Desktop、Build-Depends、CLI 与设备枚举通过；
- Ubuntu 22.04 构建的同一 `.deb` 安装和覆盖安装通过；
- GUI 与 monitor 冒烟通过；
- Desktop 与 AppStream 严格验证通过；
- 新应用 ID、Polkit action 和安装文件清单验证通过。

## 尚未验证

- Ubuntu 24.04 原生桌面；
- 原生 Wayland/X11 布局、图形渲染和完整交互；
- 实际 pkexec 管理员授权、取消授权与密码 stdin 链路；
- pyudev 真实 USB 热插拔、防抖和多设备行为；
- ctypes `sg_io_hdr` 对真实目标设备的 ABI 与 sense/status 行为；
- 新实现的真实 status、错误密码、正确密码 unlock、写后验证和 rescan；
- 真实设备节点变化后的 stable ID 重新发现。

所有 WSL 测试均未发现候选 WD 设备，也未发送真实 SCSI 请求。进入稳定发布或重要数据测试前，必须遵循 [SG_IO_CLEAN_ROOM.md](SG_IO_CLEAN_ROOM.md) 和 [HARDWARE_TEST_PLAN.md](HARDWARE_TEST_PLAN.md)。
