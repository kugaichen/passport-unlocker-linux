# Compatibility

## Software environments

| 环境 | 结果 | 范围 |
|---|---|---|
| Ubuntu 22.04.5 WSL，Python 3.10，GTK 4.6，Libadwaita 1.1 | 通过 | Phase 1/2、`.deb` 构建、Lintian、安装、CLI、GUI、monitor、Polkit |
| Ubuntu 26.04 WSL，Python 3.14 | 通过 | Phase 1/2、Jammy 构建包安装、CLI、GUI、monitor、Polkit、Desktop、AppStream |
| Ubuntu 24.04 原生桌面 | 待验证 | 项目目标环境，尚未单独安装测试 |

WSLg 测试使用当前进程的 Cairo 软件渲染绕过 Mesa/EGL 环境问题，因此不等同于原生桌面的完整视觉和 GPU 渲染验证。

## Hardware devices

| 型号 | VID:PID | 新实现状态 | 说明 |
|---|---|---|---|
| WD My Passport 2626（约 1 TB） | 待真机采集 | 未验证 | 用户已用上游工具成功解锁；新实现尚未执行真实 status、unlock 或 rescan |

当前经过新实现完整验证的硬盘型号数量为 **0**。项目只能声明支持经过状态、解锁和重扫描测试的具体设备，不能宣传支持所有 WD 加密硬盘。公开日志不得记录完整序列号。
