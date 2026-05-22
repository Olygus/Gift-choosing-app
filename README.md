# Giftify Calculator

A gift choosing assistant originally created as part of assigment task 3 for enterprise computing made with a C++17 calculator and featuring SQLite3 integration.

## Compilation Instructions

Ensure you have a C++17 compliant compiler and the SQLite3 development libraries installed on your system.

### Start Here
1. Clone my repositorywith
   ```bash
   git clone https://github.com/Olygus/Gift-choosing-app
   ```
2. go into the project folder:
   ```bash
   cd Path-to-download-location/Gift-choosing-app
   ```

### Linux (Ubuntu/Debian)
1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install g++ libsqlite3-dev
   ```
2. Navigate to the app folder:
   ```bash
   cd ~/location-installed
   ```
3. Compile the project:
   ```bash
   g++ -std=c++17 -O2 -Wall -Wextra -o giftify calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```bash
   ./giftify
   ```
### Arch Linux Setup & Compilation

1. Install the GNU Compiler Collection (GCC) and SQLite package:
   ```bash
   sudo pacman -Syu base-devel sqlite
   ```
   *(Note: Arch includes development headers directly in the core package, so no separate `-dev` package is needed).*

2. Navigate to the app folder:
   ```bash
   cd ~/location-installed
   ```
3. Compile the project:
   ```bash
   g++ -std=c++17 -O2 -Wall -Wextra -o giftify calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```bash
   ./giftify
   ```

### Windows (MinGW/MSYS2)
1. Install MinGW-w64 and ensure `g++` is in your Environment PATH.
2. Install or download the SQLite3 amalgamation files (`sqlite3.h` and DLL/lib).
3. Compile the project:
   ```cmd
   g++ -std=c++17 -O2 -Wall -Wextra -o giftify.exe calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```cmd
   giftify.exe
   ```

## Optional: Load Sample Data

If you want a populated with a sanple database to test with, run the sample seeding script before launching the app. This works on Debian/Ubuntu, Arch Linux, and Windows as long as Python 3 is installed:

```bash (Linux based)
python3 db-generate-sample.py giftify.db
```

On Windows, use:

```cmd
python db-generate-sample.py giftify.db
```

This resets the sample tables and inserts users, profiles, items, and sales data that match the SQLite schema used by the app.
