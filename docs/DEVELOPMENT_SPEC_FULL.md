# Passport Unlocker for Linux 二次开发设计与 Codex 实施指南

> 文档用途：指导 Codex 基于 `0-duke/wdpassport-utils` 进行安全、可测试、可打包的二次开发，将现有命令行脚本改造成适用于 Linux 桌面的 WD My Passport 图形化解锁应用。  
> 初始目标平台：Ubuntu 24.04 LTS，GNOME/Wayland；兼容性验证设备为 WD My Passport 2626，约 1 TB。  
> 文档版本：v1.0  
> 日期：2026-07-15

---

## 0. 如何使用本文档

建议不要让 Codex 一次性完成全部开发。正确方式是：

1. 将本文档放入目标仓库，例如 `docs/DEVELOPMENT_SPEC.md`。
2. 先让 Codex完整检查上游代码，生成基线分析，但不要立即重写。
3. 严格按照本文档第 17 节的阶段顺序开发。
4. 每一阶段只处理有限数量的文件，先测试，再进入下一阶段。
5. 真机测试只允许执行“状态查询、正确密码解锁、重新扫描”，不得测试擦除或重置密钥。
6. 第一次公开发布前，必须处理第 13 节的许可证问题。

推荐给 Codex 的总原则：

```text
改动要小，方便审查。
动手前先说明计划修改的文件和原因。
不要胡编目录、设备路径、依赖版本或系统配置。
不要在日志、命令行、测试数据和提交记录中泄露硬盘密码。
行为变化必须补测试。
执行命令前说明目的。
默认中文汇报，输出命令必须可复制。
不要硬编码 /dev/sda，设备节点在重扫描后可能变化。
绝不实现或暴露 secure erase、密钥重置和格式化功能。
```

---

# 1. 项目目标

## 1.1 产品定义

开发一个非 Western Digital 官方的 Linux 桌面应用：

```text
Passport Unlocker for Linux
```

安装一次后，用户连接兼容的 WD My Passport 加密硬盘，应用自动发现设备并弹出图形化解锁窗口。用户输入硬盘密码后，应用通过底层 SCSI 命令请求硬盘控制器解锁，随后重新扫描设备，使 Linux 桌面能够识别并挂载数据分区。

目标用户体验：

```text
插入硬盘
  ↓
后台监测到候选 WD My Passport
  ↓
弹出图形化解锁窗口
  ↓
显示型号、容量、序列号后四位和连接状态
  ↓
用户输入硬盘密码
  ↓
Polkit 请求必要的系统权限
  ↓
底层 helper 查询状态并执行解锁
  ↓
重新扫描 SCSI 设备
  ↓
按稳定设备标识重新发现新的 /dev/sdX
  ↓
等待桌面自动挂载，或提示用户在文件管理器中打开
```

## 1.2 项目定位

这是一个 Linux 客户端，不是：

- 密码破解工具；
- 数据恢复工具；
- 通用 SCSI 管理器；
- WD 固件修改器；
- 自动运行 U 盘程序；
- Western Digital 官方软件。

应用名称、图标和关于页面必须明确写明：

```text
Unofficial utility for compatible WD My Passport drives.
Not affiliated with or endorsed by Western Digital.
```

不要未经许可使用 WD 官方商标作为应用主图标，也不要让用户误认为本项目由 Western Digital 发布。

## 1.3 为什么不直接把 Linux 程序写进硬盘并自动运行

现代 Linux 桌面通常不会自动运行 USB 存储设备中的可执行文件，否则任意恶意 U 盘都可以在插入后执行代码。

此外，WD 锁定状态下展示的解锁虚拟介质可能由硬盘固件管理，未必是用户可写的普通分区。因此正确产品形态是：

```text
首次：用户安装 .deb
以后：插盘自动发现并弹出解锁界面
```

可以额外把 `.deb` 或 AppImage 放在硬盘的普通可写分区中，供用户手动安装，但它不能替代系统侧安装和桌面集成。

---

# 2. 上游项目基线分析

## 2.1 当前仓库结构

上游仓库非常小，主要包含：

```text
.gitignore
LICENSE
README.md
setup.py
wdpassport-utils.py
```

当前核心实现是一个约 457 行的单文件 Python CLI。它支持：

- 查询硬盘安全状态；
- 输入密码解锁；
- 修改或移除密码；
- secure erase / 重置密钥；
- 重新扫描设备；
- 多设备时用 `--device /dev/sdX` 指定目标。

当前安装方式使用旧式 `setup.py`，并将 `py3_sg` 作为 Git 依赖。README 中的 `sudo pip install` 在启用了 PEP 668 的新 Ubuntu 上会触发 `externally-managed-environment`，不适合作为新的产品安装方案。

## 2.2 当前代码的关键问题

### 单文件和全局状态

原脚本使用：

```python
dev = None
device_name = None
```

多个函数直接依赖这些全局变量。GUI、并发设备和单元测试都不适合继续使用这种方式。

### 直接退出进程

底层协议函数遇到错误时大量调用：

```python
sys.exit(1)
```

导入为库后，这会直接杀死 GUI 进程。应改为抛出结构化异常，由 CLI、GUI 或 helper 决定如何展示。

### 裸 `except`

上游在解锁、改密和擦除路径中使用裸异常：

```python
except:
    ...
```

它把“密码错误、设备拔出、权限不足、SCSI sense error、程序 bug”混在一起，GUI 无法给出准确提示，也不利于测试。

### 设备识别过于简单

上游通过沿 pyudev 父设备链查找：

```text
ID_SERIAL startswith "Western_Digital_My_"
```

来识别设备。该方式可作为候选筛选，但正式 helper 不能只信任一个字符串。至少还需验证：

- 请求对象是整块磁盘而非分区；
- 设备位于 USB 总线；
- 稳定序列号、USB VID/PID、型号与当前设备一致；
- `/dev/...` 是真实块设备而不是用户提供的任意路径；
- WD 状态查询返回正确签名；
- 解锁前后设备身份一致。

### 多设备处理方式不适合 GUI

上游发现多个设备时直接报错并退出。GUI 应显示设备列表，让用户依据型号、容量和序列号后四位选择。

### 危险功能与正常解锁混在同一入口

上游 CLI 同时提供：

```text
--unlock
--change_passwd
--erase
```

新项目 v0.1 绝不能暴露 `--erase`、密钥重置、格式化和密码修改功能。最好从正式安装包中完全移除这些入口，而不是只在界面里隐藏。

---

# 3. 底层协议与解锁原理

## 3.1 解锁并不是在 Linux 中逐文件解密

WD My Passport 的硬件控制器负责数据加密、解密和访问控制。Linux 应用只负责：

1. 获取用户输入的密码；
2. 按照 WD 兼容规则派生认证数据；
3. 通过 Linux SCSI Generic 接口发送厂商命令；
4. 由硬盘控制器验证密码；
5. 验证成功后，控制器允许访问正常数据区；
6. Linux 重新扫描设备并读取分区。

因此解锁速度与磁盘容量基本无关，不会在解锁时把 1 TB 数据重新处理一遍。

## 3.2 状态查询

上游使用如下 10 字节 CDB 查询加密状态：

```python
[0xC0, 0x45, 0x00, 0x00, 0x00,
 0x00, 0x00, 0x00, 0x30, 0x00]
```

读取 512 字节数据，并检查：

```text
data[0] == 0x45
```

关键字段：

```text
data[3]       安全状态
data[4]       cipher id
data[6:8]     password length，大端
data[8:12]    key reset enabler
```

