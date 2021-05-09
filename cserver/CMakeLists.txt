cmake_minimum_required(VERSION 3.19)
project(cserver)

set(CMAKE_CXX_STANDARD 14)
# set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")
add_executable(cserver rpc_server.cpp)
link_libraries(ws2_32)
target_link_libraries(cserver libwsock32.dll)
