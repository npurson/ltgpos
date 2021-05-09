#include <iostream>
#include <stdio.h>
#include <vector>
#include <winsock2.h>
#include <fstream>
#include <direct.h>
#include <ctime>
using namespace std;

#define RECVLENGTH 30
#define HEADLENGTH 10

#pragma comment(lib, "ws2_32.lib")

vector<string> split(const string& str, const string& delim) {
    vector<string> res;
    if("" == str) return res;
    //先将要切割的字符串从string类型转换为char*类型
    char * strs = new char[str.length() + 1] ; //不要忘了
    strcpy(strs, str.c_str());

    char * d = new char[delim.length() + 1];
    strcpy(d, delim.c_str());

    char *p = strtok(strs, d);
    while(p) {
        string s = p; //分割得到的字符串转换为string类型
        res.push_back(s); //存入结果数组
        p = strtok(NULL, d);
    }

    return res;
}

int main() {
    // 初始化WSA
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2,2), &wsaData);
    // 创建套接字
    SOCKET slisten = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if(slisten == INVALID_SOCKET){
        printf("Init error\n");
        return 0;
    }

    // 绑定IP和端口

    sockaddr_in sin;
    sin.sin_family = AF_INET;
    sin.sin_port = htons(8888);  // 绑定端口
//    sin.sin_addr.S_un.S_addr = INADDR_ANY;
    sin.sin_addr.S_un.S_addr = inet_addr("127.0.0.1");;
    if(bind(slisten, (LPSOCKADDR)&sin, sizeof(sin)) == SOCKET_ERROR)
    {
//        LPSOCKADDR 就是 sockaddr*
        printf("bind error !");
        closesocket(slisten);
        return 0;
    }
    else
        listen(slisten, 5);
//    开始监听
    SOCKET sClient;

    const char * sendData = "DataReceived!\n";
    int i = 0, n = 10;
//    超过n次连接失败终止程序
    while(true){
        sockaddr_in remoteAddr;
        int nAddrLen = sizeof(remoteAddr);
        char revData[RECVLENGTH];
        printf("\n Waiting for connection......\n");
        sClient = accept(slisten, (SOCKADDR *)&remoteAddr, &nAddrLen);
        if(sClient == INVALID_SOCKET){
            printf("Accept error!\n");
            if(i++ > n)
                break;
            continue;
        }
        printf("One connection detected!\n");
        // 创建供写入的文件
        // 获得时间，根据时间进行文件的创建
        time_t rawTime;
        struct tm *info;
        time(&rawTime);
        info = localtime(&rawTime);
        char* s = asctime(info);
        string curTimeStr = s;
        curTimeStr.replace(curTimeStr.find("\n"), 1 , "");
        curTimeStr.replace(curTimeStr.find(":"), 1, "_");
        curTimeStr.replace(curTimeStr.find(":"), 1, "_");
        vector<string> resStr = split(curTimeStr, " ");
        string outFileName = resStr[4] + "_" + resStr[1] + "_" + resStr[2] + "_" + resStr[3] + ".txt";
        string tmp = getcwd(NULL, 0);
        outFileName = tmp + "\\" + outFileName;
        ofstream outFile;
        outFile.open(outFileName.c_str(), ios::out);
        // 用来保存的文件创建结束，如果创建失败，直接返回
        if(!outFile)
            return -1;

        while(true){

            // 接受数据
            memset(revData, 0, RECVLENGTH); // 将保存缓冲区数据的变量清0
            string tmpRevdata = "";
            int recvLength = 0;
            int fullLength = 0;
            int ret = recv(sClient, revData, RECVLENGTH, 0);
            if(ret <= 0)
                break;
            // 对字符数组最后一位置00，否则转换string出错
            revData[RECVLENGTH] = 0x00;
            // 取得字符数据，进行解析获得有效数据长度和第一段有效数据
            string tmp = revData;
            // 解析字符串得到这条数据的有效数据长度和有效数据
            fullLength = atoi(tmp.substr(0, HEADLENGTH).c_str());
            recvLength += tmp.substr(HEADLENGTH).length();
            // 如果有效数据长度小于RECVLENGTH，那就可以直接下一条了
            if(fullLength < RECVLENGTH)
                continue;
            else{
                tmp = tmp.substr(HEADLENGTH);
                while(recvLength < fullLength){
                    memset(revData, 0, sizeof(revData));
                    // 如果剩下这条数据没有接受的长度大于定义的数组最大长度，那就接受RECVLENGTH这么长，否则接受剩余的长度即可
                    if (fullLength - recvLength > RECVLENGTH)
                        recv(sClient, revData, RECVLENGTH, 0);
                    else
                        recv(sClient, revData, fullLength - recvLength, 0);
                    // 取得数据
                    string t = revData;
                    // 拼接数据
                    tmp += t;
                    // 对当前接受的数据的长度进行累计计数
                    recvLength += ret;
                }
            }
            // 接受一条有效数据完毕，清空状态
            recvLength = 0;
            printf("\n%d\n", tmp.length());
            outFile << tmp << endl;
            tmp = "";
            // 发送数据，表明接受结束
            ret = send(sClient, sendData, strlen(sendData), 0);
            // 发送数据失败
            if(ret < 0)
                break;
        }
        // 文件关闭
        outFile.close();
        closesocket(sClient);
    }
    WSACleanup();
    getchar();
    return 0;
}