状态映射：

```text
0x00  No lock
0x01  Locked
0x02  Unlocked
0x06  Locked, unlock blocked
0x07  No keys
```

新项目必须把这些数值定义为枚举，不要继续在 GUI 中传播裸整数。

## 3.3 Handy Store 参数读取

上游通过 CDB `0xD8` 读取 Handy Store page 1，验证：

```text
签名：00 01 44 57
块大小：512 字节
最后一字节：checksum
```

读取：

```text
iteration = little-endian uint32 at offset 8
salt      = bytes 12:20
hint      = bytes 24:226
```

第一版 GUI 不需要显示完整 hint；若后续显示，应正确处理 NUL、编码和不可打印字符。

## 3.4 密码派生

上游算法大致为：

```python
clean_salt = 从 salt 的偶数字节提取字符，遇到 00 00 结束
password = clean_salt + user_password
password_bytes = password.encode("utf-16")[2:]
重复 iteration 次：
    password_bytes = SHA256(password_bytes)
```

在 x86_64 Linux 上，`encode("utf-16")[2:]` 实际通常等价于去掉 BOM 后的 UTF-16LE。

重构时不要直接“优化”该算法。应先建立黄金测试，再考虑把实现改为明确的：

```python
password.encode("utf-16-le")
```

这样可以避免主机字节序对行为产生影响。

用于单元测试的合成向量：

```text
password  = Test123!
salt      = 41 00 42 00 43 00 44 00
iteration = 2
expected  = 5965eea11dfd0cd9567f5955f23489d9160943c2fec9e9802e4726ce1cdfb38b
```

该向量仅用于验证兼容实现，不是用户真实密码或设备参数。

## 3.5 解锁命令

上游生成密码块后发送：

```python
CDB = [0xC1, 0xE1, 0x00, 0x00, 0x00,
       0x00, 0x00, 0x00, length, 0x00]
```

数据区由：

```text
8 字节 header + 派生后的 32 字节密码数据
```

构成。SCSI 写操作成功不应被简单等同于“一定解锁成功”。新实现应在写操作后再次查询状态，只有状态变为 `UNLOCKED` 或 `NO_LOCK` 才返回成功。

## 3.6 重新扫描

上游做法是：

```text
向 /sys/block/<name>/device/delete 写入 1
向 /sys/class/scsi_host/<host>/scan 写入 "- - -"
```

这会导致原来的 `/dev/sdX` 消失，再由内核重新发现设备。重新发现后设备节点可能变化，例如：

```text
解锁前 /dev/sda
解锁后 /dev/sdb
```

因此整个项目中都不得把 `/dev/sda` 当作稳定身份。必须使用：

```text
USB 序列号 + USB VID/PID + 型号
```

形成 `stable_id`，在重扫描后重新查找设备。

---

# 4. v0.1 功能范围

## 4.1 必须实现

1. 发现候选 WD My Passport 整盘设备。
2. 支持多个设备同时连接。
3. 显示：
   - 型号；
   - 容量；
   - USB 连接；
   - 序列号后四位；
   - 当前操作状态。
4. 输入硬盘密码。
5. 调用受限特权 helper。
6. helper 重新验证设备身份。
7. 查询安全状态。
8. 已解锁时返回幂等成功。
9. 锁定时派生认证数据并发送解锁命令。
10. 解锁后再次查询状态。
11. 重新扫描设备。
12. 按 stable_id 等待设备重新出现。
13. 提示自动挂载结果或引导用户打开文件管理器。
14. 插盘自动弹出窗口。
15. 提供手动启动入口。
16. 提供中英文基础界面。
17. 构建 Ubuntu 24.04 `.deb`。
18. 保留兼容的安全 CLI，用于诊断：
    - `list`
    - `status`
    - `unlock`
    - `rescan`
19. 单元测试不依赖真实硬盘。
20. 真机测试有明确安全流程。

## 4.2 明确不实现

v0.1 不允许实现或暴露：

- 修改密码；
- 设置新密码；
- 移除密码；
- secure erase；
- 重置内部密钥；
- 格式化；
- 修改分区表；
- 固件升级；
- 密码爆破；
- 记住密码；
- 网络上传日志；
- 自动解锁；
- 远程解锁；
- 以 root 身份运行整个 GUI。

---

# 5. 推荐总体架构

## 5.1 MVP 推荐架构

第一版推荐使用：

```text
普通用户 GTK 应用
    │
    ├── pyudev 监听设备插拔
    ├── 显示设备、密码输入和状态
    └── 通过 pkexec 启动一次性特权 helper
                │
                ├── 验证 stable_id 与当前设备
                ├── 以 root 打开块设备
                ├── 查询状态
                ├── 解锁
                ├── 验证结果
                └── 重新扫描
```

优点：

- 不需要长期运行 root daemon；
- GUI 始终是普通用户进程；
- 使用桌面已有 Polkit agent；
- 密码不出现在命令行；
- helper 权限面小；
- 容易审查和打包；
- 适合 Codex 分阶段实现。

## 5.2 为什么不让 GUI 直接 `sudo`

禁止：

```bash
sudo passport-unlocker
```

因为这会让 GTK、主题、图标解析、桌面集成和整个 Python GUI 全部拥有 root 权限。正确做法是只让一个代码量很小、接口固定的 helper 获得特权。

## 5.3 后续生产架构

v1.0 以后可以升级为：

```text
GTK GUI
  ↓ system D-Bus
root helper service
  ↓ Polkit CheckAuthorization
SG_IO
```

长期服务能提供无额外弹窗的只读状态查询和更平滑的 UX，但 D-Bus 方法、FD 密码传递、服务激活和策略审计更复杂，不应作为第一阶段起点。

---

# 6. 推荐仓库结构

```text
passport-unlocker-linux/
├── LICENSE
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── pyproject.toml
├── MANIFEST.in
│
├── docs/
│   ├── DEVELOPMENT_SPEC.md
│   ├── UPSTREAM_ANALYSIS.md
│   ├── PROTOCOL_NOTES.md
│   ├── SECURITY_MODEL.md
│   ├── HARDWARE_TEST_PLAN.md
│   └── COMPATIBILITY.md
│
├── src/
│   └── passport_unlocker/
│       ├── __init__.py
│       ├── __main__.py
│       ├── version.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── constants.py
│       │   ├── models.py
│       │   ├── errors.py
│       │   ├── password.py
│       │   ├── protocol.py
│       │   ├── service.py
│       │   └── transport.py
│       │
│       ├── devices/
│       │   ├── __init__.py
│       │   ├── discovery.py
│       │   ├── identity.py
│       │   ├── monitor.py
│       │   └── rescan.py
│       │
│       ├── helper/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── authorization.py
│       │   ├── validation.py
│       │   └── wire.py
│       │
│       ├── gui/
│       │   ├── __init__.py
│       │   ├── application.py
│       │   ├── window.py
│       │   ├── device_row.py
│       │   ├── controller.py
│       │   ├── worker.py
│       │   └── notifications.py
│       │
│       └── cli/
│           ├── __init__.py
│           └── main.py
│
├── data/
│   ├── io.github.REPLACE_ME.PassportUnlocker.desktop
│   ├── io.github.REPLACE_ME.PassportUnlocker.metainfo.xml
│   ├── io.github.REPLACE_ME.PassportUnlocker.svg
│   ├── io.github.REPLACE_ME.PassportUnlocker.policy
│   └── autostart/
│       └── io.github.REPLACE_ME.PassportUnlocker.Monitor.desktop
│
├── packaging/
│   └── debian/
│       ├── changelog
│       ├── control
│       ├── copyright
│       ├── install
│       ├── rules
│       ├── source/
│       │   └── format
│       └── tests/
│           └── smoke
│
├── tests/
│   ├── unit/
│   │   ├── test_password.py
│   │   ├── test_protocol_status.py
│   │   ├── test_protocol_unlock.py
│   │   ├── test_discovery.py
│   │   ├── test_identity.py
│   │   ├── test_validation.py
│   │   ├── test_wire.py
│   │   └── test_service.py
│   ├── integration/
│   │   ├── test_helper_fake_transport.py
│   │   └── test_gui_controller.py
│   └── fixtures/
│       ├── status_locked.bin
│       ├── status_unlocked.bin
│       └── handy_store_page1.bin
│
└── .github/
    └── workflows/
        ├── test.yml
        └── package.yml
```

