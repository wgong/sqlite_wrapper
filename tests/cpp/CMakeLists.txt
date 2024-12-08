# tests/cpp/CMakeLists.txt

# Find GTest package
find_package(GTest REQUIRED)
include(GoogleTest)

# Set test source files
set(TEST_SOURCES
    unit/test_wrapper.cpp
    integration/test_sqlite_ops.cpp
)

# Create test executable
add_executable(sqlite_analytics_tests ${TEST_SOURCES})

# Include directories
target_include_directories(sqlite_analytics_tests
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/cpp/include
        ${GTEST_INCLUDE_DIRS}
        ${DUCKDB_INCLUDE_DIRS}
        ${SQLite3_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(sqlite_analytics_tests
    PRIVATE
        sqlite_analytics
        GTest::GTest
        GTest::Main
        duckdb
        SQLite::SQLite3
        dl
)

# Discover and add tests
gtest_discover_tests(sqlite_analytics_tests)

# Optional: Copy test data files if needed
# file(COPY ${CMAKE_CURRENT_SOURCE_DIR}/data DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

# Set test properties
set_target_properties(sqlite_analytics_tests
    PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/tests"
)