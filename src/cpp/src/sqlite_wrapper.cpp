#include <sqlite3.h>
#include <duckdb.hpp>
#include <memory>
#include <string>
#include <cstring>
#include <ctime>
#include <mutex>
#include <thread>
#include <unistd.h>
#include <sys/socket.h>
#include <netdb.h>
#include <dlfcn.h>
#include <sstream>

// Global DuckDB connection for logging
std::unique_ptr<duckdb::DuckDB> g_duckdb;
std::unique_ptr<duckdb::Connection> g_duckdb_conn;
std::mutex g_duckdb_mutex;

// Function pointer types for original SQLite functions
typedef int (*sqlite3_prepare_v2_fn)(
    sqlite3*,            /* Database handle */
    const char*,        /* SQL statement, UTF-8 encoded */
    int,               /* Maximum length of zSql in bytes */
    sqlite3_stmt**,    /* OUT: Statement handle */
    const char**       /* OUT: Pointer to unused portion of zSql */
);

typedef int (*sqlite3_step_fn)(sqlite3_stmt*);
typedef int (*sqlite3_finalize_fn)(sqlite3_stmt*);

// Store original function pointers
sqlite3_prepare_v2_fn original_prepare_v2 = nullptr;
sqlite3_step_fn original_step = nullptr;
sqlite3_finalize_fn original_finalize = nullptr;

// Helper function to get hostname and IP
std::pair<std::string, std::string> get_caller_info() {
    char hostname[1024];
    gethostname(hostname, sizeof(hostname));
    
    struct hostent *host_entry = gethostbyname(hostname);
    std::string ip = "127.0.0.1";
    if (host_entry != nullptr) {
        ip = inet_ntoa(*((struct in_addr*)host_entry->h_addr_list[0]));
    }
    
    return {hostname, ip};
}

// Initialize DuckDB logging
void init_duckdb_logging(const char* path = ":memory:") {
    try {
        g_duckdb = std::make_unique<duckdb::DuckDB>(path);
        g_duckdb_conn = std::make_unique<duckdb::Connection>(*g_duckdb);
        
        // Create logging table
        g_duckdb_conn->Query(R"(
            CREATE TABLE IF NOT EXISTS sqlite_queries (
                id INTEGER PRIMARY KEY,
                query TEXT,
                timestamp TIMESTAMP,
                hostname VARCHAR,
                ip VARCHAR,
                thread_id INTEGER,
                status VARCHAR
            )
        )");
    } catch (const std::exception& e) {
        fprintf(stderr, "Failed to initialize DuckDB: %s\n", e.what());
    }
}

// Log query to DuckDB
void log_query(const char* sql, const char* status) {
    std::lock_guard<std::mutex> lock(g_duckdb_mutex);
    
    try {
        auto [hostname, ip] = get_caller_info();
        auto thread_id = std::this_thread::get_id();
        
        std::stringstream ss;
        ss << thread_id;
        
        g_duckdb_conn->Query(R"(
            INSERT INTO sqlite_queries (query, timestamp, hostname, ip, thread_id, status)
            VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?)
        )", sql, hostname, ip, ss.str(), status);
    } catch (const std::exception& e) {
        fprintf(stderr, "Failed to log query: %s\n", e.what());
    }
}

// Wrapped SQLite prepare_v2
extern "C" int sqlite3_prepare_v2(
    sqlite3* db,
    const char* zSql,
    int nByte,
    sqlite3_stmt** ppStmt,
    const char** pzTail
) {
    // Log the SQL query
    log_query(zSql, "prepared");
    
    // Call original function
    return original_prepare_v2(db, zSql, nByte, ppStmt, pzTail);
}

// Wrapped SQLite step
extern "C" int sqlite3_step(sqlite3_stmt* stmt) {
    int result = original_step(stmt);
    
    // Log execution status
    const char* sql = sqlite3_sql(stmt);
    if (sql) {
        log_query(sql, (result == SQLITE_DONE) ? "completed" : "executing");
    }
    
    return result;
}

// Wrapped SQLite finalize
extern "C" int sqlite3_finalize(sqlite3_stmt* stmt) {
    const char* sql = sqlite3_sql(stmt);
    if (sql) {
        log_query(sql, "finalized");
    }
    
    return original_finalize(stmt);
}

// Initialize function hooking
__attribute__((constructor))
static void init() {
    // Initialize DuckDB logging
    init_duckdb_logging("/tmp/sqlite_analytics.duckdb");
    
    // Get handle to the real SQLite library
    void* sqlite_handle = dlopen("libsqlite3.so", RTLD_LAZY);
    if (!sqlite_handle) {
        fprintf(stderr, "Failed to load SQLite library: %s\n", dlerror());
        return;
    }
    
    // Store original function pointers
    original_prepare_v2 = (sqlite3_prepare_v2_fn)dlsym(sqlite_handle, "sqlite3_prepare_v2");
    original_step = (sqlite3_step_fn)dlsym(sqlite_handle, "sqlite3_step");
    original_finalize = (sqlite3_finalize_fn)dlsym(sqlite_handle, "sqlite3_finalize");
    
    if (!original_prepare_v2 || !original_step || !original_finalize) {
        fprintf(stderr, "Failed to get SQLite function pointers\n");
        return;
    }
}