# ui/app.py
import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple

# Configuration
CONFIG = {
    "time_ranges": {
        "Last 1 hour": timedelta(hours=1),
        "Last 24 hours": timedelta(days=1),
        "Last 7 days": timedelta(days=7),
        "All time": None
    },
    "query_types": ["ALL", "SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "OTHER"],
    "duckdb_path": "/tmp/sqlite_analytics.duckdb"
}

def init_connection() -> duckdb.DuckDBPyConnection:
    """Initialize DuckDB connection."""
    @st.cache_resource
    def get_connection():
        return duckdb.connect(CONFIG["duckdb_path"])
    return get_connection()

def setup_page():
    """Configure page settings."""
    st.set_page_config(
        page_title="SQLite Analytics Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("SQLite Analytics Dashboard")

def create_sidebar_filters() -> Tuple[str, str]:
    """Create and handle sidebar filters."""
    st.sidebar.header("Filters")
    
    selected_range = st.sidebar.selectbox(
        "Time Range",
        list(CONFIG["time_ranges"].keys())
    )
    
    selected_type = st.sidebar.selectbox(
        "Query Type",
        CONFIG["query_types"]
    )
    
    return selected_range, selected_type

def build_query(selected_range: str, selected_type: str) -> str:
    """Build the SQL query based on selected filters."""
    base_query = """
        SELECT 
            query,
            timestamp,
            hostname,
            status,
            CASE 
                WHEN query ILIKE 'SELECT%' THEN 'SELECT'
                WHEN query ILIKE 'INSERT%' THEN 'INSERT'
                WHEN query ILIKE 'UPDATE%' THEN 'UPDATE'
                WHEN query ILIKE 'DELETE%' THEN 'DELETE'
                WHEN query ILIKE 'CREATE%' THEN 'CREATE'
                ELSE 'OTHER'
            END as query_type
        FROM sqlite_queries
        WHERE 1=1
    """
    
    if CONFIG["time_ranges"][selected_range]:
        base_query += f" AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '{CONFIG['time_ranges'][selected_range]}'"
    
    if selected_type != "ALL":
        base_query += f" AND query ILIKE '{selected_type}%'"
    
    return base_query

def display_metrics(df: pd.DataFrame):
    """Display key metrics at the top of the dashboard."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Queries", len(df))
    
    with col2:
        if not df.empty:
            avg_queries_per_hour = len(df) / max(1, (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600)
            st.metric("Avg Queries/Hour", f"{avg_queries_per_hour:.1f}")
    
    with col3:
        if not df.empty:
            st.metric("Unique Hosts", df['hostname'].nunique())

def plot_query_distribution(df: pd.DataFrame):
    """Create and display query distribution pie chart."""
    if not df.empty:
        st.subheader("Query Distribution")
        fig = px.pie(df, names='query_type', title="Query Types Distribution")
        st.plotly_chart(fig)

def plot_query_timeline(df: pd.DataFrame):
    """Create and display query timeline."""
    if not df.empty:
        st.subheader("Query Timeline")
        timeline_df = df.set_index('timestamp').resample('1min').size().reset_index()
        timeline_df.columns = ['timestamp', 'count']
        fig = px.line(timeline_df, x='timestamp', y='count', title="Queries per Minute")
        st.plotly_chart(fig)

def display_recent_queries(df: pd.DataFrame):
    """Display recent queries table."""
    st.subheader("Recent Queries")
    if not df.empty:
        st.dataframe(
            df[['timestamp', 'query_type', 'query', 'status', 'hostname']]
            .sort_values('timestamp', ascending=False)
            .head(100)
        )
    else:
        st.info("No queries found for the selected filters")

def display_query_analysis(df: pd.DataFrame):
    """Display detailed query analysis section."""
    if st.checkbox("Show Query Analysis"):
        st.subheader("Query Analysis")
        
        # Most common queries
        st.write("Most Common Queries")
        common_queries = df['query'].value_counts().head(10)
        st.bar_chart(common_queries)
        
        # Performance by host
        st.write("Queries by Host")
        host_dist = df['hostname'].value_counts()
        st.bar_chart(host_dist)

        # Additional analysis features can be added here
        if st.checkbox("Show Advanced Analysis"):
            display_advanced_analysis(df)

def display_advanced_analysis(df: pd.DataFrame):
    """Display advanced analysis features."""
    # Example advanced analysis - can be expanded
    st.write("Query Patterns Over Time")
    hourly_patterns = df.set_index('timestamp').resample('H')['query_type'].value_counts()
    st.line_chart(hourly_patterns)

def main():
    """Main application entry point."""
    # Initialize
    conn = init_connection()
    setup_page()
    
    # Get filters
    selected_range, selected_type = create_sidebar_filters()
    
    # Get data
    query = build_query(selected_range, selected_type)
    df = conn.execute(query).df()
    
    # Display components
    display_metrics(df)
    plot_query_distribution(df)
    plot_query_timeline(df)
    display_recent_queries(df)
    display_query_analysis(df)

if __name__ == "__main__":
    main()