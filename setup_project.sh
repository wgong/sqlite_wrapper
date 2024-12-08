#!/bin/bash

# Create main project directory
PROJECT_ROOT="."
echo "Creating project structure in $PROJECT_ROOT..."

# Create directory structure and empty files
touch "$PROJECT_ROOT"/README.md
touch "$PROJECT_ROOT"/requirements.txt
touch "$PROJECT_ROOT"/CMakeLists.txt

mkdir -p "$PROJECT_ROOT"/deps/sqlite

mkdir -p "$PROJECT_ROOT"/src/cpp/include
touch "$PROJECT_ROOT"/src/cpp/include/sqlite_wrapper.h

mkdir -p "$PROJECT_ROOT"/src/cpp/src
touch "$PROJECT_ROOT"/src/cpp/src/sqlite_wrapper.cpp

mkdir -p "$PROJECT_ROOT"/src/python/sqlite
touch "$PROJECT_ROOT"/src/python/sqlite/__init__.py
touch "$PROJECT_ROOT"/src/python/sqlite/wrapper.py
touch "$PROJECT_ROOT"/src/python/setup.py


mkdir -p "$PROJECT_ROOT"/tests/cpp/integration
mkdir -p "$PROJECT_ROOT"/tests/cpp/unit
touch "$PROJECT_ROOT"/tests/cpp/integration/test_sqlite.cpp
touch "$PROJECT_ROOT"/tests/cpp/unit/test_wrapper.cpp

mkdir -p "$PROJECT_ROOT"/tests/python/integration
mkdir -p "$PROJECT_ROOT"/tests/python/unit
touch "$PROJECT_ROOT"/tests/python/integration/test_sqlite.py
touch "$PROJECT_ROOT"/tests/python/unit/test_wrapper.py


mkdir -p "$PROJECT_ROOT"/ui/static
touch "$PROJECT_ROOT"/ui/app.py
touch "$PROJECT_ROOT"/ui/requirements.txt
touch "$PROJECT_ROOT"/ui/static/style.css

mkdir -p "$PROJECT_ROOT"/scripts
touch "$PROJECT_ROOT"/scripts/setup_deps.sh
touch "$PROJECT_ROOT"/scripts/build.sh
touch "$PROJECT_ROOT"/scripts/test.sh

# Create scripts directory
cat > "$PROJECT_ROOT"/scripts/build.sh << 'EOF'
#!/bin/bash
mkdir -p build
cd build
cmake ..
make
cd ../src/python
pip install -e .
EOF

cat > "$PROJECT_ROOT"/scripts/test.sh << 'EOF'
#!/bin/bash
cd build
ctest --output-on-failure
cd ../tests/python
python -m pytest
EOF

# Make scripts executable
chmod +x "$PROJECT_ROOT"/scripts/build.sh
chmod +x "$PROJECT_ROOT"/scripts/test.sh

# Initialize git repository
cd "$PROJECT_ROOT"
git init

# Create .gitignore
cat > .gitignore << 'EOF'
# Build directories
build/
dist/
*.egg-info/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# DuckDB
*.duckdb
*.duckdb.wal

# SQLite
*.db
*.sqlite
*.sqlite3
EOF

echo "Project structure created successfully!"
echo "Next steps:"
echo "1. Clone SQLite: git submodule add https://github.com/sqlite/sqlite.git deps/sqlite"
echo "2. Install DuckDB development headers: sudo apt-get install libduckdb-dev"
echo "3. Build the project: ./scripts/build.sh"