import sqlite3
import duckdb
import hashlib
import socket
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import pandas as pd

class SQLiteWrapper:
    def __init__(self, duckdb_path: str = ":memory:"):
        """Initialize the SQL interceptor with DuckDB storage"""
        self.duckdb_conn = duckdb.connect(duckdb_path)
        self._setup_storage()
        self.local_data = threading.local()

    def _setup_storage(self):
        """Create the sql_info table in DuckDB"""
        self.duckdb_conn.execute("""
            CREATE TABLE IF NOT EXISTS sql_info (
                id INTEGER PRIMARY KEY,
                raw_sql_stmt TEXT,
                sql_stmt_hash VARCHAR(64),
                sql_stmt TEXT,
                param_values ARRAY(VARCHAR),
                timestamp TIMESTAMP,
                caller_name VARCHAR(255),
                caller_ip VARCHAR(45),
                source VARCHAR(50)  -- Added to track if query came from cursor or pandas
            )
        """)

    def _get_caller_info(self) -> tuple[str, str]:
        """Get caller name and IP address"""
        caller_name = socket.gethostname()
        try:
            caller_ip = socket.gethostbyname(caller_name)
        except:
            caller_ip = "127.0.0.1"
        return caller_name, caller_ip

    def _compute_hash(self, sql: str) -> str:
        """Compute hash of normalized SQL statement"""
        return hashlib.sha256(sql.encode()).hexdigest()

    def _format_param_value(self, value: Any) -> str:
        """Convert parameter value to string representation"""
        if value is None:
            return 'NULL'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (datetime, str)):
            return f"'{str(value)}'"
        elif isinstance(value, (list, tuple)):
            return f"ARRAY{str(value)}"
        return str(value)

    def connect(self, database: str, **kwargs) -> 'WrappedConnection':
        """Create a wrapped SQLite connection"""
        sqlite_conn = sqlite3.connect(database, **kwargs)
        return WrappedConnection(sqlite_conn, self)

    def log_query(self, sql: str, parameters: Optional[Union[tuple, dict]] = None, source: str = "cursor"):
        """Log SQL query to DuckDB"""
        caller_name, caller_ip = self._get_caller_info()
        sql_hash = self._compute_hash(sql)

        # Convert parameters to string values
        param_values = []
        if parameters:
            if isinstance(parameters, dict):
                param_values = [self._format_param_value(v) for v in parameters.values()]
            else:
                param_values = [self._format_param_value(v) for v in parameters]

        self.duckdb_conn.execute("""
            INSERT INTO sql_info (
                raw_sql_stmt, sql_stmt_hash, sql_stmt, param_values,
                timestamp, caller_name, caller_ip, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sql,
            sql_hash,
            sql,
            param_values,
            datetime.now(),
            caller_name,
            caller_ip,
            source
        ))

    def query_history(self, conditions: str = "") -> List[Dict]:
        """Query the stored SQL information"""
        query = "SELECT * FROM sql_info"
        if conditions:
            query += f" WHERE {conditions}"
        query += " ORDER BY timestamp DESC"
        
        results = self.duckdb_conn.execute(query).fetchall()
        columns = [desc[0] for desc in self.duckdb_conn.description]
        
        return [dict(zip(columns, row)) for row in results]

class WrappedConnection:
    def __init__(self, connection: sqlite3.Connection, wrapper: SQLiteWrapper):
        self._connection = connection
        self._wrapper = wrapper
        # Store original methods we need to wrap
        self._orig_execute = connection.execute
        self._orig_executemany = connection.executemany
        # Replace connection methods with our wrapped versions
        connection.execute = self.execute
        connection.executemany = self.executemany

    def cursor(self) -> 'WrappedCursor':
        """Create a wrapped cursor"""
        return WrappedCursor(self._connection.cursor(), self._wrapper)

    def execute(self, sql: str, parameters: Optional[Union[tuple, dict]] = None) -> sqlite3.Cursor:
        """Execute a SQL query and log it (used by pandas)"""
        try:
            self._wrapper.log_query(sql, parameters, source="pandas")
            # Use stored original method to avoid recursion
            return self._orig_execute(sql, parameters if parameters is not None else ())
        except Exception as e:
            # Log the error but don't interfere with normal error handling
            print(f"Error in wrapped execute: {e}")
            raise

    def executemany(self, sql: str, parameters: List[Union[tuple, dict]]) -> sqlite3.Cursor:
        """Execute many SQL queries and log them (used by pandas)"""
        try:
            # For executemany, we'll log once with the first set of parameters
            if parameters:
                self._wrapper.log_query(sql, parameters[0], source="pandas_bulk")
            # Use stored original method to avoid recursion
            return self._orig_executemany(sql, parameters)
        except Exception as e:
            print(f"Error in wrapped executemany: {e}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._connection.close()

    def __getattr__(self, name):
        """Delegate all other attributes to the underlying connection"""
        return getattr(self._connection, name)

class WrappedCursor:
    def __init__(self, cursor: sqlite3.Cursor, wrapper: SQLiteWrapper):
        self._cursor = cursor
        self._wrapper = wrapper

    def execute(self, sql: str, parameters: Optional[Union[tuple, dict]] = None) -> 'WrappedCursor':
        """Execute a SQL query and log it"""
        self._wrapper.log_query(sql, parameters, source="cursor")
        if parameters is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, parameters)
        return self

    def executemany(self, sql: str, parameters: List[Union[tuple, dict]]) -> 'WrappedCursor':
        """Execute many SQL queries and log them"""
        for params in parameters:
            self._wrapper.log_query(sql, params, source="cursor")
        self._cursor.executemany(sql, parameters)
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

    def __getattr__(self, name):
        """Delegate all other attributes to the underlying cursor"""
        return getattr(self._cursor, name)

# Usage Example
if __name__ == "__main__":
    import pandas as pd
    
    # Test pandas to_sql functionality
    df = pd.DataFrame({
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35]
    })
    # Initialize wrapper and create an in-memory database
    wrapper = SQLiteWrapper("sql_logs.duckdb")
    
    print("Testing pandas to_sql...")
    with wrapper.connect(":memory:") as conn:
        # Write DataFrame to SQL
        df.to_sql('test_table', conn, index=False)
        
        # Read it back
        df_read = pd.read_sql("SELECT * FROM test_table", conn)
        print("Data read back:", df_read)
        
        # Check the logged queries
        print("\nLogged queries:")
        for query in wrapper.query_history():
            print(f"SQL: {query['sql_stmt']}")
            print(f"Source: {query['source']}")
            print(f"Time: {query['timestamp']}")
            print("-" * 50)
    
    # Use wrapped connection
    with wrapper.connect("example.db") as conn:
        # Create table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        """)
        
        # Insert using cursor
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("John Doe", "john@example.com")
        )
        
        # Using pandas to read data
        df = pd.read_sql("SELECT * FROM users", conn)
        print("Read using pandas:", df)
        
        # Using pandas to write data
        new_users = pd.DataFrame([
            {"name": "Jane Doe", "email": "jane@example.com"},
            {"name": "Bob Smith", "email": "bob@example.com"}
        ])
        new_users.to_sql("users", conn, if_exists="append", index=False)
        
        # Check query history
        recent_queries = wrapper.query_history()
        print("\nRecent queries:")
        for query in recent_queries:
            print(f"SQL: {query['sql_stmt']}")
            print(f"Parameters: {query['param_values']}")
            print(f"Source: {query['source']}")  # Will show if query came from cursor or pandas
            print(f"Timestamp: {query['timestamp']}")
            print("-" * 80)