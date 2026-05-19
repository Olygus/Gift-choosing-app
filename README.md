
# Giftify Calculator

A gift choosing assistant originally created as part of assigment task 3 for enterprise computing made with a C++17 calculator and featuring SQLite3 integration.

## Compilation Instructions

Ensure you have a C++17 compliant compiler and the SQLite3 development libraries installed on your system.

### Linux (Ubuntu/Debian)
1. Install dependencies:
   ```bash
   sudo apt update && sudo apt install g++ libsqlite3-dev
   ```
2. Compile the project:
   ```bash
   g++ -std=c++17 -O2 -Wall -Wextra -o giftify calculator.cpp -lsqlite3
   ```
3. Run the application:
   ```bash
   ./giftify
   ```
### Arch Linux Setup & Compilation

1. Install the GNU Compiler Collection (GCC) and SQLite package:
   ```bash
   sudo pacman -Syu base-devel sqlite
   ```
   *(Note: Arch includes development headers directly in the core package, so no separate `-dev` package is needed).*

2. Compile the project:
   ```bash
   g++ -std=c++17 -O2 -Wall -Wextra -o giftify calculator.cpp -lsqlite3
   ```

3. Run the application:
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
