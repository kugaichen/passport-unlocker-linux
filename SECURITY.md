# Security policy

## Supported versions

当前没有稳定版本。`main` 分支和本地 `0.1.0` 开发包属于 pre-alpha，仅用于代码审查、软件测试和受控硬件验证。

## Reporting a vulnerability

公开仓库创建后，请使用 GitHub Security 页面中的 **Report a vulnerability** 私密报告功能。不要把漏洞细节、密码或设备认证数据提交到公开 Issue。

如果私密报告功能尚未启用，请创建一个不含敏感细节的普通 Issue，请求维护者提供私密联系途径。不要为了联系维护者而公开敏感材料。

报告中可以提供：

- 应用版本和 Linux 发行版；
- 设备型号、VID:PID 和序列号后四位；
- 最小复现步骤；
- 已清理的错误类型和日志。

请勿提供硬盘密码、派生 hash、原始解锁 payload、完整序列号、Token、私钥或未清理日志。

## Security boundary

- GUI 为普通用户进程；
- 一次性 helper 只接受固定 operation 和 64 位十六进制 stable ID；
- 密码只通过 stdin 管道传递；
- helper 重新发现并验证 USB 整盘和协议响应；
- SG_IO transport 仅允许状态查询、Handy Store page 1 读取和固定解锁请求；
- 生产入口不包含擦除、改密、密钥重置、格式化、分区或通用 raw SCSI 功能。

Python 字符串无法保证像专用安全内存一样可靠清零。应用会及时清空 UI 和可变输入缓冲区，但不宣称达到硬件安全模块级别。
