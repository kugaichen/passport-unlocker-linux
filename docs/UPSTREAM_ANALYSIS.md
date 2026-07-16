# 上游分析

## 基线

- 仓库：`https://github.com/0-duke/wdpassport-utils`
- commit：`4317baece37fa9c41070d790427c03f0a782a6ad`
- commit 日期：2023-02-09
- 文件：`.gitignore`、`LICENSE`、`README.md`、`setup.py`、`wdpassport-utils.py`
- 许可证标记：GPLv2

## 代码结构与调用关系

`main()` 负责参数解析、pyudev 自动发现、打开原始块设备和分派操作：

```text
main
├─ get_encryption_status
├─ unlock
│  ├─ get_encryption_status
│  ├─ read_handy_store_block1 → read_handy_store
│  ├─ mk_password_block
│  └─ py_sg.write
├─ change_password
│  ├─ get_encryption_status
│  ├─ read/write_handy_store_block1
│  ├─ mk_password_block
│  └─ py_sg.write
├─ secure_erase → get_encryption_status → py_sg.write
└─ enable_mount → get_encryption_status → sysfs delete/scan
```

辅助函数 `fail/success/question` 生成 ANSI 文本，`sec_status_to_str` 与 `cipher_id_to_str` 做显示映射，`_scsi_pack_cdb`、`htonl`、`htons` 做字节构造，`hsb_checksum` 计算 Handy Store checksum。

## 协议命令

| 操作 | CDB | 方向 | v0.1 |
|---|---|---|---|
| 状态查询 | `c0 45 00 00 00 00 00 00 30 00` | 读 512 | 保留 |
| Handy Store 读 | `d8 ... page(be32) ... 01 00` | 读 512 | 保留 |
| Handy Store 写 | `da ... page(be32) ... 01 00` | 写 512 | 禁止 |
| 解锁 | `c1 e1 ... length 00` | 写 | 保留 |
| 修改密码 | `c1 e2 ... length 00` | 写 | 移除 |
| 重置内部密钥 | `c1 e3 key-reset ... length 00` | 写 | 移除 |

状态响应签名为 `data[0] == 0x45`，状态在 byte 3，cipher 在 byte 4，密码块长度为 bytes 6–7（大端）。Handy Store page 1 签名为 `00 01 44 57`，iteration 在 offset 8（小端 uint32），salt 为 bytes 12–19。

## 风险点

- 全局可变对象：`dev`、`device_name`。
- 底层协议函数直接 `print()` 和多处 `sys.exit(1)`。
- `unlock`、`change_password`、`secure_erase` 和设备打开路径使用裸 `except`。
- `unlock` 只按 SCSI write 是否抛异常判断成功，没有写后状态验证。
- 设备发现只检查父链 `ID_SERIAL` 前缀，且允许直接传 `/dev/sdX`。
- `change_password` 可写 Handy Store 和修改/移除密码。
- `secure_erase` 使用 `C1/E3` 更换内部密钥，会永久丢失数据。
- `enable_mount` 写 sysfs 删除设备并扫描，节点可能变化。
- `setup.py` 依赖 Git 形式的 `py3_sg`，不适合 PEP 668 和可复现打包。

本项目保留只读参考文件，但正式 CLI/GUI/helper 不包含密码修改、Handy Store 写入、E2/E3 命令或任意设备路径入口。