`REPLACE_ME` 必须由项目所有者替换为自己的 GitHub 名或控制的反向域名。Codex 不得猜测应用 ID。

---

# 7. 核心模块详细设计

## 7.1 数据模型

建议使用冻结 dataclass 和枚举：

```python
from dataclasses import dataclass
from enum import IntEnum, StrEnum


class SecurityState(IntEnum):
    NO_LOCK = 0x00
    LOCKED = 0x01
    UNLOCKED = 0x02
    LOCKED_BLOCKED = 0x06
    NO_KEYS = 0x07


class OperationState(StrEnum):
    IDLE = "idle"
    AUTHORIZING = "authorizing"
    CHECKING = "checking"
    UNLOCKING = "unlocking"
    RESCANNING = "rescanning"
    WAITING_FOR_DEVICE = "waiting_for_device"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class DeviceIdentity:
    stable_id: str
    device_node: str
    sys_path: str
    model: str
    vendor: str
    serial: str
    size_bytes: int
    usb_vid: str | None
    usb_pid: str | None


@dataclass(frozen=True)
class EncryptionStatus:
    state: SecurityState
    cipher_id: int
    password_length: int
    key_reset_enabler: bytes


@dataclass(frozen=True)
class UnlockResult:
    stable_id: str
    state_before: SecurityState
    state_after: SecurityState
    old_device_node: str
    new_device_node: str | None
    rescanned: bool
```

要求：

- `DeviceIdentity` 不允许 GUI 自己构造后直接被 helper 信任；
- helper 必须重新通过 pyudev 构造真实身份；
- `key_reset_enabler` 在 v0.1 不应出现在 GUI 或日志；
- 不要把密码放入 dataclass、repr、异常对象或结果对象。

## 7.2 异常体系

```python
class PassportUnlockerError(Exception):
    """所有可预期项目错误的基类。"""


class UnsupportedDeviceError(PassportUnlockerError):
    pass


class DeviceNotFoundError(PassportUnlockerError):
    pass


class DeviceIdentityChangedError(PassportUnlockerError):
    pass


class PermissionDeniedError(PassportUnlockerError):
    pass


class DeviceBusyError(PassportUnlockerError):
    pass


class DeviceDisconnectedError(PassportUnlockerError):
    pass


class ProtocolSignatureError(PassportUnlockerError):
    pass


class HandyStoreChecksumError(PassportUnlockerError):
    pass


class InvalidHashParametersError(PassportUnlockerError):
    pass


class WrongPasswordError(PassportUnlockerError):
    pass


class UnlockBlockedError(PassportUnlockerError):
    pass


class ScsiTransportError(PassportUnlockerError):
    pass


class RescanError(PassportUnlockerError):
    pass


class RescanTimeoutError(PassportUnlockerError):
    pass
```

底层不得 `print()` 或 `sys.exit()`。CLI 和 GUI 负责把异常翻译成用户可读消息。

## 7.3 Transport 抽象

核心协议不能直接依赖全局文件句柄或 `py3_sg`。定义：

```python
from typing import Protocol


class ScsiTransport(Protocol):
    def read(self, cdb: bytes, allocation_length: int) -> bytes:
        ...

    def write(self, cdb: bytes, payload: bytes) -> None:
        ...

    def close(self) -> None:
        ...
```

提供：

```text
FakeScsiTransport
LinuxSgIoTransport
```

### FakeScsiTransport

用于：

- 返回预置状态块；
- 记录发送的 CDB；
- 模拟密码错误；
- 模拟设备断开；
- 模拟 SCSI sense error；
- 验证 payload 长度和字节序。

### LinuxSgIoTransport

公开分发版本建议基于 Linux `SG_IO` UAPI 自行实现最小 transport：

```text
open(device_node, O_RDWR | O_CLOEXEC)
fcntl.ioctl(fd, SG_IO, sg_io_hdr)
```

只实现项目需要的：

- from-device read；
- to-device write；
- sense buffer；
- timeout；
- status 检查。

不要实现通用任意命令执行 CLI，避免项目变成可滥用的通用 SCSI 写工具。

## 7.4 协议层

推荐类：

```python
class WdPassportProtocol:
    def __init__(self, transport: ScsiTransport):
        self._transport = transport

    def get_status(self) -> EncryptionStatus:
        ...

    def read_hash_parameters(self) -> HashParameters:
        ...

    def unlock(self, password: bytearray) -> None:
        ...
```

其中：

```python
@dataclass(frozen=True)
class HashParameters:
    iteration: int
    salt: bytes
    hint: bytes
```

协议层职责：

- 构建 CDB；
- 解析固定格式响应；
- 校验签名和 checksum；
- 派生密码；
- 发送解锁命令；
- 验证状态。

协议层不负责：

- 设备发现；
- Polkit；
- GTK；
- 自动挂载；
- 用户文案；
- 日志格式；
- sysfs 重新扫描。

## 7.5 密码处理

GUI 中使用 `Gtk.PasswordEntry`。

传给 helper 前：

- 不放入 argv；
- 不放入环境变量；
- 不写临时文件；
- 不写日志；
- 不放入异常；
- 不持久化；
- 不保存到配置；
- 不使用 shell；
- 使用二进制匿名管道。

推荐 helper stdin 协议：

```text
4 字节大端无符号整数：密码 UTF-8 字节长度
N 字节：密码 UTF-8
```

GUI：

```python
payload = password.encode("utf-8")
stdin.write(len(payload).to_bytes(4, "big"))
stdin.write(payload)
stdin.flush()
stdin.close()
```

helper：

1. 最多读取 4 字节长度；
2. 拒绝超过合理上限的长度，例如 1024 字节；
3. 精确读取 N 字节；
4. 解码 UTF-8；
5. 尽量使用 `bytearray`；
6. 派生后覆盖 `bytearray`；
7. 不返回派生值。

注意：Python 字符串不可保证真正安全清零。文档和 README 应诚实说明这一限制，不宣称达到硬件安全模块级别。

## 7.6 业务服务层

```python
class PassportUnlockService:
    def get_status(self, identity: DeviceIdentity) -> EncryptionStatus:
        ...

    def unlock_and_rescan(
        self,
        expected_stable_id: str,
        password: bytearray,
        timeout_seconds: float = 15.0,
    ) -> UnlockResult:
        ...
```

`unlock_and_rescan` 必须执行：

