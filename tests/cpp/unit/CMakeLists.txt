# tests/cpp/unit/CMakeLists.txt

# Set unit test source files
set(UNIT_TEST_SOURCES
    test_wrapper.cpp
)

# Create unit test executable
add_executable(sqlite_analytics_unit_tests ${UNIT_TEST_SOURCES})

# Include directories
target_include_directories(sqlite_analytics_unit_tests
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/cpp/include
        ${GTEST_INCLUDE_DIRS}
        ${DUCKDB_INCLUDE_DIRS}
        ${SQLite3_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(sqlite_analytics_unit_tests
    PRIVATE
        sqlite_analytics
        GTest::GTest
        GTest::Main
        duckdb
        SQLite::SQLite3
        dl
)

# Discover and add unit tests
gtest_discover_tests(sqlite_analytics_unit_tests)