cmake_minimum_required(VERSION 3.16)
project(ZeladorDoVacuo CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# -- SDL2 --
find_package(SDL2 REQUIRED)

# SDL2_ttf -- suporta tanto o modulo moderno quanto busca manual
find_library(SDL2_TTF_LIB NAMES SDL2_ttf REQUIRED)
find_path(SDL2_TTF_INCLUDE NAMES SDL_ttf.h PATH_SUFFIXES SDL2)

add_library(SDL2_ttf UNKNOWN IMPORTED)
set_target_properties(SDL2_ttf PROPERTIES
    IMPORTED_LOCATION "${SDL2_TTF_LIB}"
    INTERFACE_INCLUDE_DIRECTORIES "${SDL2_TTF_INCLUDE}"
)

# -- Fontes --
set(SOURCES
    src/main.cpp
    src/managers/GameManager.cpp
    src/managers/SanityManager.cpp
    src/managers/DayManager.cpp
    src/managers/MaintenanceManager.cpp
    src/systems/RadioSystem.cpp
    src/systems/RadarSystem.cpp
)

add_executable(ZeladorDoVacuo ${SOURCES})

target_include_directories(ZeladorDoVacuo PRIVATE include)

target_link_libraries(ZeladorDoVacuo PRIVATE
    SDL2::SDL2main
    SDL2::SDL2
    SDL2_ttf
)

# Windows: copiar DLLs para pasta do exe
if(WIN32)
    add_custom_command(TARGET ZeladorDoVacuo POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:SDL2::SDL2>
            $<TARGET_FILE:SDL2_ttf>
            $<TARGET_FILE_DIR:ZeladorDoVacuo>
    )
endif()

# Copiar assets para pasta de build
add_custom_command(TARGET ZeladorDoVacuo POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        "${CMAKE_SOURCE_DIR}/assets"
        "$<TARGET_FILE_DIR:ZeladorDoVacuo>/assets"
)