```text
重新发现 stable_id
  ↓
确认整盘、USB、型号、序列号、VID/PID
  ↓
打开设备
  ↓
查询状态
  ├── NO_LOCK/UNLOCKED：幂等成功，可选择 rescan
  ├── LOCKED_BLOCKED：拒绝并提示拔插设备
  ├── NO_KEYS：拒绝并提示不支持
  └── LOCKED：继续
  ↓
读取 hash 参数
  ↓
派生认证数据
  ↓
发送解锁命令
  ↓
再次查询状态
  ↓
若仍 LOCKED：WrongPasswordError
  ↓
关闭 fd
  ↓
记录原 scsi_host 和 stable_id
  ↓
sysfs delete + scan
  ↓
按 stable_id 等待重新出现
  ↓
返回新的 device_node
```

解锁后验证状态比仅依赖 `py_sg.write()` 是否抛异常更可靠。

## 7.7 设备发现

推荐函数：

```python
def list_candidate_devices(context: pyudev.Context) -> list[DeviceIdentity]:
    ...
```

候选过滤至少包括：

```text
subsystem == block
DEVTYPE == disk
device_node 非空
父链存在 usb_device
ID_BUS == usb 或可确认 USB parent
ID_VENDOR / ID_VENDOR_ID
ID_MODEL
ID_SERIAL / ID_SERIAL_SHORT
```

候选判断应分两级：

### 第一级：宽松发现

用于普通用户 GUI 列表：

- WD/Western Digital；
- 模型包含 My Passport；
- USB 整盘。

### 第二级：协议探测

由特权 helper 执行：

- 状态查询 CDB 成功；
- 首字节签名为 `0x45`；
- 返回长度正确；
- 状态值在已知范围或标记为 unknown；
- 密码长度合理。

只有第二级通过才能执行解锁。

## 7.8 Stable ID

不要用 `/dev/sda`。

建议：

```python
stable_id = sha256(
    f"{usb_vid}:{usb_pid}:{serial_short}:{model}".encode("utf-8")
).hexdigest()
```

stable_id 只用于进程间引用，不应代替 helper 的重新验证。

日志中可以只记录：

```text
stable_id 前 12 位
型号
序列号后四位
```

不要默认把完整序列号上传或写入公开 bug report。

## 7.9 自动监测

后台 GUI 进程运行在用户会话中：

```python
monitor = pyudev.Monitor.from_netlink(context)
monitor.filter_by(subsystem="block")
```

处理：

```text
add/change
  ↓
防抖 500–1500 ms
  ↓
重新枚举所有候选整盘
  ↓
与当前 stable_id 集合比较
  ↓
发现新设备
  ↓
激活 Gtk.Application 窗口
```

不要在 pyudev 回调线程直接更新 GTK。使用：

```python
GLib.idle_add(...)
```

将 UI 更新切回主线程。

应处理：

- 同一插盘产生多个 udev event；
- 解锁重扫描产生 remove + add；
- GUI 已打开；
- 多设备同时插入；
- 用户拔出设备；
- 当前设备节点改变；
- 没有桌面会话；
- 用户关闭自动弹窗但保留托盘/后台。

v0.1 可使用 XDG Autostart：

```text
/etc/xdg/autostart/io.github.REPLACE_ME.PassportUnlocker.Monitor.desktop
```

不需要让 udev 直接启动 GUI。

## 7.10 GUI 页面与状态机

建议使用 GTK 4 + Libadwaita。

主要页面：

### 空状态

```text
未发现兼容的 WD My Passport 设备
连接硬盘后将自动显示。
```

### 设备选择

每个设备显示：

```text
My Passport 2626
931.5 GiB · USB · 序列号 …4231
```

### 解锁页

控件：

- 设备名称；
- 设备容量；
- 密码输入；
- 显示密码开关；
- 解锁按钮；
- 取消；
- 状态说明；
- 非官方声明。

### 操作中

```text
正在请求系统权限
正在检查设备
正在验证硬盘密码
正在重新扫描设备
正在等待数据分区
```

### 成功

```text
硬盘已解锁
设备已重新连接为 /dev/sdX
可在文件管理器中打开
```

### 错误

错误必须区分：

| 异常 | 用户提示 |
|---|---|
| WrongPasswordError | 密码不正确，请重试 |
| UnlockBlockedError | 设备暂时阻止继续尝试，请安全拔出后重新连接 |
| DeviceDisconnectedError | 操作期间设备已断开 |
| PermissionDeniedError | 未获得系统授权 |
| UnsupportedDeviceError | 此设备型号或协议尚未验证 |
| RescanTimeoutError | 已解锁，但系统未能及时重新发现设备 |
| ProtocolSignatureError | 设备返回了不兼容的协议响应 |
| DeviceIdentityChangedError | 设备身份发生变化，为安全起见已取消操作 |

GUI 主线程不得执行：

- 密码哈希循环；
- helper 等待；
- pyudev 枚举；
- SCSI 操作；
- 15 秒重扫描等待。

应使用后台线程、`Gio.Subprocess` 异步 API或受控 worker。

---

# 8. 特权 Helper 设计

## 8.1 安装路径

```text
/usr/libexec/passport-unlocker-helper
```

不要把 helper 放在普通用户可写目录。

## 8.2 helper 命令

v0.1 只允许：

```text
passport-unlocker-helper unlock-and-rescan --stable-id <id>
passport-unlocker-helper status --stable-id <id>
```

更严格的 MVP 可以只提供：

```text
unlock-and-rescan
```

禁止：

```text
raw-scsi
erase
reset-key
format
change-password
run-command
device-path 任意文件
```

## 8.3 调用方式

GUI 使用绝对路径和固定参数数组：

```python
[
    "/usr/bin/pkexec",
    "/usr/libexec/passport-unlocker-helper",
    "unlock-and-rescan",
    "--stable-id",
    stable_id,
]
```

禁止：

```python
shell=True
os.system(...)
subprocess.run(f"...{user_input}...", shell=True)
```

密码通过 stdin 长度前缀协议发送。

## 8.4 helper 输出

stdout 只输出一行 JSON：

```json
{
  "ok": true,
  "operation": "unlock-and-rescan",
  "stable_id": "abc123...",
  "state_before": "locked",
  "state_after": "unlocked",
  "old_device_node": "/dev/sda",
  "new_device_node": "/dev/sdb",
  "rescanned": true,
  "error_code": null,
  "message": "Device unlocked"
}
```

失败：

```json
{
  "ok": false,
  "operation": "unlock-and-rescan",
  "stable_id": "abc123...",
  "error_code": "wrong_password",
  "message": "Password verification failed"
}
```

要求：

- stdout 不打印调试信息；
- stderr 可写本地诊断，但不包含密码、派生值、完整 payload；
- JSON 中不包含完整序列号；
- GUI 不通过字符串匹配判断错误，必须使用 `error_code`。

## 8.5 Polkit 策略

建议 action id：

```text
io.github.REPLACE_ME.passportunlocker.unlock
```

初始策略使用：

```xml
<allow_any>no</allow_any>
<allow_inactive>no</allow_inactive>
<allow_active>auth_admin_keep</allow_active>
```

开发稳定并完成 helper 安全审计后，才讨论是否改成更便利的 `auth_self_keep` 或针对本地活跃会话的更宽松规则。

不要为了省一次密码输入，就给整个 `/dev/sd*` 设置全局 `0666` 权限，也不要建议用户加入 `disk` 组。

## 8.6 helper 安全校验清单

helper 每次执行必须：

