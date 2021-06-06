#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <Winsock2.h>

#define HEADERLEN   4
#define BUFSIZE     8192

#pragma comment(lib, "ws2_32.lib")


int main(int argc, char* argv[])
{
    assert(argc == 2);
    int port = atoi(argv[1]);
    // int port = 8888;

    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sock == INVALID_SOCKET) {
        printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
    }

    sockaddr_in sock_addr;
    sock_addr.sin_family = AF_INET;
    sock_addr.sin_addr.s_addr = INADDR_ANY;
    sock_addr.sin_port = htons(port);

    if (bind(sock, (sockaddr*)&sock_addr, sizeof(sock_addr))) {
        printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
    }
    printf("Listening...\n");
    listen(sock, 5);

    char buf[BUFSIZE + 1];
    // Wating for connections.
    while (1) {
        sockaddr_in conn_addr;
        int addrlen = sizeof(conn_addr);
        SOCKET conn = accept(sock, (sockaddr*)&conn_addr, &addrlen);

        if (conn == INVALID_SOCKET) {
            printf("%s(%d): %d", __FILE__, __LINE__, WSAGetLastError());
        }
        printf("Connected.\n");

        // Wating for packets.
        while (1) {
            int recv_size = recv(conn, buf, BUFSIZE, 0);
            if (!recv_size) {       // Remote socket closed.
                printf("Connection broken.\n");
                break;
            }
            char header[HEADERLEN + 1] = { 0 };
            strncpy(header, buf, HEADERLEN);
            int packlen = atoi(header);

            if (packlen > 0) {                  // header > 0: calls ltgpos and return the result.
                // if (packlen > BUFSIZE)       // This may not happen now.
                int total_size = recv_size;
                while (total_size - HEADERLEN != packlen) {     // Incomplete packet.
                    total_size += recv(conn, buf + total_size, BUFSIZE - total_size, 0);
                }
                buf[total_size] = 0;
                printf("Packet received.\n");
                char* output = "{\"date_time\":\"2021-05-10 12:35:59\",\"time\":232.55284268356445,\"latitude\":29.401820998079458,\"longitude\":111.85898095548136,\"altitude\":0,\"goodness\":1.8526270500081734,\"current\":82.210809098043072}";
                send(conn, output, strlen(output), 0);
                // TODO send exception
            } else if (packlen == -1) {         // header == -1: closes socket.
                closesocket(conn);
                break;
            } else if (packlen == -2) {         // header == -2: closes server.
                closesocket(conn);
                // goto l1;
                break;
            }
        }
    }

l1:
    closesocket(sock);
    WSACleanup();
    return 0;
}
