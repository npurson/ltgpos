cmake_minimum_required(VERSION 3.19)
project(wrapper)

add_library(wrapper STATIC wrapper.cpp)
target_include_directories(wrapper PRIVATE libs/onnxruntime/include)
target_link_libraries(wrapper libs/onnxruntime/lib)