1. stable_id 格式合法；
2. 从 pyudev 重新枚举；
3. 找到且只找到一个匹配设备；
4. 匹配对象是 block disk；
5. 真实路径位于 `/dev`；
6. `os.stat()` 确认为块设备；
7. 不是符号链接或解析后仍是同一块设备；
8. 设备位于 USB parent；
9. VID/PID、型号、序列号与 stable_id 一致；
10. 打开后通过协议签名探测；
11. 只发送预定义 CDB；
12. 限制响应和 payload 长度；
13. 设置 SCSI timeout；
14. 操作后关闭 fd；
15. 重扫描前保存 scsi_host；
16. 重扫描后按 stable_id 重找设备；
17. 任何身份不一致立即失败。

---

# 9. 挂载策略

解锁和挂载是两个不同步骤。

v0.1 推荐：

1. helper 只执行解锁和重新扫描；
2. 设备重新出现后，等待桌面环境/UDisks2 自动挂载；
3. GUI 观察分区是否出现；
4. 若已挂载，显示挂载点；
5. 若未挂载，提示用户在文件管理器中点击设备。

不要直接在 root helper 中：

```bash
mount /dev/sdX1 /mnt/...
```

原因：

- 无法正确继承桌面用户；
- 挂载目录所有权可能错误；
- 文件管理器不知道挂载状态；
- 多分区和文件系统类型复杂；
- 会绕过 UDisks2 的桌面策略。

后续可通过 UDisks2 D-Bus 请求用户态挂载，但这不是 v0.1 必需条件。

---

# 10. CLI 兼容层

重构后保留一个安全 CLI：

```bash
passport-unlocker list
passport-unlocker status --device-id <stable-id>
passport-unlocker unlock --device-id <stable-id>
```

要求：

- 默认不提供 erase；
- 默认不接受密码命令行参数；
- `unlock` 使用 `getpass`；
- CLI 调用同一个 core/service；
- 退出码稳定。

建议退出码：

```text
0   success
2   invalid arguments
10  no device
11  multiple/ambiguous identity
12  unsupported device
20  permission denied
21  wrong password
22  unlock blocked
23  device disconnected
30  protocol error
31  rescan failed
40  internal error
```

可保留一个仅开发使用的上游兼容 wrapper，但正式包不应安装危险参数。

---

# 11. Python 工程和依赖

## 11.1 pyproject.toml

替代旧 `setup.py`，使用 `src` layout 和 entry points：

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "passport-unlocker"
version = "0.1.0"
description = "Unofficial Linux unlocker for compatible WD My Passport drives"
requires-python = ">=3.10"
license = { text = "GPL-2.0-only" }
dependencies = [
  "pyudev>=0.24",
]

[project.scripts]
passport-unlocker = "passport_unlocker.cli.main:main"
passport-unlocker-gui = "passport_unlocker.gui.application:main"
passport-unlocker-helper = "passport_unlocker.helper.main:main"
```

GTK/PyGObject 在 Ubuntu `.deb` 中优先使用系统包，不建议依赖 pip 构建 GI。

## 11.2 Ubuntu 24.04 开发依赖

```bash
sudo apt install \
  python3 \
  python3-dev \
  python3-venv \
  python3-gi \
  python3-pyudev \
  gir1.2-gtk-4.0 \
  gir1.2-adw-1 \
  policykit-1 \
  build-essential \
  git \
  pytest \
  python3-pytest \
  python3-setuptools \
  python3-wheel \
  debhelper \
  dh-python \
  devscripts \
  build \
  desktop-file-utils \
  appstream
```

创建开发环境时，PyGObject 来自系统包，可使用：

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

不要执行：

```bash
sudo pip install ...
pip install --break-system-packages ...
```

## 11.3 开发工具

建议：

```text
pytest
pytest-cov
ruff
mypy
build
```

`ruff` 负责格式和 lint，`mypy` 优先检查 core/helper，GUI 的 GI 动态类型可以局部放宽，但不得全项目关闭类型检查。

---

# 12. Debian/Ubuntu 安装包

## 12.1 首选 `.deb`

AppImage 只能方便分发用户态程序，但本项目还需要：

- `/usr/libexec` helper；
- Polkit policy；
- 桌面入口；
- XDG autostart；
- 图标；
- 应用元数据。

因此 v0.1 首选：

```text
passport-unlocker_0.1.0-1_all.deb
```

如果自行实现的 SG_IO transport 是纯 Python，包可为 `all`；若包含 C 扩展，则应为 `amd64` 等架构包。

## 12.2 运行时依赖

建议 Debian `Depends`：

```text
python3
python3-gi
python3-pyudev
gir1.2-gtk-4.0
gir1.2-adw-1
policykit-1
```

## 12.3 安装路径

```text
/usr/bin/passport-unlocker
/usr/bin/passport-unlocker-gui
/usr/libexec/passport-unlocker-helper
/usr/lib/python3/dist-packages/passport_unlocker/
/usr/share/applications/io.github.REPLACE_ME.PassportUnlocker.desktop
/etc/xdg/autostart/io.github.REPLACE_ME.PassportUnlocker.Monitor.desktop
/usr/share/polkit-1/actions/io.github.REPLACE_ME.PassportUnlocker.policy
/usr/share/metainfo/io.github.REPLACE_ME.PassportUnlocker.metainfo.xml
/usr/share/icons/hicolor/scalable/apps/io.github.REPLACE_ME.PassportUnlocker.svg
/usr/share/doc/passport-unlocker/
```

## 12.4 postinst

`postinst` 只做必要缓存更新：

```bash
update-desktop-database
gtk-update-icon-cache
```

不要在安装脚本中：

- 修改用户 shell；
- 自动加入 `disk` 组；
- 改 `/dev/sd*` 权限；
- 下载 GitHub 代码；
- 用 pip 修改系统 Python；
- 自动运行解锁；
- 搜索或保存硬盘密码。

---

# 13. 许可证与分发风险

## 13.1 上游许可证

`wdpassport-utils` 仓库标记为 GPL-2.0，`setup.py` 写的是 `GPLv2`。从该代码衍生的项目应保留：

- 原作者版权；
- GPL 文本；
- 修改说明和日期；
- 源代码获取方式；
- 无担保声明。

## 13.2 py3_sg 许可证风险

当前 `py3_sg` 仓库标记为 GPL-3.0，而上游项目是 GPL-2.0。GPL-2.0-only 与 GPL-3.0 组合在公开分发时可能存在许可证不兼容问题。

这不是本文档能够给出的正式法律结论，但发布安装包前必须处理。不要因为原上游 `setup.py` 已经写了该依赖，就假设组合一定合规。

## 13.3 推荐处理方式

优先方案：

```text
对 Linux SG_IO 公共 UAPI 做独立、最小、可审查的 clean-room transport 实现，
不复制 py3_sg 的源码和独特结构。
```

实施原则：

1. 只参考 Linux 公共接口定义和公开文档；
2. 不复制 `py3_sg.c`；
3. 记录 clean-room 实现说明；
4. 为 transport 编写独立测试；
5. 保持项目 GPL-2.0-only，与上游一致；
6. 发布前由熟悉开源许可证的人复核。

备选方案：

- 联系上游作者确认是否可以将 `wdpassport-utils` 以 GPL-2.0-or-later 或 GPL-3.0 发布；
- 获得明确授权后统一许可证。

本地个人实验阶段可以继续使用已经安装的 `py3_sg` 验证功能，但正式 `.deb` 不应在许可证未澄清的情况下直接捆绑该组合。

---

# 14. 安全模型

## 14.1 受保护资产

- 用户硬盘密码；
- 磁盘数据；
- 原始块设备访问权限；
- 设备稳定身份；
- 系统 root 权限；
- 解锁协议和状态；
- 本地日志。

## 14.2 威胁

- 密码出现在 argv；
- 密码进入 shell history；
- GUI 以 root 运行；
- helper 接受任意设备路径；
- `/dev/sda` 在操作前被替换；
- 恶意 USB 伪造型号；
- 任意 SCSI 命令注入；
- 日志泄露密码 hash；
- 多设备时解锁错盘；
- 重扫描后设备节点变化；
- 设备在操作中拔出；
- UI 重复点击并发解锁；
- 错误密码无限快速尝试；
- 把 destructive operation 意外暴露。

## 14.3 必须满足的安全规则

```text
S1  密码不得出现在命令行。
S2  密码不得写入磁盘。
S3  密码不得写入日志。
S4  GUI 不以 root 运行。
S5  helper 只接受 stable_id，不直接信任 GUI 传入的 /dev/sdX。
S6  helper 必须重新发现和验证设备。
S7  helper 只实现固定的状态、解锁、重扫描操作。
S8  不提供 raw SCSI 通道。
S9  不提供 erase、reset-key、format、change-password。
S10 解锁后再次查询状态。
S11 重扫描后按 stable_id 重新发现。
S12 所有超时和设备拔出均可恢复。
S13 同一 stable_id 同时只允许一个操作。
S14 UI 连续失败要有本地短暂退避，避免误操作。
S15 错误报告默认隐藏完整序列号。
```

## 14.4 密码尝试限制

硬盘固件可能有自己的失败计数。应用侧应：

- 每次只允许一个解锁请求；
- 错误后按钮延迟 1–3 秒恢复；
- 若状态变成 `LOCKED_BLOCKED`，立即停止；
- 明确提示用户安全拔出后重新连接；
- 不实现批量密码或自动重试；
- 不提供脚本化密码文件入口。

---

# 15. 测试设计

## 15.1 单元测试

### password.py

- 合成黄金向量；
- salt 中途 `00 00`；
- 空 salt；
- Unicode 密码；
- iteration 为 0、1、2；
- 异常大 iteration 的上限校验；
- 明确 UTF-16LE。

### status parser

- locked；
- unlocked；
- no lock；
- blocked；
- no keys；
- unknown state；
- 错误签名；
- 响应过短；
- password length 异常。

### Handy Store

- 正确 signature；
- 错误 signature；
- 正确 checksum；
- 错误 checksum；
- iteration 解析；
- salt 解析；
- hint 截断。

### unlock builder

- CDB 字节完全匹配；
- 长度字段正确；
- payload header；
- 密码 hash 长度；
- 写后状态验证；
- transport 抛 OSError；
- SCSI sense error；
- 写成功但状态仍 locked。

### discovery

使用 mock pyudev 数据验证：

- 单 WD 设备；
- 两个 WD 设备；
- 非 WD USB；
- SATA WD；
- 分区而非 disk；
- 缺失 serial；
- 重扫描节点变化；
- stable_id 一致性。

### helper wire

- 正常长度前缀；
- 读取不足；
- 长度超过上限；
- 非 UTF-8；
- 空密码；
- stdout JSON；
- 确保错误输出无密码。

## 15.2 集成测试

使用 `FakeScsiTransport`：

```text
GUI controller
  → fake privileged runner
  → helper service
  → fake transport
