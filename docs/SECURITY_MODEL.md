# 安全模型

受保护资产包括硬盘密码、磁盘数据、原始块设备权限、stable ID 和 root 权限。主要威胁是密码进入 argv/日志、GUI 以 root 运行、设备路径替换、伪造 USB 身份、任意 SCSI 注入、并发解锁和误暴露破坏性命令。

控制措施：

- GUI 只把 stable ID 和 stdin 密码帧交给固定绝对路径的 helper。
- helper 重新枚举并验证 USB 整盘、VID/PID、序列号、型号、真实块设备和协议签名。
- SG_IO transport 使用固定 allowlist，写路径只接受 `C1/E1` 与固定 40 字节 payload。
- 解锁后重新查询状态；重扫描后按 stable ID 重找设备。
- 无密码保存、raw SCSI、改密、密钥重置、格式化和分区功能。

当前风险：协议来自社区逆向而非厂商文档；Python 密码字符串不可保证清零；GTK/udev/Polkit 只完成 WSL 软件冒烟；真实 SG_IO、设备路径、密码验证和重扫描仍需 Ubuntu 24.04 真机验证。
