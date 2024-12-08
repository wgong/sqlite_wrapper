# src/cpp/CMakeLists.txt

# Set source files
set(SQLITE_WRAPPER_SOURCES
    src/sqlite_wrapper.cpp
)

# Set header files
set(SQLITE_WRAPPER_HEADERS
    include/sqlite_wrapper.h
)

# Create the library
add_library(sqlite_analytics SHARED
    ${SQLITE_WRAPPER_SOURCES}
    ${SQLITE_WRAPPER_HEADERS}
)

# Include directories
target_include_directories(sqlite_analytics
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${DUCKDB_INCLUDE_DIRS}
        ${SQLite3_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(sqlite_analytics
    PRIVATE
        duckdb
        SQLite::SQLite3
        dl
)

# Create source groups for IDE organization
source_group(
    TREE "${CMAKE_CURRENT_SOURCE_DIR}"
    PREFIX "Source Files"
    FILES ${SQLITE_WRAPPER_SOURCES}
)

source_group(
    TREE "${CMAKE_CURRENT_SOURCE_DIR}"
    PREFIX "Header Files"
    FILES ${SQLITE_WRAPPER_HEADERS}
)