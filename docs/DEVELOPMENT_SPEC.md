# Development specification

本项目依据用户提供的《Passport Unlocker for Linux 二次开发设计与 Codex 实施指南》v1.0（2026-07-15）实施。

核心约束：

1. GUI 为普通用户进程；原始块设备访问仅在固定接口的 Polkit helper 中执行。
2. 密码不进入 argv、环境变量、日志、临时文件、配置或 JSON。
3. 设备使用 VID、PID、序列号和型号生成的 stable ID，不把 `/dev/sdX` 当作身份。
4. 协议层无 GUI、pyudev、打印、终端输入、全局设备句柄和进程退出。
5. 状态查询、Handy Store、密码派生、解锁 CDB 和字节序由黄金测试固定。
6. 解锁写请求后必须再次查询状态。
7. v0.1 仅含发现、状态、解锁和重扫描，不含任何破坏性或密码管理功能。
8. 正式安装使用系统依赖和 `.deb`，不使用系统级 pip。
9. SG_IO transport 只实现固定的项目 CDB，不提供通用 raw SCSI 入口。
10. 真机操作不属于自动化测试范围。

完整原始规格由项目委托方保管；本仓库中的其他设计文档记录实现细节和验收边界。

