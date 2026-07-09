cmake_minimum_required(VERSION 3.22.1)

project("watermarker")

add_library(
        watermarker
        SHARED
        native-engine.cpp)

find_library(
        log-lib
        log)

# Add the jnigraphics library for bitmap manipulation
find_library(
        jnigraphics-lib
        jnigraphics)

target_link_libraries(
        watermarker
        ${log-lib}
        ${jnigraphics-lib})
