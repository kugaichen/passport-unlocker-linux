# Passport Unlocker for Linux

[![CI](https://github.com/kugaichen/passport-unlocker-linux/actions/workflows/ci.yml/badge.svg)](https://github.com/kugaichen/passport-unlocker-linux/actions/workflows/ci.yml)

Passport Unlocker for Linux 是一个非官方开源工具，用于在 Linux 上解锁兼容的、启用硬件加密的 WD My Passport 硬盘。

它不会破解或绕过密码；用户仍须输入正确的硬盘密码。应用向硬盘控制器发送兼容的认证请求，成功后重新查询状态并重新扫描设备，让桌面环境识别数据分区。

> **状态：pre-alpha。** 新实现已经通过 Ubuntu 22.04/26.04 WSL 软件测试，但尚未在真实 WD 硬盘上完成状态查询和解锁验证。不要把它用于没有独立备份的重要数据。

> Unofficial utility for compatible WD My Passport drives.  
> Not affiliated with or endorsed by Western Digital.

## 当前验证状态

| 环境 | 已验证 |
|---|---|
| Ubuntu 22.04 WSL，Python 3.10，GTK 4.6，Libadwaita 1.1 | Phase 1/2、构建、Lintian、安装、CLI、GUI、monitor、Polkit |
| Ubuntu 26.04 WSL，Python 3.14 | Phase 2、安装、CLI、GUI、monitor、Polkit |
| Ubuntu 24.04 原生桌面 | 待验证 |
| 真实 WD My Passport | 待验证；当前兼容型号数量为 0 |

详细证据与限制见 [docs/VALIDATION.md](docs/VALIDATION.md) 和 [docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)。

## v0.1 范围

- 候选设备发现与多设备选择；
- 状态查询、解锁、解锁后验证和重新扫描；
- 普通用户 GTK 4/Libadwaita GUI；
- 通过 Polkit/pkexec 启动的一次性最小特权 helper；
- XDG Autostart 插盘监测；
- Ubuntu/Debian `.deb` 打包。

本项目刻意不提供密码修改、密码移除、secure erase、密钥重置、格式化、分区修改、密码保存或通用 raw SCSI 接口。

## 安装本地开发包

在真实硬件验证完成前，本地 `.deb` 仅用于开发和审查：

```bash
sudo apt install ./passport-unlocker_0.1.0-1_all.deb
```

安装不会自动解锁设备。卸载：

```bash
sudo apt remove passport-unlocker
```

## 使用

列出候选设备：

```bash
passport-unlocker list
```

启动普通用户 GUI：

```bash
passport-unlocker-gui
```

不要使用 `sudo passport-unlocker-gui`。GUI 通过 Polkit 请求受限 helper 执行必要的设备操作。

## 开发验证

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python3 -m pytest
ruff check .
mypy src/passport_unlocker/core src/passport_unlocker/helper
```

完整 Linux 检查还需要 GTK、pyudev、Desktop、AppStream 和 Debian 构建工具：

```bash
RUFF_BIN=.venv/bin/ruff sh scripts/wsl-test-phase2.sh
```

正式安装应使用 `.deb`，不要使用 `sudo pip` 或 `--break-system-packages`。

## 构建 `.deb`

安装项目 Build-Depends 后，在源码根目录执行：

```bash
sh scripts/build-deb.sh
```

脚本不会安装依赖或联网。为避免 `/mnt/c` 的 DrvFS 权限映射干扰 Debhelper，它会把源码复制到 WSL 原生临时目录、规范构建权限，并调用二进制包构建：

```bash
dpkg-buildpackage -b -us -uc
```

生成的 `.deb`、`.changes` 和 `.buildinfo` 位于源码目录的上一级。安装前请检查包内容；真机测试必须遵循 [docs/HARDWARE_TEST_PLAN.md](docs/HARDWARE_TEST_PLAN.md)。

## 安全说明

- GUI 以普通用户运行；仅 helper 通过 Polkit 获得临时特权。
- 密码通过 stdin 长度前缀协议传给 helper，不进入 argv、环境变量、日志或文件。
- `/dev/sdX` 不是稳定身份，操作以 VID、PID、序列号和型号生成的 stable ID 重新发现设备。
- SG_IO transport 只允许固定的状态读取、Handy Store page 1 读取和解锁写请求。
- 真实硬件测试前必须备份重要数据；自动化测试不访问真实设备。

安全问题请阅读 [SECURITY.md](SECURITY.md)。普通问题见 [SUPPORT.md](SUPPORT.md)，贡献代码前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 项目地址

- 源码与文档：https://github.com/kugaichen/passport-unlocker-linux
- 问题反馈：https://github.com/kugaichen/passport-unlocker-linux/issues
- 应用 ID：`io.github.kugaichen.PassportUnlocker`

## 许可证

项目基于 `0-duke/wdpassport-utils`（上游 commit `4317baece37fa9c41070d790427c03f0a782a6ad`）二次开发，按 GPL-2.0-only 分发。详见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 与 [docs/UPSTREAM_ANALYSIS.md](docs/UPSTREAM_ANALYSIS.md)。
