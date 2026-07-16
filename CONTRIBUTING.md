# Contributing

感谢你帮助改进 Passport Unlocker for Linux。本项目直接操作加密硬盘控制器，因此数据安全优先于功能数量和界面便利性。

## 开始之前

- 不要提交硬盘密码、密码派生值、完整序列号、原始解锁 payload 或未清理日志。
- 不要新增 secure erase、密钥重置、密码修改/移除、格式化、分区修改或通用 raw SCSI 入口。
- 不要把密码放入 argv、环境变量、日志、临时文件、配置文件或测试夹具。
- 未经维护者确认，不要在包含唯一副本数据的真实硬盘上测试。

安全问题请遵循 [SECURITY.md](SECURITY.md)，不要创建包含敏感细节的公开 Issue。

## 开发环境

推荐 Ubuntu 22.04 或更新版本。安装 GTK、pyudev、Debian 构建与验证依赖后：

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
```

运行基础测试：

```bash
python3 -m pytest
ruff check .
mypy src/passport_unlocker/core src/passport_unlocker/helper
```

完整 Linux 检查：

```bash
RUFF_BIN=.venv/bin/ruff sh scripts/wsl-test-phase2.sh
```

构建 Debian 二进制包：

```bash
sh scripts/build-deb.sh
```

## 提交要求

- 改动保持集中，并说明行为、安全边界和兼容性影响。
- 协议字节、密码派生、CDB、payload 或响应解析发生变化时，必须先增加黄金测试。
- GUI 不得以 root 运行；特权操作只能通过受限 helper。
- 解锁写请求后必须重新查询状态，不能把“写调用未报错”等同于解锁成功。
- 新设备支持必须附经过清理的型号、VID:PID、固件/桥接信息和测试结果。

## 真机测试

真机测试必须遵循 [docs/HARDWARE_TEST_PLAN.md](docs/HARDWARE_TEST_PLAN.md)。首次测试只连接一块已备份测试盘，并禁止任何擦除、改密、格式化或分区命令。
