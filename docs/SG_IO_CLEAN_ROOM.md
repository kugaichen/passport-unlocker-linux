# SG_IO clean-room note

`core/linux_sg_io.py` 按 Linux 公共 `sg_io_hdr` ABI 和 `SG_IO` ioctl 最小实现，没有复制 `py3_sg` 源码或结构。实现只支持项目所需的 from-device/to-device 请求，并在调用前对 CDB、长度和解锁 payload header 做 allowlist 校验。

正式发布前需在 Ubuntu 24.04 上完成：

1. 对照目标架构的 `/usr/include/scsi/sg.h` 核验 ctypes 布局与常量；
2. 用已备份测试盘比较只读 status 响应；
3. 检查 SCSI status/host status/driver status 和 sense 处理；
4. 再进行一次正确密码解锁测试；
5. 完成开源许可证复核。

Ubuntu 22.04/26.04 WSL 已完成单元测试、打包和无设备冒烟，但没有候选 WD 设备，因此没有执行真实 SG_IO。本文档不是法律意见，也不声称真机等价性已经确认。
