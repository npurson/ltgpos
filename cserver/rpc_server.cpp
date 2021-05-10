#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <Winsock2.h>

#pragma comment(lib, "ws2_32.lib")


int main(int argc, char* argv[])
{
    assert(argc == 2);
    char* addr = argv[0];
    int port = atoi(argv[1]);

    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
    }
    sockaddr_in sock_addr;
    sock_addr.sin_family = AF_INET;
    sock_addr.sin_addr.s_addr = inet_addr(addr);
    sock_addr.sin_port = htons(port);

    if (bind(sock, (sockaddr*)&sock_addr, sizeof(sock_addr))) {
        printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
    }
    listen(sock, 5);

    #define BUFSIZE 16384
    char buf[BUFSIZE];
    while (1) {
        sockaddr_in conn_addr;
        int addrlen = sizeof(conn_addr);
        SOCKET conn = accept(sock, (sockaddr*)&conn_addr, &addrlen);
        if (conn == INVALID_SOCKET) {
            printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
        }

        while (1) {
            int recv_size = recv(conn, buf, BUFSIZE, 0);
            buf[recv_size] = 0;
            char header[6] = { 0 };
            strncpy(header, buf, 5);
            int packlen = atoi(header);

            if (packlen > 0) {              // header > 0: calls ltgpos and return the result.
                if (packlen > BUFSIZE) {
                    // TODO concat receive string or drop the rest?
                    char* ret_str = "test";
                    send(conn, ret_str, strlen(ret_str), 0);
                    continue;
                } else if (recv_size - 5 < packlen) {       // Incomplete packet.
                    int total_size = recv_size;
                    while (1) {
                        total_size += recv(conn, buf + total_size, BUFSIZE - total_size, 0);
                        if (total_size - 5 == packlen) {
                            buf[total_size] = 0;
                            break;
                        }
                    }
                }
                char* ret_str = "test";
                send(conn, ret_str, strlen(ret_str), 0);
                // TODO send exception
            } else if (packlen == -1) {     // header == -1: closes socket.
                closesocket(conn);
                break;
            } else if (packlen == -2) {     // header == -2: closes server.
                closesocket(conn);
                goto l1;
            }
        }
    }

l1:
    closesocket(sock);
    WSACleanup();
    return 0;
}
