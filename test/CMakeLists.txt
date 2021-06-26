cmake_minimum_required(VERSION 3.17)
project(rpc_server)

set(CMAKE_CXX_STANDARD 14)
add_executable(rpc_server rpc_server.cpp)
link_libraries(ws2_32)
target_link_libraries(rpc_server libwsock32.dll)
