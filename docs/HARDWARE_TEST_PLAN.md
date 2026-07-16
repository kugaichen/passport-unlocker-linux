# Ubuntu 24.04 真机测试计划

前提：重要数据已有独立备份；首轮只连接一块测试盘；用 `lsblk` 核对型号、容量和系统盘；源码中不存在擦除/改密/格式化入口。

按顺序验证：

1. 安装 `.deb`，运行 `passport-unlocker --version` 和 `passport-unlocker list`。
2. 手动启动 GUI，确认普通用户身份和无设备空状态。
3. 插入锁定盘，确认只出现一个窗口并显示正确型号、容量、序列号后四位。
4. 取消 Polkit，确认安全恢复。
5. 输入一次错误密码，确认明确提示且无自动重试。
6. 输入正确密码，确认写后状态验证、重扫描和分区出现。
7. 验证节点从 `/dev/sdX` 改变时仍按 stable ID 找回。
8. 覆盖操作中拔盘、blocked、多设备、Wayland/X11 和桌面会话重启。

绝不执行 secure erase、reset key、change/remove password、fdisk、mkfs、wipefs 或 parted。

