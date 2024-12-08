# CMakeLists.txt
cmake_minimum_required(VERSION 3.10)
project(sqlite_analytics)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(DuckDB REQUIRED)
find_package(SQLite3 REQUIRED)

# Add the source subdirectory where the library is defined
add_subdirectory(src/cpp)

# Add tests if testing is enabled
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests/cpp)
endif()

# Installation rules
install(TARGETS sqlite_analytics
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)