```

覆盖：

- 正确密码；
- 错误密码；
- 已解锁；
- blocked；
- 中途拔盘；
- 重扫描超时；
- 多设备；
- 用户取消 Polkit；
- 用户关闭窗口；
- 重复点击。

## 15.3 真机测试

初始设备：

```text
WD My Passport 2626
约 1 TB
```

不要在文档、测试和公开日志中硬编码完整序列号。

测试前：

1. 重要数据已有独立备份；
2. 确认目标型号和容量；
3. `lsblk` 再次确认系统盘不是目标；
4. 禁止出现 `erase`、`reset`、`format`；
5. 先运行上游已验证命令确认密码可用；
6. 一次只连接一块测试盘完成首轮；
7. 后续再测试多设备。

真机用例：

| 编号 | 用例 | 期望 |
|---|---|---|
| H01 | 插入锁定设备 | GUI 自动弹出 |
| H02 | 正确密码 | 解锁并重新发现 |
| H03 | 错误密码 | 明确错误，数据不变 |
| H04 | 再输正确密码 | 成功 |
| H05 | 已解锁设备 | 幂等成功 |
| H06 | 操作中拔盘 | 提示断开，不崩溃 |
| H07 | 两块候选盘 | 可分别选择 |
| H08 | 重扫描节点变化 | 仍通过 stable_id 识别 |
| H09 | 取消 Polkit | 安全返回 |
| H10 | 重启桌面会话后插盘 | 自动监测正常 |
| H11 | Wayland | 正常弹窗 |
| H12 | X11 | 正常弹窗 |

绝不执行：

```text
secure erase
reset key
change password
remove password
fdisk
mkfs
```

## 15.4 硬件测试日志模板

```text
Date:
OS:
Kernel:
Desktop:
Application version:
Device model:
Capacity:
Serial suffix:
USB VID:PID:
Initial node:
Initial state:
Operation:
Result:
Node after rescan:
Mounted:
Relevant sanitized logs:
```

日志不得包含密码、派生 hash、完整序列号或原始解锁 payload。

---

# 16. CI 和质量门槛

## 16.1 GitHub Actions

`test.yml`：

```text
Ubuntu 24.04
Python 3.10/3.12
ruff check
ruff format --check
mypy core helper
pytest --cov
python -m build
```

硬件相关测试必须标记：

```python
@pytest.mark.hardware
```

CI 默认排除。

## 16.2 package.yml

执行：

```text
dpkg-buildpackage -us -uc
desktop-file-validate
appstreamcli validate
安装到临时 Ubuntu 环境
运行 --version
运行 list，无设备时正常退出
```

## 16.3 Definition of Done

每个 PR 至少满足：

- 无 `shell=True`；
- 无密码 argv；
- 无新增裸 `except`；
- core 无 `sys.exit`；
- helper 不接受任意原始命令；
- 新行为有测试；
- README 更新；
- `ruff` 通过；
- `pytest` 通过；
- 无 destructive UI/CLI；
- 安全相关改动有独立说明。

---

# 17. 分阶段开发计划

## Phase 0：建立基线，不改行为

### 目标

保存上游行为并形成审查依据。

### Codex 应做

1. 阅读所有上游文件；
2. 创建 `docs/UPSTREAM_ANALYSIS.md`；
3. 列出函数、CDB、全局变量、退出点、危险功能；
4. 把上游脚本复制为受保护参考，例如：
   `legacy/wdpassport_utils_upstream.py`；
5. 记录上游 commit hash；
6. 不修改协议字节。

### 验收

- 上游 CLI 仍可按原方式运行；
- 文档准确；
- 没有删除任何功能；
- 没有真机写操作。

---

## Phase 1：拆出纯核心库

### 目标

把状态解析、Handy Store、密码派生和解锁构造拆成可测试模块。

### 文件

```text
src/passport_unlocker/core/constants.py
src/passport_unlocker/core/models.py
src/passport_unlocker/core/errors.py
src/passport_unlocker/core/password.py
src/passport_unlocker/core/protocol.py
src/passport_unlocker/core/transport.py
tests/unit/...
```

### 要求

- Fake transport；
- 黄金测试；
- 无 pyudev；
- 无 GTK；
- 无 root；
- 无 sysfs；
- 无打印；
- 无 `sys.exit`；
- 与上游字节行为一致。

### 验收

- 所有黄金测试通过；
- 新协议层生成的 status/unlock CDB 与上游完全一致；
- 错误通过异常表达。

---

## Phase 2：设备发现和 stable_id

### 目标

支持多个设备和重扫描后的稳定身份。

### 文件

```text
src/passport_unlocker/devices/identity.py
src/passport_unlocker/devices/discovery.py
src/passport_unlocker/devices/monitor.py
tests/unit/test_discovery.py
tests/unit/test_identity.py
```

### 要求

- 不硬编码 `/dev/sda`；
- 不硬编码用户设备完整序列号；
- 宽松候选发现和严格 helper 验证分开；
- 设备列表可排序；
- 序列号 UI 默认只显示后四位。

### 验收

- mock pyudev 测试覆盖多设备；
- stable_id 在节点变化时保持一致。

---

## Phase 3：安全 CLI 和业务服务

### 目标

用新库实现无危险功能的 CLI。

### 文件

```text
src/passport_unlocker/core/service.py
src/passport_unlocker/cli/main.py
tests/integration/test_helper_fake_transport.py
```

### 命令

```text
list
status
unlock
```

### 验收

- 密码通过 getpass；
- 无 erase；
- 退出码稳定；
- fake transport 完整流程通过。

---

## Phase 4：特权 helper

### 目标

实现一次性、可审查、固定接口的 root helper。

### 文件

```text
src/passport_unlocker/helper/main.py
src/passport_unlocker/helper/validation.py
src/passport_unlocker/helper/wire.py
data/*.policy
tests/unit/test_validation.py
tests/unit/test_wire.py
```

### 要求

- stdin 长度前缀；
- stdout JSON；
- stable_id；
- 无 shell；
- 严格设备验证；
- 固定命令；
- 无 destructive operation；
- 密码不进日志。

### 验收

- 用户取消授权可恢复；
- 恶意 stable_id 被拒绝；
- 任意路径无法传入；
- 错误码稳定。

---

## Phase 5：GTK GUI

### 目标

实现手动启动的图形解锁窗口。

### 文件

```text
src/passport_unlocker/gui/application.py
src/passport_unlocker/gui/window.py
src/passport_unlocker/gui/controller.py
src/passport_unlocker/gui/worker.py
```

### 要求

- GTK 4；
- GUI 普通用户运行；
- worker 不阻塞主线程；
- 多设备选择；
- 错误分类；
- 不保存密码；
- 解锁按钮防重复点击。

### 验收

- fake runner 可演示全部状态；
- 无真实设备也可启动；
- UI 不因 helper 超时冻结。

---

## Phase 6：自动发现

### 目标

插盘自动弹窗。

### 文件

```text
src/passport_unlocker/devices/monitor.py
data/autostart/*.desktop
```

### 要求

- XDG autostart；
- pyudev 防抖；
- `GLib.idle_add`；
- 解锁重扫描不重复弹多个窗口；
- 可在设置中关闭自动弹窗。

### 验收

- 模拟 add/remove/change；
- GUI 单实例；
- 同一设备事件合并。

---

## Phase 7：SG_IO clean-room transport

### 目标

去除正式分发对 `py3_sg` 的依赖。

### 文件

```text
src/passport_unlocker/core/linux_sg_io.py
docs/SG_IO_CLEAN_ROOM.md
tests/unit/test_linux_sg_io.py
```

### 要求

- 仅参考 Linux UAPI；
- 不复制 `py3_sg.c`；
- 限定 CDB 和 buffer；
- sense 数据结构化；
- 超时；
- 关闭 fd；
- 记录 clean-room 过程。

### 验收

- fake ioctl 测试；
- 与本地 `py3_sg` 在测试盘上的只读 status 结果一致；
- 再比较 unlock；
- 发布包不依赖 py3_sg。

---

## Phase 8：打包和真机验证

### 目标

生成可安装 `.deb`。

### 要求

- 正确安装 desktop、autostart、policy、icons；
- 不运行 pip；
- 不改 disk group；
- 卸载干净；
- 真机测试按第 15 节执行。

### 验收

```bash
sudo apt install ./passport-unlocker_0.1.0-1_all.deb
passport-unlocker --version
passport-unlocker-gui
```

插入测试盘后自动弹窗，正确密码成功解锁。

---

# 18. 可直接粘贴给 Codex 的阶段提示词

## Prompt 1：只做上游分析

```text
请先不要修改功能代码。阅读当前仓库中的 README.md、setup.py、LICENSE 和 wdpassport-utils.py，完成以下工作：

1. 说明每个函数的职责和调用关系。
2. 列出状态查询、Handy Store 读取、密码派生、解锁、重新扫描对应的 CDB 和字段。
3. 找出所有全局变量、sys.exit、裸 except、print 副作用和危险功能。
4. 创建 docs/UPSTREAM_ANALYSIS.md。
5. 保存当前 commit hash。
6. 给出下一阶段最小重构计划，但不要实施。
7. 不执行真实硬盘写命令，不调用 erase/change password。
8. 中文汇报，先说明计划和涉及文件。
```

## Prompt 2：拆核心库

```text
参考 docs/DEVELOPMENT_SPEC.md 的 Phase 1，把上游协议逻辑拆成可导入、可测试的 core 模块。

要求：
- 保持协议字节行为不变。
- 新增 ScsiTransport Protocol 和 FakeScsiTransport。
- 用 dataclass/enum 表达状态。
- 底层不得 print、sys.exit、读取终端或依赖全局变量。
- 添加密码派生黄金测试：
  password=Test123!
  salt=41 00 42 00 43 00 44 00
  iteration=2
  expected=5965eea11dfd0cd9567f5955f23489d9160943c2fec9e9802e4726ce1cdfb38b
- 不接触真实设备。
- 先列出要修改和新增的文件，再实施。
- 运行 pytest 和 ruff，并汇报结果。
```

## Prompt 3：设备发现

```text
实现 docs/DEVELOPMENT_SPEC.md Phase 2。

重点：
- 使用 pyudev 枚举 block/DEVTYPE=disk。
- 支持多个 WD My Passport 候选设备。
- 生成 stable_id，不能使用 /dev/sdX 作为稳定身份。
- GUI 展示只使用序列号后四位。
- helper 侧严格验证与 GUI 宽松发现必须分离。
- 不硬编码我的设备序列号，也不硬编码 /dev/sda。
- 全部使用 mock pyudev 测试。
```

## Prompt 4：安全 helper

```text
实现一次性 pkexec helper，只允许 unlock-and-rescan。

安全要求：
- helper 安装目标为 /usr/libexec/passport-unlocker-helper。
- GUI/调用方只传 stable_id。
- 密码通过 stdin 的 4 字节大端长度前缀 + UTF-8 字节传入。
- 密码不得出现在 argv、环境变量、日志、JSON 和异常。
- helper 重新发现设备并验证整盘、USB、型号、序列号和协议签名。
- 禁止 raw-scsi、erase、reset-key、format、change-password。
- stdout 只输出单行结构化 JSON。
- 不使用 shell=True。
- 为恶意输入、超长密码、设备消失、错误密码、重扫描超时写测试。
- 先给出威胁分析和文件计划。
```

## Prompt 5：GTK GUI

```text
实现 GTK 4 + Libadwaita GUI。

要求：
- GUI 以普通用户身份运行。
- 支持无设备、单设备和多设备。
- 使用 Gtk.PasswordEntry。
- 点击解锁后异步调用 pkexec helper，不能阻塞 GTK 主线程。
- 密码不持久化，操作结束后清空输入框。
- 显示 authorizing/checking/unlocking/rescanning/completed/failed 状态。
- 对 wrong_password、blocked、permission_denied、device_disconnected、rescan_timeout 分别提示。
- 重复点击必须被禁止。
- 使用 fake privileged runner 完成 GUI 测试，不访问真实硬盘。
```

## Prompt 6：自动弹窗

```text
实现用户会话中的 pyudev 监测和 XDG autostart。

要求：
- 不让 udev 直接启动 GUI。
- 使用 Gtk.Application 单实例。
- add/change 事件做防抖。
- 通过 GLib.idle_add 更新 UI。
- 解锁时产生的 remove/add 不能重复弹出多个窗口。
- 可关闭自动弹窗。
- 不需要 udev chmod 规则，不修改 disk 组。
```

## Prompt 7：打包

```text
为 Ubuntu 24.04 创建 Debian 包。

要求：
- 安装 Python 模块、/usr/bin 入口、/usr/libexec helper、desktop、autostart、Polkit policy、AppStream metadata 和图标。
- 运行时使用 apt 的 python3-gi、gir1.2-gtk-4.0、gir1.2-adw-1、python3-pyudev。
- postinst 不运行 pip、不联网、不修改用户组。
- 添加 desktop-file-validate、appstreamcli validate 和安装后 smoke test。
- 当前若仍依赖 GPL-3.0 的 py3_sg，不得宣称发布包许可证问题已解决；优先先完成 clean-room SG_IO transport。
```

---

# 19. Codex 审查清单

每次 Codex 完成一个阶段后，让它回答：

```text
1. 修改了哪些文件？
2. 每个修改为什么必要？
3. 是否改变了协议字节？
4. 是否新增了 root 权限面？
5. 密码可能出现在哪里？
6. 是否存在 shell=True、os.system、裸 except、sys.exit？
7. 是否硬编码 /dev/sda 或序列号？
8. 是否新增 destructive operation？
9. 新增了哪些测试？
10. 运行了哪些命令，结果是什么？
11. 当前仍有哪些风险和未完成项？
```

---

# 20. 发布前最终检查

## 功能

- [ ] 手动启动可发现设备；
- [ ] 插盘自动弹窗；
- [ ] 多设备可选择；
- [ ] 正确密码可解锁；
- [ ] 错误密码不破坏数据；
- [ ] 已解锁幂等；
- [ ] 重扫描后节点变化可跟踪；
- [ ] 桌面可识别数据分区；
- [ ] 取消授权可恢复；
- [ ] 拔盘不崩溃。

## 安全

- [ ] GUI 非 root；
- [ ] 密码不在 argv；
- [ ] 密码不在日志；
- [ ] helper 固定路径；
- [ ] 无 shell；
- [ ] helper 只接受 stable_id；
- [ ] 严格设备验证；
- [ ] 无 raw SCSI；
- [ ] 无 erase；
- [ ] 无 change password；
- [ ] 无 format；
- [ ] 无 disk group 修改。

## 工程

- [ ] core 无全局设备句柄；
- [ ] core 无 print；
- [ ] core 无 sys.exit；
- [ ] 异常结构化；
- [ ] 单元测试通过；
- [ ] GUI fake 测试通过；
- [ ] `.deb` 可安装和卸载；
- [ ] desktop 文件通过验证；
- [ ] AppStream 通过验证；
- [ ] README 有非官方声明；
- [ ] SECURITY.md 有漏洞报告方式。

## 许可证

- [ ] 保留上游作者和 GPL-2.0；
- [ ] 修改文件有说明；
- [ ] 提供完整源码；
- [ ] py3_sg 组合风险已解决或获得授权；
- [ ] 第三方依赖许可证清单完整；
- [ ] 未使用 WD 官方图标或误导性命名。

---

# 21. 关键设计结论

1. **能够做成 Linux 图形解锁应用。**底层协议链路已由现有 CLI 和当前测试设备验证。
2. **不能依赖 USB 自动运行。**正确方案是安装一次 Linux 客户端，然后插盘自动弹窗。
3. **第一版应只做解锁。**不要把修改密码和 secure erase 带进 GUI。
4. **GUI 不能以 root 运行。**使用最小化的 Polkit helper。
5. **不能硬编码 `/dev/sda`。**重扫描后节点可能变化，必须用 stable_id。
6. **先重构和测试协议，再做 GUI。**否则 UI bug、权限 bug和协议 bug会混在一起。
7. **正式包应避免 `sudo pip`。**用 `.deb` 和系统依赖解决 PEP 668。
8. **公开分发前处理许可证。**上游 GPL-2.0 与当前 py3_sg GPL-3.0 的组合不能被忽略。
9. **clean-room SG_IO transport 是推荐路线。**它同时改善打包、可维护性和许可证边界。
10. **所有真机测试都必须以数据安全为第一优先级。**

---

# 22. 核对依据

本文档基于以下公开资料和当前上游状态整理：

```text
Upstream:
https://github.com/0-duke/wdpassport-utils

SCSI transport currently referenced by upstream:
https://github.com/tvladyslav/py3_sg

Polkit documentation:
https://polkit.pages.freedesktop.org/polkit/

GTK / PyGObject documentation:
https://pygobject.gnome.org/
https://api.pygobject.gnome.org/

Freedesktop udev/systemd/XDG specifications:
https://www.freedesktop.org/software/systemd/man/
https://specifications.freedesktop.org/

Python packaging:
https://packaging.python.org/
```

应在真正开始开发时记录上游 commit hash，因为仓库后续可能变化。

---

# 附录 A：建议的第一版 README 摘要

```text
Passport Unlocker for Linux is an unofficial open-source utility for
unlocking compatible WD My Passport hardware-encrypted drives on Linux.

The application does not crack or bypass passwords. It sends a compatible
authentication request to the drive controller and requires the correct
drive password.

Version 0.1 supports device discovery, status checking, unlock, and device
rescan. It intentionally does not provide secure erase, key reset, password
change, formatting, or automatic password storage.

This project is not affiliated with or endorsed by Western Digital.
Use it at your own risk and keep independent backups of important data.
```

# 附录 B：禁止 Codex 实现的函数名和关键词

代码审查可搜索：

```text
secure_erase
reset_key
change_password
change_passwd
mkfs
fdisk
parted
wipefs
sg_raw
shell=True
os.system
--password
password=
MODE="0666"
GROUP="disk"
```

出现不代表一定错误，但必须人工解释和审查。v0.1 的生产代码中不应出现 destructive operation。

# 附录 C：本地开发安全命令

只读检查：

```bash
lsblk -d -o NAME,PATH,TRAN,VENDOR,MODEL,SERIAL,SIZE
udevadm info --query=property --name=/dev/sdX
```

上游已验证的状态查询：

```bash
sudo /opt/wdpassport-venv/bin/wdpassport-utils.py --device /dev/sdX
```

已确认目标设备和密码后才执行：

```bash
sudo /opt/wdpassport-venv/bin/wdpassport-utils.py \
  --device /dev/sdX \
  --unlock \
  --mount
```

永远不要在有重要数据的设备上执行：

```text
-e
--erase
```


