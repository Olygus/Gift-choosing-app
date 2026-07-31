# Giftyfy Calculator

A gift choosing assistant originally created as part of assigment task 3 for enterprise computing made with a C++17 calculator and featuring SQLite3 integration and a python dashboard (streamlit with html and css).

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
   g++ -std=c++17 -O2 -Wall -Wextra -o giftyfy calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```bash
   ./giftyfy
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
   g++ -std=c++17 -O2 -Wall -Wextra -o giftyfy calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```bash
   ./giftyfy
   ```

### Windows (MinGW/MSYS2)
1. Install MinGW-w64 and ensure `g++` is in your Environment PATH.
2. Install or download the SQLite3 amalgamation files (`sqlite3.h` and DLL/lib).
3. Compile the project:
   ```cmd
   g++ -std=c++17 -O2 -Wall -Wextra -o giftyfy.exe calculator.cpp -lsqlite3
   ```
4. Run the application:
   ```cmd
   giftyfy.exe
   ```

## Change Default Admin Credentials and DB Path

If you want to change the default admin login, update these values in `calculator.cpp`:

```cpp
const std::string adminUser = "admin";
const std::string adminPass = "admin123";
```

Replace `"admin"` and `"admin123"` with your preferred username and password, then recompile the app.

The app also contains an SQL fallback/update line for the default admin account in `calculator.cpp` incase it is missing:

```cpp
"UPDATE users_login SET password_ = 'admin123', email_ = 'FarhanIsBest@gmail.com', is_admin = 1 WHERE username_ = 'admin';",
```

Update this SQL string to match your new admin username/password/email, for example:

```cpp
"UPDATE users_login SET password_ = 'yourNewPassword', email_ = 'you@example.com', is_admin = 1 WHERE username_ = 'yourAdminUsername';",
```
or keep it as is for a fallback.

If you are using your own database, the SQL update above ensures the admin row is corrected on startup.

For the Streamlit dashboard, the default DB file location is defined in `app.py`, change it if you want to use an alternate database:

```python
DEFAULT_DB_PATH = Path(__file__).with_name("giftyfy.db")
```

And used in the DB path input field:

```python
value=str(get_db_path()),
help="Defaults to giftyfy.db beside app.py",
```

To use a different default location, set `DEFAULT_DB_PATH` to another path (for example, `Path("/absolute/path/to/giftyfy.db")`), then restart Streamlit.

## Optional: Load Sample Data

If you want a populated with a sanple database to test with, run the sample seeding script before launching the app. This works on Debian/Ubuntu, Arch Linux, and Windows as long as Python 3 is installed:

```bash (Linux based)
python3 db-generate-sample.py giftyfy.db
```

On Windows, use:

```cmd
python db-generate-sample.py giftyfy.db
```

This resets the sample tables and inserts users, profiles, items, and sales data that match the SQLite schema used by the app.

## Run the Streamlit app for dashboard (local)

Prerequisites
- Python 3.8+ installed
- Python environment  
- `streamlit` (install into your virtual environment or system Python):
- `pyinstaller` (optional for linux users, untested for windows)

begin with installing the python libraries 

```bash
pip install streamlit pandas plotly
```

Linux

```bash
# from the folder where you cloned the repository:
cd Gift-choosing-app
#create a venv if needed with 
python3 -m venv .venv
# activate the project's venv if you created one (use activate.fish if your have fish installed):
source .venv/bin/activate
# then run Streamlit
python -m streamlit run app.py

# OR run the venv python directly (useful when your path contains spaces):
"./.venv/bin/python" -m streamlit run app.py
```

```bash
# alternatively you can run the app via pyinstaller (recommended but untested for windows)
pip install pyinstaller
# then in the same directory run
pyinstaller --noconsole --onefile --name dashboard --add-data "app.py:." --add-data "giftyfy.db:." dahsboard.py
# then launch it from the dist folder with 
./dist/dashboard
```


Windows (PowerShell)

```powershell
# from the folder where you cloned the repository:
cd "C:\path\to\Gift-choosing-app"
# activate venv created with `python -m venv .venv`:
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py
```

Windows (Command Prompt)

```cmd
cd "C:\path\to\Gift-choosing-app"
.venv\Scripts\activate.bat
python -m streamlit run app.py
```

Notes
- If you created the virtual environment in a different location, replace the `.venv` path above with your environment's Python executable (quote the path if it contains spaces).
- If you are having trouble using the pyinstaller, it is likely because you need to have your python environment active.
- If you are using WSL, run the Linux commands from the WSL shell.
- To run with the sample data (creates `giftyfy.db`), run the seeding script before launching the app:

```bash
python3 db-generate-sample.py giftyfy.db   # Linux/macOS
```

```bash
python db-generate-sample.py giftyfy.db    # Windows
```
