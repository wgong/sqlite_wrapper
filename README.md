# SQLite Wrapper

Capture SQL statement for SQLite

## Add SQLite as submodule
```
cd deps
git submodule add https://github.com/sqlite/sqlite.git sqlite
git submodule update --init --recursive
```

## Build
```
mkdir build
cd build
cmake ..
make
```