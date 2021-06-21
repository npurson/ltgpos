# Ltgwave 雷击波形分类 IPC 部署

## Python 服务端

### Python 环境配置

**Requirements**：torch（请参考 PyTorch 官网指南安装对应版本，其余可直接 pip install），scipy，pyts，matplotlib，pillow

环境配置完成后，运行以下测试程序验证分类器模块正常运行。

```Bash
python test_model.py
```

预计输出：

```B
1
1
1
0
0
0
0
0
```

`test_model.py` 测试通过后可删除。

## C++ 客户端

`caller.cpp` 包含了调用 Python 服务端的样例，与 Python 服务端的相对路径关系无影响。

客户端调用流程如下：

```Cpp
#include <WinSock2.h>

// WinSock 服务初始化，对应 WSACleanup() 释放资源
WSADATA wsaData;
WSAStartup(MAKEWORD(2, 2), &wsaData);

// 拉起 Ltgwave Python 服务端，对应 ipc_exit() 终止服务端
ipc_init("C:\\path\\to\\ltgwave\\ltgwave\\ltgwave.py", 8889, "C:\\path\\to\\ltgwave\\ltgwave\\model.pt");

// 建立 socket 连接，对应 closesocket() 关闭连接
SOCKET sock = ipc_connet(8889);

while (...) {       // 不断调用 Ltgwave 服务端进行雷击波形分类。
    int result = ipc_waveclf(sock, 2000000, data);
}

if (...) {          // 如有需要，可关闭连接，之后可重新建立连接
    closesocket(sock);
    sock = ipc_connet(8889);
}

// 终止 Ltgwave 服务端及 socket 连接，如有需要仍可以重新通过 ipc_init() 拉起并进行连接。
ipc_exit(sock);

// 释放 WinSock 服务资源，仅在程序退出时调用即可
WSACleanup();
```

修改 `caller.cpp` 88 行的 Python 服务端路径以及模型权重路径即可运行。

C++ 客户端预期输出：

```Bash
1
1
1
0
0
0
0
0
```

Python 服务端预期输出：

```Bash
Model loaded.
Connected
flag  0
freq  2000000.0
insz  2400
data  [-14. -14. -14. ...   0. -14. -28.]
 ret  1

flag  0
freq  2000000.0
insz  2400
data  [ 0.    0.    0.   ... -2.72 -2.72 -2.72]
 ret  1

flag  0
freq  2000000.0
insz  2400
data  [   0.      0.      0.   ... -339.77 -339.77 -339.77]
 ret  1

Closed
Connected
flag  0
freq  2000000.0
insz  2400
data  [  0.     0.     0.   ... 551.62 519.79 477.36]
 ret  0

flag  0
freq  2000000.0
insz  2400
data  [ -3.12  -3.12  -3.12 ... -46.8  -46.8  -46.28]
 ret  0

flag  0
freq  2000000.0
insz  2400
data  [-0.94 -0.47 -0.47 ... -6.08 -6.08 -5.62]
 ret  0

flag  0
freq  2000000.0
insz  2400
data  [-0.55 -0.55 -0.55 ...  8.01  8.19  8.19]
 ret  0

flag  0
freq  2000000.0
insz  2400
data  [  0.     0.     0.   ... 172.69 172.69 179.09]
 ret  0
```

加载模型（即显示 Model Loaded）约为 10 s，单次推理（即打出一组调试信息）约为 1 s。

若想关闭 Python 服务端输出，修改 `ltgwave.py` 第 16 行为：

```Python
DEBUG = False
```
