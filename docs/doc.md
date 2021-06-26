# Ltgpos RPC 使用说明

本程序通过 RPC（Remote Procedure Call，远程过程调用）实现客户端服务器（目前为 192.168.10.50）读取数据库数据，调用服务端服务器（目前为 192.168.10.48）上部署的雷电定位程序，并将计算结果写回数据库的功能。

## 服务端

服务端雷电定位程序位于 192.168.10.48 的 `D:\ltgpos_server`，通过命令行调用，调用时需指定端口号（1024~65535，与客户端一致即可），例如

```bash
D:\ltgpos_server > ltgpos_server.exe 8889
```

服务端由人工启动，随后一直停留在后台运行，不断接收客户端程序连接。

## 客户端

客户端程序位于 192.168.10.50 的 `D:\ltgpos_client`，通过 `ltgpos.bat` 与 `auto_ltgpos.bat` 脚本调用，前者供人工手动调用，后者由 Windows 定时服务每小时启动一次。

手动调用时需用文本编辑器编辑 `ltgpos.bat` 设定参数，之后直接双击启动或在命令行中启动，参数设定样例如下：

```bash
python src/ltgpos_client.py \
    --addr 192.168.10.48 --port 8889 \
    --start_datetime 2021-05-20 06:30:21 \
    --end_datetime 2021-05-21 06:30:21 \
    --src_table waveinfo_rs \
    --dst_table ltgpos_2d
```

参数说明如下：

- `--addr`: 服务端 IP 地址，**必选**
- `--port`: 服务端程序端口号，**必选**，与服务端设置一致即可
- `--start_datetime`: **可选**，选取数据起始时间，按照 datetime 字符串格式，例如 `2021-05-20`、`2021-05-20 06:30:21`，不设置时选取从最早数据记录时间开始
- `--end_datetime`: **可选**，选取数据终止时间，格式同上，不设置时选取截至最晚数据记录时间
- `--src_table`: **必选**，存放待计算数据的表，待选项包括 `waveinfo_rs`, `waveinfo_ic`, `waveinfo_nb`, `waveinfo_pb`
- `--dst_table`: **可选**，指定计算结果存入的表，不存在会自动新建，不指定时默认为诸如 `ltgpos_rs` 的后缀与 `src_table` 对应的表名
