# tests/cpp/integration/CMakeLists.txt

# Set integration test source files
set(INTEGRATION_TEST_SOURCES
    test_sqlite_ops.cpp
)

# Create integration test executable
add_executable(sqlite_analytics_integration_tests ${INTEGRATION_TEST_SOURCES})

# Include directories
target_include_directories(sqlite_analytics_integration_tests
    PRIVATE
        ${CMAKE_SOURCE_DIR}/src/cpp/include
        ${GTEST_INCLUDE_DIRS}
        ${DUCKDB_INCLUDE_DIRS}
        ${SQLite3_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(sqlite_analytics_integration_tests
    PRIVATE
        sqlite_analytics
        GTest::GTest
        GTest::Main
        duckdb
        SQLite::SQLite3
        dl
)

# Discover and add integration tests
gtest_discover_tests(sqlite_analytics_integration_tests)

# Set test timeouts for integration tests (optional)
set_tests_properties(${INTEGRATION_TEST_SOURCES}
    PROPERTIES
    TIMEOUT 300  # 5-minute timeout for integration tests
)