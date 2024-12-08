// test_sqlite_analytics.cpp
#include <sqlite3.h>
#include <iostream>
#include <string>

int main() {
    sqlite3* db;
    char* err_msg = nullptr;
    
    // Open database
    int rc = sqlite3_open(":memory:", &db);
    if (rc != SQLITE_OK) {
        std::cerr << "Failed to open database: " << sqlite3_errmsg(db) << std::endl;
        return 1;
    }
    
    // Create table
    const char* create_sql = "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)";
    rc = sqlite3_exec(db, create_sql, nullptr, nullptr, &err_msg);
    if (rc != SQLITE_OK) {
        std::cerr << "Failed to create table: " << err_msg << std::endl;
        sqlite3_free(err_msg);
        return 1;
    }
    
    // Insert data
    const char* insert_sql = "INSERT INTO users (name) VALUES ('Alice'), ('Bob')";
    rc = sqlite3_exec(db, insert_sql, nullptr, nullptr, &err_msg);
    if (rc != SQLITE_OK) {
        std::cerr << "Failed to insert data: " << err_msg << std::endl;
        sqlite3_free(err_msg);
        return 1;
    }
    
    // Query data
    sqlite3_stmt* stmt;
    const char* select_sql = "SELECT * FROM users";
    rc = sqlite3_prepare_v2(db, select_sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) {
        std::cerr << "Failed to prepare statement: " << sqlite3_errmsg(db) << std::endl;
        return 1;
    }
    
    // Print results
    std::cout << "Users in database:\n";
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        int id = sqlite3_column_int(stmt, 0);
        const char* name = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
        std::cout << id << ": " << name << std::endl;
    }
    
    sqlite3_finalize(stmt);
    sqlite3_close(db);
    return 0;
}