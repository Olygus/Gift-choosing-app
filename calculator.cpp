#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <algorithm>
#include <cctype>
#include <memory>
#include <sqlite3.h>
#include <cmath>
#include <iomanip>
#include <sstream>

// Platform-specific includes
#ifdef _WIN32
    #include <conio.h>
    #include <windows.h>
#else
    #include <termios.h>
    #include <unistd.h>
    #include <sys/ioctl.h>
#endif

const int NUM_CATEGORIES = 41;
const int TOP_N_ITEMS = 10;


const std::string DB_PATH = "giftyfy.db";

using SqliteDbPtr = std::unique_ptr<sqlite3, decltype(&sqlite3_close)>;
using SqliteStmtPtr = std::unique_ptr<sqlite3_stmt, decltype(&sqlite3_finalize)>;

bool tableHasColumn(sqlite3* db, const std::string& table, const std::string& column);
bool ensureDatabaseCompatibility(sqlite3* db);
struct UserAccount;
void runAdminConsole(const UserAccount& user);

// Cross-platform key input function
char getch_cross() {
    #ifdef _WIN32
        return _getch();
    #else
        struct termios oldt, newt;
        char ch;
        tcgetattr(STDIN_FILENO, &oldt);
        newt = oldt;
        newt.c_lflag &= ~(ICANON | ECHO);
        tcsetattr(STDIN_FILENO, TCSANOW, &newt);
        ch = getchar();
        tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
        return ch;
    #endif
}

// ANSI color helpers (24-bit)
std::string esc_fg(int r, int g, int b) {
    std::ostringstream ss;
    ss << "\033[38;2;" << r << ";" << g << ";" << b << "m";
    return ss.str();
}

std::string esc_bg(int r, int g, int b) {
    std::ostringstream ss;
    ss << "\033[48;2;" << r << ";" << g << ";" << b << "m";
    return ss.str();
}

std::string esc_bold() {
    return "\033[1m";
}

std::string esc_reset() {
    return "\033[0m";
}

// removed global bg because it locked ugly
// set terminal background color for the whole session (attempt)
void setTerminalBackground(int r, int g, int b) {
    std::string bg = esc_bg(r, g, b);
    // Set background color and clear screen
    std::cout << bg << "\033[2J\033[H" << std::flush;
}

std::string readMaskedInput(const std::string& prompt) {
    std::string input;
    std::cout << prompt << ": ";

    while (true) {
        char ch = getch_cross();

        if (ch == 10 || ch == 13) {
            std::cout << std::endl;
            break;
        }

        if (ch == 8 || ch == 127) {
            if (!input.empty()) {
                input.pop_back();
                std::cout << "\b \b" << std::flush;
            }
            continue;
        }

        if (std::isprint(static_cast<unsigned char>(ch))) {
            input.push_back(ch);
            std::cout << '*' << std::flush;
        }
    }

    return input;
}

void clearScreen() {
    #ifdef _WIN32
        system("cls");
    #else
        std::cout << "\033[3J\033[2J\033[H" << std::flush;
    #endif
}

void printDivider() {
    std::cout << "========================================" << std::endl;
}

std::string getSqliteText(sqlite3_stmt* stmt, int column) {
    const unsigned char* text = sqlite3_column_text(stmt, column);
    return text ? reinterpret_cast<const char*>(text) : "";
}

std::string normalizeConsoleText(std::string text) {
    for (char& ch : text) {
        if (ch == '\n' || ch == '\r' || ch == '\t') {
            ch = ' ';
        }
    }

    while (!text.empty() && std::isspace(static_cast<unsigned char>(text.front()))) {
        text.erase(text.begin());
    }

    while (!text.empty() && std::isspace(static_cast<unsigned char>(text.back()))) {
        text.pop_back();
    }

    return text;
}

std::string truncateConsoleText(const std::string& text, std::size_t max_width) {
    if (text.size() <= max_width) {
        return text;
    }

    if (max_width <= 3) {
        return text.substr(0, max_width);
    }

    return text.substr(0, max_width - 1) + "…";
}

std::string padConsoleText(const std::string& text, std::size_t width, bool align_right = false) {
    std::ostringstream stream;
    stream << (align_right ? std::right : std::left)
           << std::setw(static_cast<int>(width))
           << truncateConsoleText(normalizeConsoleText(text), width);
    return stream.str();
}

void renderCompactQueryTable(const std::string& title,
                             const std::vector<std::string>& column_names,
                             const std::vector<std::vector<std::string>>& rows,
                             std::size_t start_row,
                             std::size_t end_row,
                             std::size_t page_number,
                             std::size_t total_pages) {
    const std::string title_color = esc_fg(80, 220, 255);
    const std::string header_color = esc_fg(255, 255, 255) + esc_bg(0, 110, 140) + esc_bold();
    const std::string label_color = esc_fg(255, 215, 0) + esc_bold();
    const std::string value_color = esc_fg(230, 230, 230);
    const std::string row_even_color = esc_bg(24, 24, 28);
    const std::string row_odd_color = esc_bg(14, 14, 18);
    const std::string border_color = esc_fg(90, 90, 100);

    auto divider = [&]() {
        std::cout << border_color << "========================================" << esc_reset() << std::endl;
    };

    divider();
    std::cout << title_color << esc_bold() << title << esc_reset();
    if (total_pages > 1) {
        std::cout << ' ' << esc_fg(180, 180, 180)
                  << "(Page " << page_number << " / " << total_pages << ")"
                  << esc_reset();
    }
    std::cout << std::endl;
    divider();

    if (rows.empty() || start_row >= end_row) {
        std::cout << esc_fg(180, 180, 180) << "No records found." << esc_reset() << std::endl;
        return;
    }

    bool use_vertical_layout = column_names.size() > 8;

    if (use_vertical_layout) {
        std::size_t label_width = 0;
        for (const std::string& name : column_names) {
            label_width = std::max(label_width, normalizeConsoleText(name).size());
        }
        label_width = std::min<std::size_t>(label_width, 28);

        for (std::size_t row_index = start_row; row_index < end_row; ++row_index) {
            std::size_t page_row_number = row_index - start_row + 1;
            const std::string& row_bg = (row_index % 2 == 0) ? row_even_color : row_odd_color;
            std::cout << row_bg << label_color << " Row " << page_row_number << " " << esc_reset() << std::endl;

            for (std::size_t column_index = 0; column_index < column_names.size(); ++column_index) {
                std::string label = padConsoleText(column_names[column_index], label_width);
                std::string value = column_index < rows[row_index].size() ? rows[row_index][column_index] : "";
                value = normalizeConsoleText(value);
                if (value.size() > 180) {
                    value = truncateConsoleText(value, 180);
                }

                std::cout << row_bg
                          << "  " << label_color << label << esc_reset()
                          << row_bg << " : " << value_color << value << esc_reset()
                          << std::endl;
            }

            divider();
        }

        return;
    }

    const std::size_t max_column_width = 22;
    std::vector<std::size_t> widths(column_names.size(), 0);
    for (std::size_t i = 0; i < column_names.size(); ++i) {
        widths[i] = std::min<std::size_t>(std::max<std::size_t>(normalizeConsoleText(column_names[i]).size(), 4), max_column_width);
    }

    for (std::size_t row_index = start_row; row_index < end_row; ++row_index) {
        const auto& row = rows[row_index];
        for (std::size_t i = 0; i < column_names.size(); ++i) {
            std::string value = i < row.size() ? normalizeConsoleText(row[i]) : "";
            widths[i] = std::min<std::size_t>(std::max(widths[i], value.size()), max_column_width);
        }
    }

    auto print_border = [&]() {
        std::cout << border_color << '+';
        for (std::size_t i = 0; i < widths.size(); ++i) {
            std::cout << std::string(widths[i] + 2, '-') << '+';
        }
        std::cout << esc_reset() << std::endl;
    };

    print_border();
    std::cout << border_color << '|' << esc_reset();
    for (std::size_t i = 0; i < column_names.size(); ++i) {
        std::cout << header_color << ' ' << padConsoleText(column_names[i], widths[i]) << ' ' << esc_reset() << border_color << '|' << esc_reset();
    }
    std::cout << std::endl;
    print_border();

    for (std::size_t row_index = start_row; row_index < end_row; ++row_index) {
        const std::string& row_bg = (row_index % 2 == 0) ? row_even_color : row_odd_color;
        std::cout << border_color << '|' << esc_reset();
        for (std::size_t column_index = 0; column_index < column_names.size(); ++column_index) {
            std::string value = column_index < rows[row_index].size() ? normalizeConsoleText(rows[row_index][column_index]) : "";
            std::cout << row_bg << value_color << ' ' << padConsoleText(value, widths[column_index]) << ' ' << esc_reset() << border_color << '|' << esc_reset();
        }
        std::cout << std::endl;
    }

    print_border();
}

bool prepareSqliteStatement(sqlite3* db, const std::string& query, SqliteStmtPtr& statement) {
    sqlite3_stmt* raw_statement = nullptr;
    if (sqlite3_prepare_v2(db, query.c_str(), -1, &raw_statement, nullptr) != SQLITE_OK) {
        std::cerr << "SQL Error: " << sqlite3_errmsg(db) << std::endl;
        return false;
    }

    statement.reset(raw_statement);
    return true;
}

struct Item {
    int item_id;
    std::string item_name;
    std::string retailer;
    std::string associate_link;
    double price;
    double scores[NUM_CATEGORIES];
};

struct RankedItem {
    int item_id;
    std::string item_name;
    std::string retailer;
    std::string associate_link;
    double price;
    double distance_squared; 
    double match_percentage; 
    
    bool operator>(const RankedItem& other) const {
        return distance_squared > other.distance_squared;
    }
};

struct RankedItemWorseDistanceFirst {
    bool operator()(const RankedItem& a, const RankedItem& b) const {
        return a.distance_squared < b.distance_squared;
    }
};

double calculateSquaredDistance(const double user_scores[NUM_CATEGORIES], 
                                const double item_scores[NUM_CATEGORIES], 
                                const double category_weights[NUM_CATEGORIES]) {
    double total_distance_squared = 0.0;
    
    for (int i = 0; i < NUM_CATEGORIES; i++) {
        double weighted_user = user_scores[i] * category_weights[i];
        double weighted_item = item_scores[i];
        
        double diff = weighted_user - weighted_item;
        
        total_distance_squared += (diff * diff); 
    }
    
    return total_distance_squared;
}

bool isValidPassword(const std::string& password) { //6 character minimum
    if (password.length() < 6) {
        std::cout << "Error: password must be at least 6 characters." << std::endl;
        return false;
    }
    return true;
}

bool isValidEmail(const std::string& email) {
    if (email.find("@gmail.com") != std::string::npos ||
        email.find("@outlook.com") != std::string::npos ||
        email.find("@linux.com") != std::string::npos) {
        return true;
    }
    std::cout << "Error: invalid domain (use @gmail.com, @outlook.com, @linux.com)" << std::endl;
    std::cout << "Please enter a valid email address" << std::endl;
    return false;
}

void renderSlider(const std::string& category, double &value) {
    const int BAR_WIDTH = 20;
    bool adjusting = true;

    while (adjusting) {
        // clear line and display instructions
        std::cout << "\r" << category << " [" ;
        
        // draw the visual bar
        int pos = static_cast<int>((value / 2.0) * BAR_WIDTH);
        for (int i = 0; i < BAR_WIDTH; ++i) {
            if (i < pos) std::cout << "=";
            else if (i == pos) std::cout << ">";
            else std::cout << " ";
        }
        std::cout << "] " << (int)(value * 50) << "% (A: - | S: + | Enter: Confirm)";
        std::cout.flush();

        // handle input
        char key = getch_cross(); 
        if (key == 'a' || key == 'A') {
            if (value > 0.0) value -= 0.1; // decrease by 0.1
        } else if (key == 's' || key == 'S') {
            if (value < 2.0) value += 0.1; // increase by 0.1
        } else if (key == 10 || key == 13) { // 10 is Enter on Unix, 13 is carriage return
            adjusting = false;
            std::cout << std::endl; // move to next line after confirm
        }
        // boundary check
        if (value < 0) value = 0;
        if (value > 2.0) value = 2.0;
    }
}


sqlite3* getDBConnection() {
    sqlite3* db = nullptr;
    if (sqlite3_open(DB_PATH.c_str(), &db) != SQLITE_OK) {
        std::cerr << "Database connection error: "
                  << (db ? sqlite3_errmsg(db) : "unknown error") << std::endl;
        if (db) {
            sqlite3_close(db);
        }
        return nullptr;
    }

    sqlite3_exec(db, "PRAGMA foreign_keys = ON;", nullptr, nullptr, nullptr);
    if (!ensureDatabaseCompatibility(db)) {
        sqlite3_close(db);
        return nullptr;
    }
    return db;
}

struct UserAccount {
    int user_id;
    std::string username;
    std::string email;
    bool is_admin;
};

std::string getSqliteValue(sqlite3_stmt* stmt, int column) {
    switch (sqlite3_column_type(stmt, column)) {
        case SQLITE_INTEGER:
            return std::to_string(sqlite3_column_int64(stmt, column));
        case SQLITE_FLOAT:
            return std::to_string(sqlite3_column_double(stmt, column));
        case SQLITE_TEXT:
            return getSqliteText(stmt, column);
        case SQLITE_NULL:
            return "NULL";
        default:
            return "";
    }
}

bool tableHasColumn(sqlite3* db, const std::string& table, const std::string& column) {
    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    std::string query = "PRAGMA table_info(" + table + ")";

    if (!prepareSqliteStatement(db, query, statement)) {
        return false;
    }

    while (sqlite3_step(statement.get()) == SQLITE_ROW) {
        if (getSqliteText(statement.get(), 1) == column) {
            return true;
        }
    }

    return false;
}

bool tableExists(sqlite3* db, const std::string& table) {
    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    std::string query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?";
    if (!prepareSqliteStatement(db, query, statement)) return false;
    sqlite3_bind_text(statement.get(), 1, table.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(statement.get()) == SQLITE_ROW) return true;
    return false;
}

bool ensureDatabaseCompatibility(sqlite3* db) {
    // if core tables do not exist (fresh DB), initialize schema from code.
    if (!tableExists(db, "users_login")) {
        const char* init_sql = R"sql(
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users_login (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username_ varchar(255) NOT NULL,
    password_ varchar(255) NOT NULL,
    email_ varchar(255) NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0 CHECK (is_admin IN (0, 1))
);

CREATE TABLE IF NOT EXISTS user_profiles (
    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_ varchar(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users_login(user_id) ON DELETE CASCADE,

    -- Category scores are stored as unsigned bytes, so valid values are 0-255.
    computing_devices_score TINYINT DEFAULT 0 CHECK (computing_devices_score BETWEEN 0 AND 255),
    peripherals_score TINYINT DEFAULT 0 CHECK (peripherals_score BETWEEN 0 AND 255),
    displays_score TINYINT DEFAULT 0 CHECK (displays_score BETWEEN 0 AND 255),
    storage_electronics_score TINYINT DEFAULT 0 CHECK (storage_electronics_score BETWEEN 0 AND 255),
    audio_score TINYINT DEFAULT 0 CHECK (audio_score BETWEEN 0 AND 255),
    video_score TINYINT DEFAULT 0 CHECK (video_score BETWEEN 0 AND 255),
    wearables_tech_score TINYINT DEFAULT 0 CHECK (wearables_tech_score BETWEEN 0 AND 255),
    accessories_electronics_score TINYINT DEFAULT 0 CHECK (accessories_electronics_score BETWEEN 0 AND 255),
    power_charging_score TINYINT DEFAULT 0 CHECK (power_charging_score BETWEEN 0 AND 255),

    furniture_score TINYINT DEFAULT 0 CHECK (furniture_score BETWEEN 0 AND 255),
    home_decor_score TINYINT DEFAULT 0 CHECK (home_decor_score BETWEEN 0 AND 255),
    storage_home_score TINYINT DEFAULT 0 CHECK (storage_home_score BETWEEN 0 AND 255),
    cleaning_score TINYINT DEFAULT 0 CHECK (cleaning_score BETWEEN 0 AND 255),
    home_organization_score TINYINT DEFAULT 0 CHECK (home_organization_score BETWEEN 0 AND 255),

    skincare_score TINYINT DEFAULT 0 CHECK (skincare_score BETWEEN 0 AND 255),
    personal_hygiene_score TINYINT DEFAULT 0 CHECK (personal_hygiene_score BETWEEN 0 AND 255),

    men_fashion_score TINYINT DEFAULT 0 CHECK (men_fashion_score BETWEEN 0 AND 255),
    women_fashion_score TINYINT DEFAULT 0 CHECK (women_fashion_score BETWEEN 0 AND 255),
    children_fashion_score TINYINT DEFAULT 0 CHECK (children_fashion_score BETWEEN 0 AND 255),
    fashion_general_score TINYINT DEFAULT 0 CHECK (fashion_general_score BETWEEN 0 AND 255),

    jewelry_score TINYINT DEFAULT 0 CHECK (jewelry_score BETWEEN 0 AND 255),
    luxury_score TINYINT DEFAULT 0 CHECK (luxury_score BETWEEN 0 AND 255),

    toys_score TINYINT DEFAULT 0 CHECK (toys_score BETWEEN 0 AND 255),
    educational_toys_score TINYINT DEFAULT 0 CHECK (educational_toys_score BETWEEN 0 AND 255),
    games_puzzles_score TINYINT DEFAULT 0 CHECK (games_puzzles_score BETWEEN 0 AND 255),
    baby_gear_score TINYINT DEFAULT 0 CHECK (baby_gear_score BETWEEN 0 AND 255),

    pet_toys_score TINYINT DEFAULT 0 CHECK (pet_toys_score BETWEEN 0 AND 255),
    pet_health_score TINYINT DEFAULT 0 CHECK (pet_health_score BETWEEN 0 AND 255),

    car_accessories_score TINYINT DEFAULT 0 CHECK (car_accessories_score BETWEEN 0 AND 255),
    car_vehicle_score TINYINT DEFAULT 0 CHECK (car_vehicle_score BETWEEN 0 AND 255),

    power_tools_score TINYINT DEFAULT 0 CHECK (power_tools_score BETWEEN 0 AND 255),
    hand_tools_score TINYINT DEFAULT 0 CHECK (hand_tools_score BETWEEN 0 AND 255),
    industrial_score TINYINT DEFAULT 0 CHECK (industrial_score BETWEEN 0 AND 255),
    safety_score TINYINT DEFAULT 0 CHECK (safety_score BETWEEN 0 AND 255),

    gardening_supplies_score TINYINT DEFAULT 0 CHECK (gardening_supplies_score BETWEEN 0 AND 255),
    outdoor_score TINYINT DEFAULT 0 CHECK (outdoor_score BETWEEN 0 AND 255),
    camping_score TINYINT DEFAULT 0 CHECK (camping_score BETWEEN 0 AND 255),
    fitness_score TINYINT DEFAULT 0 CHECK (fitness_score BETWEEN 0 AND 255),

    books_score TINYINT DEFAULT 0 CHECK (books_score BETWEEN 0 AND 255),
    music_instruments_score TINYINT DEFAULT 0 CHECK (music_instruments_score BETWEEN 0 AND 255),
    movies_media_score TINYINT DEFAULT 0 CHECK (movies_media_score BETWEEN 0 AND 255),

    -- Slider weights use a compact 0.0-2.0 scale.
    electronics_slider DOUBLE DEFAULT 0 CHECK (electronics_slider BETWEEN 0 AND 2),
    home_slider DOUBLE DEFAULT 0 CHECK (home_slider BETWEEN 0 AND 2),
    personal_care_slider DOUBLE DEFAULT 0 CHECK (personal_care_slider BETWEEN 0 AND 2),
    wearables_slider DOUBLE DEFAULT 0 CHECK (wearables_slider BETWEEN 0 AND 2),
    luxury_slider DOUBLE DEFAULT 0 CHECK (luxury_slider BETWEEN 0 AND 2),
    children_slider DOUBLE DEFAULT 0 CHECK (children_slider BETWEEN 0 AND 2),
    pet_slider DOUBLE DEFAULT 0 CHECK (pet_slider BETWEEN 0 AND 2),
    car_slider DOUBLE DEFAULT 0 CHECK (car_slider BETWEEN 0 AND 2),
    outdoor_slider DOUBLE DEFAULT 0 CHECK (outdoor_slider BETWEEN 0 AND 2),
    creative_slider DOUBLE DEFAULT 0 CHECK (creative_slider BETWEEN 0 AND 2)
);

CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name VARCHAR(255) NOT NULL,
    retailer VARCHAR(100),
    associate_link TEXT,
    price DECIMAL(10, 2),

    -- Category scores are stored as unsigned bytes, so valid values are 0-255.
    computing_devices_score TINYINT DEFAULT 0 CHECK (computing_devices_score BETWEEN 0 AND 255),
    peripherals_score TINYINT DEFAULT 0 CHECK (peripherals_score BETWEEN 0 AND 255),
    displays_score TINYINT DEFAULT 0 CHECK (displays_score BETWEEN 0 AND 255),
    storage_electronics_score TINYINT DEFAULT 0 CHECK (storage_electronics_score BETWEEN 0 AND 255),
    audio_score TINYINT DEFAULT 0 CHECK (audio_score BETWEEN 0 AND 255),
    video_score TINYINT DEFAULT 0 CHECK (video_score BETWEEN 0 AND 255),
    wearables_tech_score TINYINT DEFAULT 0 CHECK (wearables_tech_score BETWEEN 0 AND 255),
    accessories_electronics_score TINYINT DEFAULT 0 CHECK (accessories_electronics_score BETWEEN 0 AND 255),
    power_charging_score TINYINT DEFAULT 0 CHECK (power_charging_score BETWEEN 0 AND 255),

    furniture_score TINYINT DEFAULT 0 CHECK (furniture_score BETWEEN 0 AND 255),
    home_decor_score TINYINT DEFAULT 0 CHECK (home_decor_score BETWEEN 0 AND 255),
    storage_home_score TINYINT DEFAULT 0 CHECK (storage_home_score BETWEEN 0 AND 255),
    cleaning_score TINYINT DEFAULT 0 CHECK (cleaning_score BETWEEN 0 AND 255),
    home_organization_score TINYINT DEFAULT 0 CHECK (home_organization_score BETWEEN 0 AND 255),

    skincare_score TINYINT DEFAULT 0 CHECK (skincare_score BETWEEN 0 AND 255),
    personal_hygiene_score TINYINT DEFAULT 0 CHECK (personal_hygiene_score BETWEEN 0 AND 255),

    men_fashion_score TINYINT DEFAULT 0 CHECK (men_fashion_score BETWEEN 0 AND 255),
    women_fashion_score TINYINT DEFAULT 0 CHECK (women_fashion_score BETWEEN 0 AND 255),
    children_fashion_score TINYINT DEFAULT 0 CHECK (children_fashion_score BETWEEN 0 AND 255),
    fashion_general_score TINYINT DEFAULT 0 CHECK (fashion_general_score BETWEEN 0 AND 255),

    jewelry_score TINYINT DEFAULT 0 CHECK (jewelry_score BETWEEN 0 AND 255),
    luxury_score TINYINT DEFAULT 0 CHECK (luxury_score BETWEEN 0 AND 255),

    toys_score TINYINT DEFAULT 0 CHECK (toys_score BETWEEN 0 AND 255),
    educational_toys_score TINYINT DEFAULT 0 CHECK (educational_toys_score BETWEEN 0 AND 255),
    games_puzzles_score TINYINT DEFAULT 0 CHECK (games_puzzles_score BETWEEN 0 AND 255),
    baby_gear_score TINYINT DEFAULT 0 CHECK (baby_gear_score BETWEEN 0 AND 255),

    pet_toys_score TINYINT DEFAULT 0 CHECK (pet_toys_score BETWEEN 0 AND 255),
    pet_health_score TINYINT DEFAULT 0 CHECK (pet_health_score BETWEEN 0 AND 255),

    car_accessories_score TINYINT DEFAULT 0 CHECK (car_accessories_score BETWEEN 0 AND 255),
    car_vehicle_score TINYINT DEFAULT 0 CHECK (car_vehicle_score BETWEEN 0 AND 255),

    power_tools_score TINYINT DEFAULT 0 CHECK (power_tools_score BETWEEN 0 AND 255),
    hand_tools_score TINYINT DEFAULT 0 CHECK (hand_tools_score BETWEEN 0 AND 255),
    industrial_score TINYINT DEFAULT 0 CHECK (industrial_score BETWEEN 0 AND 255),
    safety_score TINYINT DEFAULT 0 CHECK (safety_score BETWEEN 0 AND 255),

    gardening_supplies_score TINYINT DEFAULT 0 CHECK (gardening_supplies_score BETWEEN 0 AND 255),
    outdoor_score TINYINT DEFAULT 0 CHECK (outdoor_score BETWEEN 0 AND 255),
    camping_score TINYINT DEFAULT 0 CHECK (camping_score BETWEEN 0 AND 255),
    fitness_score TINYINT DEFAULT 0 CHECK (fitness_score BETWEEN 0 AND 255),

    books_score TINYINT DEFAULT 0 CHECK (books_score BETWEEN 0 AND 255),
    music_instruments_score TINYINT DEFAULT 0 CHECK (music_instruments_score BETWEEN 0 AND 255),
    movies_media_score TINYINT DEFAULT 0 CHECK (movies_media_score BETWEEN 0 AND 255)
);
)sql";

        char* errmsg = nullptr;
        if (sqlite3_exec(db, init_sql, nullptr, nullptr, &errmsg) != SQLITE_OK) {
            std::cerr << "Database initialization error: " << (errmsg ? errmsg : sqlite3_errmsg(db)) << std::endl;
            if (errmsg) sqlite3_free(errmsg);
            return false;
        }
        if (errmsg) sqlite3_free(errmsg);
    }
    if (!tableHasColumn(db, "users_login", "is_admin")) {
        char* error_message = nullptr;
        if (sqlite3_exec(db,
                "ALTER TABLE users_login ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;",
                nullptr,
                nullptr,
                &error_message) != SQLITE_OK) {
            std::cerr << "Database migration error: "
                      << (error_message ? error_message : sqlite3_errmsg(db)) << std::endl;
            if (error_message) {
                sqlite3_free(error_message);
            }
            return false;
        }
        if (error_message) {
            sqlite3_free(error_message);
        }
    }

    char* error_message = nullptr;
    if (sqlite3_exec(db,
            "CREATE TABLE IF NOT EXISTS sales ("
            "sale_id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "user_id INTEGER NOT NULL REFERENCES users_login(user_id) ON DELETE CASCADE,"
            "item_id INTEGER NOT NULL REFERENCES items(item_id) ON DELETE RESTRICT,"
            "retailer_name VARCHAR(100) NOT NULL,"
            "sale_price DECIMAL(10, 2) NOT NULL CHECK (sale_price >= 0),"
            "commission_rate DECIMAL(5, 4) NOT NULL CHECK (commission_rate >= 0 AND commission_rate <= 1),"
            "profit DECIMAL(10, 2) NOT NULL CHECK (profit >= 0 AND profit <= sale_price),"
            "sold_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP"
            ");",
            nullptr,
            nullptr,
            &error_message) != SQLITE_OK) {
        std::cerr << "Database migration error: "
                  << (error_message ? error_message : sqlite3_errmsg(db)) << std::endl;
        if (error_message) {
            sqlite3_free(error_message);
        }
        return false;
    }
    if (error_message) {
        sqlite3_free(error_message);
    }

    return true;
}

std::string buildUserLabel(const UserAccount& user) {
    return user.username + (user.is_admin ? " [Admin]" : " [User]");
}

void renderNavigationBar(const std::string& page_name,
                         const std::string& user_label,
                         const std::string& actions) {
    printDivider();
    const std::string reset = esc_reset();
    // Palette colors (gruvbox_dark)
    const std::string fg0 = esc_fg(251,241,199);
    const std::string orange_bg = esc_bg(214,93,14);
    const std::string yellow_fg = esc_fg(215,153,33);
    const std::string aqua_fg = esc_fg(104,157,106);
    const std::string blue_fg = esc_fg(69,133,136);

    // Header: Giftyfy label with orange background, page name in yellow
    std::cout << orange_bg << fg0 << " Giftyfy " << reset << " "
              << yellow_fg << "| " << page_name << reset << std::endl;

    // User and actions
    std::cout << aqua_fg << "User: " << esc_bold() << user_label << reset << std::endl;
    std::cout << blue_fg << actions << reset << std::endl;
    printDivider();
}

struct UserProfile {
    int profile_id;
    std::string name;
    
    // Sliders (category weights)
    double electronics_slider;
    double home_slider;
    double personal_care_slider;
    double wearables_slider;
    double luxury_slider;
    double children_slider;
    double pet_slider;
    double car_slider;
    double outdoor_slider;
    double creative_slider;
    
    // Electronics (0-8)
    int computing_devices_score;
    int peripherals_score;
    int displays_score;
    int storage_electronics_score;
    int audio_score;
    int video_score;
    int wearables_tech_score;
    int accessories_electronics_score;
    int power_charging_score;
    
    // Home (9-13)
    int furniture_score;
    int home_decor_score;
    int storage_home_score;
    int cleaning_score;
    int home_organization_score;
    
    // Personal Care (14-15)
    int skincare_score;
    int personal_hygiene_score;
    
    // Fashion (16-19)
    int men_fashion_score;
    int women_fashion_score;
    int children_fashion_score;
    int fashion_general_score;
    
    // Luxury (20-21)
    int jewelry_score;
    int luxury_score;
    
    // Children & Family (22-25)
    int toys_score;
    int educational_toys_score;
    int games_puzzles_score;
    int baby_gear_score;
    
    // Pets (26-27)
    int pet_toys_score;
    int pet_health_score;
    
    // Cars & Tools (28-33)
    int car_accessories_score;
    int car_vehicle_score;
    int power_tools_score;
    int hand_tools_score;
    int industrial_score;
    int safety_score;
    
    // Outdoors & Creative (34-40)
    int gardening_supplies_score;
    int outdoor_score;
    int camping_score;
    int fitness_score;
    int books_score;
    int music_instruments_score;
    int movies_media_score;
};

UserAccount authenticateUser(const std::string& username, const std::string& password) {
    UserAccount user;
    user.user_id = -1;
    user.is_admin = false;
    
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database." << std::endl;
        return user;
    }

    bool has_admin_column = tableHasColumn(db.get(), "users_login", "is_admin");

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (has_admin_column) {
        if (!prepareSqliteStatement(db.get(),
                "SELECT user_id, username_, email_, is_admin FROM users_login WHERE username_ = ? AND password_ = ?",
                statement)) {
            std::cerr << "Authentication query failed." << std::endl;
            return user;
        }
    } else {
        if (!prepareSqliteStatement(db.get(),
                "SELECT user_id, username_, email_ FROM users_login WHERE username_ = ? AND password_ = ?",
                statement)) {
            std::cerr << "Authentication query failed." << std::endl;
            return user;
        }
    }

    sqlite3_bind_text(statement.get(), 1, username.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(statement.get(), 2, password.c_str(), -1, SQLITE_TRANSIENT);

    if (sqlite3_step(statement.get()) == SQLITE_ROW) {
        user.user_id = sqlite3_column_int(statement.get(), 0);
        user.username = getSqliteText(statement.get(), 1);
        user.email = getSqliteText(statement.get(), 2);
        user.is_admin = has_admin_column && sqlite3_column_int(statement.get(), 3) == 1;
    }

    return user;
}

UserProfile loadUserPreferences(int profile_id, int user_id) {
    UserProfile profile;
    profile.profile_id = -1;
    profile.name = "Default Profile";
    
    // Initialize sliders
    profile.electronics_slider = 0.0;
    profile.home_slider = 0.0;
    profile.personal_care_slider = 0.0;
    profile.wearables_slider = 0.0;
    profile.luxury_slider = 0.0;
    profile.children_slider = 0.0;
    profile.pet_slider = 0.0;
    profile.car_slider = 0.0;
    profile.outdoor_slider = 0.0;
    profile.creative_slider = 0.0;
    
    // Initialize all scores to 0
    profile.computing_devices_score = 0;
    profile.peripherals_score = 0;
    profile.displays_score = 0;
    profile.storage_electronics_score = 0;
    profile.audio_score = 0;
    profile.video_score = 0;
    profile.wearables_tech_score = 0;
    profile.accessories_electronics_score = 0;
    profile.power_charging_score = 0;
    profile.furniture_score = 0;
    profile.home_decor_score = 0;
    profile.storage_home_score = 0;
    profile.cleaning_score = 0;
    profile.home_organization_score = 0;
    profile.skincare_score = 0;
    profile.personal_hygiene_score = 0;
    profile.men_fashion_score = 0;
    profile.women_fashion_score = 0;
    profile.children_fashion_score = 0;
    profile.fashion_general_score = 0;
    profile.jewelry_score = 0;
    profile.luxury_score = 0;
    profile.toys_score = 0;
    profile.educational_toys_score = 0;
    profile.games_puzzles_score = 0;
    profile.baby_gear_score = 0;
    profile.pet_toys_score = 0;
    profile.pet_health_score = 0;
    profile.car_accessories_score = 0;
    profile.car_vehicle_score = 0;
    profile.power_tools_score = 0;
    profile.hand_tools_score = 0;
    profile.industrial_score = 0;
    profile.safety_score = 0;
    profile.gardening_supplies_score = 0;
    profile.outdoor_score = 0;
    profile.camping_score = 0;
    profile.fitness_score = 0;
    profile.books_score = 0;
    profile.music_instruments_score = 0;
    profile.movies_media_score = 0;
    
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database." << std::endl;
        return profile;
    }

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "SELECT profile_id, name_, user_id, "
            "electronics_slider, home_slider, personal_care_slider, wearables_slider, "
            "luxury_slider, children_slider, pet_slider, car_slider, outdoor_slider, creative_slider, "
            "computing_devices_score, peripherals_score, displays_score, storage_electronics_score, "
            "audio_score, video_score, wearables_tech_score, accessories_electronics_score, power_charging_score, "
            "furniture_score, home_decor_score, storage_home_score, cleaning_score, home_organization_score, "
            "skincare_score, personal_hygiene_score, "
            "men_fashion_score, women_fashion_score, children_fashion_score, fashion_general_score, "
            "jewelry_score, luxury_score, "
            "toys_score, educational_toys_score, games_puzzles_score, baby_gear_score, "
            "pet_toys_score, pet_health_score, "
            "car_accessories_score, car_vehicle_score, "
            "power_tools_score, hand_tools_score, industrial_score, safety_score, "
            "gardening_supplies_score, outdoor_score, camping_score, fitness_score, "
            "books_score, music_instruments_score, movies_media_score "
            "FROM user_profiles WHERE profile_id = ?",
            statement)) {
        std::cerr << "Query preparation failed." << std::endl;
        return profile;
    }

    sqlite3_bind_int(statement.get(), 1, profile_id);

    if (sqlite3_step(statement.get()) == SQLITE_ROW) {
        int profile_owner_id = sqlite3_column_int(statement.get(), 2);
        
        // Verify user owns this profile (FK check)
        if (profile_owner_id != user_id) {
            std::cerr << "Access denied: You do not own this profile." << std::endl;
            return profile;
        }
        
        profile.profile_id = sqlite3_column_int(statement.get(), 0);
        profile.name = getSqliteText(statement.get(), 1);
        profile.electronics_slider = sqlite3_column_double(statement.get(), 3);
        profile.home_slider = sqlite3_column_double(statement.get(), 4);
        profile.personal_care_slider = sqlite3_column_double(statement.get(), 5);
        profile.wearables_slider = sqlite3_column_double(statement.get(), 6);
        profile.luxury_slider = sqlite3_column_double(statement.get(), 7);
        profile.children_slider = sqlite3_column_double(statement.get(), 8);
        profile.pet_slider = sqlite3_column_double(statement.get(), 9);
        profile.car_slider = sqlite3_column_double(statement.get(), 10);
        profile.outdoor_slider = sqlite3_column_double(statement.get(), 11);
        profile.creative_slider = sqlite3_column_double(statement.get(), 12);
        profile.computing_devices_score = sqlite3_column_int(statement.get(), 13);
        profile.peripherals_score = sqlite3_column_int(statement.get(), 14);
        profile.displays_score = sqlite3_column_int(statement.get(), 15);
        profile.storage_electronics_score = sqlite3_column_int(statement.get(), 16);
        profile.audio_score = sqlite3_column_int(statement.get(), 17);
        profile.video_score = sqlite3_column_int(statement.get(), 18);
        profile.wearables_tech_score = sqlite3_column_int(statement.get(), 19);
        profile.accessories_electronics_score = sqlite3_column_int(statement.get(), 20);
        profile.power_charging_score = sqlite3_column_int(statement.get(), 21);
        profile.furniture_score = sqlite3_column_int(statement.get(), 22);
        profile.home_decor_score = sqlite3_column_int(statement.get(), 23);
        profile.storage_home_score = sqlite3_column_int(statement.get(), 24);
        profile.cleaning_score = sqlite3_column_int(statement.get(), 25);
        profile.home_organization_score = sqlite3_column_int(statement.get(), 26);
        profile.skincare_score = sqlite3_column_int(statement.get(), 27);
        profile.personal_hygiene_score = sqlite3_column_int(statement.get(), 28);
        profile.men_fashion_score = sqlite3_column_int(statement.get(), 29);
        profile.women_fashion_score = sqlite3_column_int(statement.get(), 30);
        profile.children_fashion_score = sqlite3_column_int(statement.get(), 31);
        profile.fashion_general_score = sqlite3_column_int(statement.get(), 32);
        profile.jewelry_score = sqlite3_column_int(statement.get(), 33);
        profile.luxury_score = sqlite3_column_int(statement.get(), 34);
        profile.toys_score = sqlite3_column_int(statement.get(), 35);
        profile.educational_toys_score = sqlite3_column_int(statement.get(), 36);
        profile.games_puzzles_score = sqlite3_column_int(statement.get(), 37);
        profile.baby_gear_score = sqlite3_column_int(statement.get(), 38);
        profile.pet_toys_score = sqlite3_column_int(statement.get(), 39);
        profile.pet_health_score = sqlite3_column_int(statement.get(), 40);
        profile.car_accessories_score = sqlite3_column_int(statement.get(), 41);
        profile.car_vehicle_score = sqlite3_column_int(statement.get(), 42);
        profile.power_tools_score = sqlite3_column_int(statement.get(), 43);
        profile.hand_tools_score = sqlite3_column_int(statement.get(), 44);
        profile.industrial_score = sqlite3_column_int(statement.get(), 45);
        profile.safety_score = sqlite3_column_int(statement.get(), 46);
        profile.gardening_supplies_score = sqlite3_column_int(statement.get(), 47);
        profile.outdoor_score = sqlite3_column_int(statement.get(), 48);
        profile.camping_score = sqlite3_column_int(statement.get(), 49);
        profile.fitness_score = sqlite3_column_int(statement.get(), 50);
        profile.books_score = sqlite3_column_int(statement.get(), 51);
        profile.music_instruments_score = sqlite3_column_int(statement.get(), 52);
        profile.movies_media_score = sqlite3_column_int(statement.get(), 53);
    }

    return profile;
}

bool createUserAccount(const std::string& username, const std::string& password, const std::string& email, bool is_admin = false) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) return false;

    char* error_message = nullptr;
    if (sqlite3_exec(db.get(), "BEGIN IMMEDIATE TRANSACTION;", nullptr, nullptr, &error_message) != SQLITE_OK) {
        std::cerr << "SQL Error: " << (error_message ? error_message : sqlite3_errmsg(db.get())) << std::endl;
        if (error_message) sqlite3_free(error_message);
        return false;
    }
    if (error_message) sqlite3_free(error_message);

    auto rollback = [&]() {
        sqlite3_exec(db.get(), "ROLLBACK;", nullptr, nullptr, nullptr);
    };

    SqliteStmtPtr user_statement(nullptr, sqlite3_finalize);
    if (is_admin && tableHasColumn(db.get(), "users_login", "is_admin")) {
        if (!prepareSqliteStatement(db.get(),
                "INSERT INTO users_login (username_, password_, email_, is_admin) VALUES (?, ?, ?, 1)",
                user_statement)) {
            rollback();
            return false;
        }
    } else {
        if (!prepareSqliteStatement(db.get(),
                "INSERT INTO users_login (username_, password_, email_) VALUES (?, ?, ?)",
                user_statement)) {
            rollback();
            return false;
        }
    }

    sqlite3_bind_text(user_statement.get(), 1, username.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(user_statement.get(), 2, password.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(user_statement.get(), 3, email.c_str(), -1, SQLITE_TRANSIENT);

    if (sqlite3_step(user_statement.get()) != SQLITE_DONE) {
        std::cerr << "SQL Error: " << sqlite3_errmsg(db.get()) << std::endl;
        rollback();
        return false;
    }

    // removed a function which creates an empty profile for the new user, as it is useless

    if (sqlite3_exec(db.get(), "COMMIT;", nullptr, nullptr, &error_message) != SQLITE_OK) {
        std::cerr << "SQL Error: " << (error_message ? error_message : sqlite3_errmsg(db.get())) << std::endl;
        if (error_message) sqlite3_free(error_message);
        rollback();
        return false;
    }
    if (error_message) sqlite3_free(error_message);

    return true;
}

bool usernameExists(const std::string& username) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) return false;

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "SELECT COUNT(*) FROM users_login WHERE username_ = ?",
            statement)) {
        return false;
    }

    sqlite3_bind_text(statement.get(), 1, username.c_str(), -1, SQLITE_TRANSIENT);

    if (sqlite3_step(statement.get()) == SQLITE_ROW) {
        int count = sqlite3_column_int(statement.get(), 0);
        return count > 0;
    }

    return false;
}

UserAccount promptForSignIn() {
    UserAccount user;
    user.user_id = -1;
    std::string username, password;
    
    printDivider();
    std::cout << "         GIFTYFY - SIGN IN" << std::endl;
    printDivider();
    renderNavigationBar("Sign In", "Guest", "[1] Sign In   [2] Create Account   [X] Exit");
    std::cout << std::endl;
    
    bool authenticated = false;
    int attempts = 0;
    const int MAX_ATTEMPTS = 3;
    
    while (!authenticated && attempts < MAX_ATTEMPTS) {
        std::cout << "Enter username: ";
        std::getline(std::cin, username);
        
        password = readMaskedInput("Enter password");
        
        user = authenticateUser(username, password);
        
        if (user.user_id != -1) {
            authenticated = true;
            std::cout << "\nLogin successful! Welcome, " << username << "!" << std::endl;
        } else {
            ++attempts;
            clearScreen();
            renderNavigationBar("Sign In", "Guest", "[1] Sign In   [2] Create Account   [X] Exit");
            if (attempts < MAX_ATTEMPTS) {
                std::cout << "Invalid username or password. Attempts remaining: " 
                         << (MAX_ATTEMPTS - attempts) << std::endl << std::endl;
            } else {
                std::cout << "Too many failed attempts. Exiting..." << std::endl << std::endl;
            }
        }
    }
    
    return user;
}

UserAccount promptForSignUp() {
    UserAccount user;
    user.user_id = -1;
    std::string username, password, email, confirm_password;
    
    printDivider();
    std::cout << "      GIFTYFY - CREATE ACCOUNT" << std::endl;
    printDivider();
    renderNavigationBar("Create Account", "Guest", "[1] Sign In   [2] Create Account   [X] Exit");
    std::cout << std::endl;
    
    bool username_valid = false;
    while (!username_valid) {
        std::cout << "Enter username: ";
        std::getline(std::cin, username);
        
        if (username.length() < 3) {
            std::cout << "Error: at least 3 characters (letters, numbers, special characters)" << std::endl;
        } else if (usernameExists(username)) {
            std::cout << "Error: Username already exists. Please choose another." << std::endl;
        } else {
            username_valid = true;
        }
    }
    
    bool email_valid = false;
    while (!email_valid) {
        std::cout << "Enter email: ";
        std::getline(std::cin, email);
        email_valid = isValidEmail(email);
    }
    
    bool password_valid = false;
    while (!password_valid) {
        password = readMaskedInput("Enter password");
        password_valid = isValidPassword(password);
    }
    
    bool password_match = false;
    while (!password_match) {
        confirm_password = readMaskedInput("Confirm password");
        
        if (password == confirm_password) {
            password_match = true;
        } else {
            std::cout << "Error: Passwords do not match. Try again." << std::endl;
        }
    }
    
    if (createUserAccount(username, password, email)) {
        std::cout << "\nAccount created successfully! Please log in." << std::endl;
        user = authenticateUser(username, password);
    } else {
        std::cout << "\nFailed to create account. Please try again." << std::endl;
    }
    
    return user;
}

UserAccount handleAuthentication() {
    UserAccount user;
    user.user_id = -1;
    
    while (user.user_id == -1) { //add forgot passwrod or email function
         printDivider();
        std::cout << "         GIFTYFY - WELCOME" << std::endl;
        printDivider();
    renderNavigationBar("Welcome", "Guest", "[1] Sign In   [2] Create Account   [X] Exit");
        std::cout << std::endl;
        std::cout << "[1] Sign In" << std::endl;
        std::cout << "[2] Create Account" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        printDivider();
        std::cout << "Select an option (1-2, X to exit): ";
        
        std::string choice;
        std::getline(std::cin, choice);
        
        if (choice == "1") {
            clearScreen();
            user = promptForSignIn();
        } else if (choice == "2") {
            clearScreen();
            user = promptForSignUp();
        } else if (choice == "X" || choice == "x") {
            std::cout << "Thank you for using Giftyfy. Goodbye!" << std::endl;
            exit(0);
        } else {
            clearScreen();
            std::cout << "Invalid option. Please try again." << std::endl << std::endl;
        }
    }
    
    return user;
}

std::vector<UserProfile> getUserProfiles(int user_id) {
    std::vector<UserProfile> profiles;
    
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) return profiles;
    // reffer to the function loadUserPreferences, we need to get the username of the user to exclude the profile with the same name as the username, which is the default profile created for each user, and is not meant to be used by the user, but is used as a fallback when loading preferences if the user does not have any other profiles
    //refer to line 805 
    std::string username;
    SqliteStmtPtr user_stmt(nullptr, sqlite3_finalize);
    if (prepareSqliteStatement(db.get(), "SELECT username_ FROM users_login WHERE user_id = ?", user_stmt)) {
        sqlite3_bind_int(user_stmt.get(), 1, user_id);
        if (sqlite3_step(user_stmt.get()) == SQLITE_ROW) {
            username = getSqliteText(user_stmt.get(), 0);
        }
    }

    std::string exclude_name;
    if (!username.empty()) exclude_name = username + "'s Profile";

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!exclude_name.empty()) {
        if (!prepareSqliteStatement(db.get(),
                "SELECT profile_id, name_ FROM user_profiles WHERE user_id = ? AND name_ != ?",
                statement)) {
            return profiles;
        }
        sqlite3_bind_int(statement.get(), 1, user_id);
        sqlite3_bind_text(statement.get(), 2, exclude_name.c_str(), -1, SQLITE_TRANSIENT);
    } else {
        if (!prepareSqliteStatement(db.get(),
                "SELECT profile_id, name_ FROM user_profiles WHERE user_id = ?",
                statement)) {
            return profiles;
        }
        sqlite3_bind_int(statement.get(), 1, user_id);
    }

    while (sqlite3_step(statement.get()) == SQLITE_ROW) {
        UserProfile profile;
        profile.profile_id = sqlite3_column_int(statement.get(), 0);
        profile.name = getSqliteText(statement.get(), 1);
        profiles.push_back(profile);
    }

    return profiles;
}

bool createNewProfile(int user_id, const std::string& profile_name) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) return false;

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "INSERT INTO user_profiles (name_, user_id) VALUES (?, ?)",
            statement)) {
        return false;
    }

    sqlite3_bind_text(statement.get(), 1, profile_name.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int(statement.get(), 2, user_id);

    if (sqlite3_step(statement.get()) != SQLITE_DONE) {
        std::cerr << "SQL Error: " << sqlite3_errmsg(db.get()) << std::endl;
        return false;
    }

    return true;
}

void runQuiz(UserProfile &profile, const std::string& user_label) {
    printDivider();
    std::cout << "         GIFTYFY - PREFERENCE QUIZ" << std::endl;
    printDivider();
    renderNavigationBar("Preference Quiz", user_label, "[Enter] Confirm each answer");
    std::cout << "\nThis 41-question quiz will help us understand what kind of gifts are perfect for this person.\n" << std::endl;
    std::cout << "Please give each question a rating from 0 to 5 (5 = they really like that, 0 = they would never be caught doing that).\n" << std::endl;
    
    std::vector<std::pair<std::string, int*>> questions = {
        // Electronics (0-8)
        {"Interest in computing devices (laptops, desktops, tablets)? (0-5): ", &profile.computing_devices_score},
        {"Interest in computer peripherals (mouse, keyboard, etc.)? (0-5): ", &profile.peripherals_score},
        {"Interest in displays and monitors? (0-5): ", &profile.displays_score},
        {"Interest in storage devices (SSDs, hard drives)? (0-5): ", &profile.storage_electronics_score},
        {"Interest in audio equipment (speakers, headphones)? (0-5): ", &profile.audio_score},
        {"Interest in video equipment (cameras, projectors)? (0-5): ", &profile.video_score},
        {"Interest in wearable tech (smartwatches, fitness trackers)? (0-5): ", &profile.wearables_tech_score},
        {"Interest in tech accessories (cables, chargers, cases)? (0-5): ", &profile.accessories_electronics_score},
        {"Interest in power and charging solutions? (0-5): ", &profile.power_charging_score},
        
        // Home (9-13)
        {"Interest in furniture? (0-5): ", &profile.furniture_score},
        {"Interest in home decor and wall art? (0-5): ", &profile.home_decor_score},
        {"Interest in home storage solutions? (0-5): ", &profile.storage_home_score},
        {"Interest in cleaning supplies and tools? (0-5): ", &profile.cleaning_score},
        {"Interest in home organization items? (0-5): ", &profile.home_organization_score},
        
        // Personal Care (14-15)
        {"Interest in skincare products? (0-5): ", &profile.skincare_score},
        {"Interest in personal hygiene items? (0-5): ", &profile.personal_hygiene_score},
        
        // Fashion (16-19)
        {"Interest in men's fashion and clothing? (0-5): ", &profile.men_fashion_score},
        {"Interest in women's fashion and clothing? (0-5): ", &profile.women_fashion_score},
        {"Interest in children's fashion? (0-5): ", &profile.children_fashion_score},
        {"Interest in general fashion accessories? (0-5): ", &profile.fashion_general_score},
        
        // Luxury (20-21)
        {"Interest in jewelry and watches? (0-5): ", &profile.jewelry_score},
        {"Interest in luxury and high-end items? (0-5): ", &profile.luxury_score},
        
        // Children & Family (22-25)
        {"Interest in toys and play items? (0-5): ", &profile.toys_score},
        {"Interest in educational toys? (0-5): ", &profile.educational_toys_score},
        {"Interest in games and puzzles? (0-5): ", &profile.games_puzzles_score},
        {"Interest in baby gear and equipment? (0-5): ", &profile.baby_gear_score},
        
        // Pets (26-27)
        {"Interest in pet toys? (0-5): ", &profile.pet_toys_score},
        {"Interest in pet health and care products? (0-5): ", &profile.pet_health_score},
        
        // Cars & Tools (28-33)
        {"Interest in car accessories? (0-5): ", &profile.car_accessories_score},
        {"Interest in vehicles and car equipment? (0-5): ", &profile.car_vehicle_score},
        {"Interest in power tools? (0-5): ", &profile.power_tools_score},
        {"Interest in hand tools? (0-5): ", &profile.hand_tools_score},
        {"Interest in industrial equipment? (0-5): ", &profile.industrial_score},
        {"Interest in safety equipment? (0-5): ", &profile.safety_score},
        
        // Outdoors & Creative (34-40)
        {"Interest in gardening supplies? (0-5): ", &profile.gardening_supplies_score},
        {"Interest in outdoor equipment? (0-5): ", &profile.outdoor_score},
        {"Interest in camping gear? (0-5): ", &profile.camping_score},
        {"Interest in fitness equipment? (0-5): ", &profile.fitness_score},
        {"Interest in books? (0-5): ", &profile.books_score},
        {"Interest in musical instruments? (0-5): ", &profile.music_instruments_score},
        {"Interest in movies and media? (0-5): ", &profile.movies_media_score}
    };
    
    for (size_t i = 0; i < questions.size(); i++) {
        std::cout << "[" << (i+1) << "/41] " << questions[i].first;
        
        int response = -1;
        while (response < 0 || response > 5) {
            std::string input;
            std::getline(std::cin, input);
            try {
                response = std::stoi(input);
                if (response < 0 || response > 5) {
                    std::cout << "Please enter a number between 0 and 5: ";
                }
            } catch (...) {
                std::cout << "Invalid input. Please enter a number between 0 and 5: ";
            }
        }
        
        // Map response (0-5) to category score (0-255 scale)
        // 0->0, 1->51, 2->102, 3->153, 4->204, 5->255
        *questions[i].second = response * 51;
    }
    
    // Initialize all sliders to 1.0 (neutral) after quiz
    profile.electronics_slider = 1.0;
    profile.home_slider = 1.0;
    profile.personal_care_slider = 1.0;
    profile.wearables_slider = 1.0;
    profile.luxury_slider = 1.0;
    profile.children_slider = 1.0;
    profile.pet_slider = 1.0;
    profile.car_slider = 1.0;
    profile.outdoor_slider = 1.0;
    profile.creative_slider = 1.0;
}

bool saveProfileScores(int profile_id, int user_id, const UserProfile &profile) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database." << std::endl;
        return false;
    }

    // Verify user owns this profile (FK check)
    SqliteStmtPtr verify_stmt(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "SELECT user_id FROM user_profiles WHERE profile_id = ?",
            verify_stmt)) {
        std::cerr << "Verification query failed." << std::endl;
        return false;
    }
    
    sqlite3_bind_int(verify_stmt.get(), 1, profile_id);
    if (sqlite3_step(verify_stmt.get()) != SQLITE_ROW) {
        std::cerr << "Profile not found." << std::endl;
        return false;
    }
    
    int stored_user_id = sqlite3_column_int(verify_stmt.get(), 0);
    if (stored_user_id != user_id) {
        std::cerr << "Access denied: You do not own this profile." << std::endl;
        return false;
    }

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "UPDATE user_profiles SET "
            "electronics_slider = ?, home_slider = ?, personal_care_slider = ?, wearables_slider = ?, "
            "luxury_slider = ?, children_slider = ?, pet_slider = ?, car_slider = ?, outdoor_slider = ?, "
            "creative_slider = ?, "
            "computing_devices_score = ?, peripherals_score = ?, displays_score = ?, storage_electronics_score = ?, "
            "audio_score = ?, video_score = ?, wearables_tech_score = ?, accessories_electronics_score = ?, power_charging_score = ?, "
            "furniture_score = ?, home_decor_score = ?, storage_home_score = ?, cleaning_score = ?, home_organization_score = ?, "
            "skincare_score = ?, personal_hygiene_score = ?, "
            "men_fashion_score = ?, women_fashion_score = ?, children_fashion_score = ?, fashion_general_score = ?, "
            "jewelry_score = ?, luxury_score = ?, "
            "toys_score = ?, educational_toys_score = ?, games_puzzles_score = ?, baby_gear_score = ?, "
            "pet_toys_score = ?, pet_health_score = ?, "
            "car_accessories_score = ?, car_vehicle_score = ?, "
            "power_tools_score = ?, hand_tools_score = ?, industrial_score = ?, safety_score = ?, "
            "gardening_supplies_score = ?, outdoor_score = ?, camping_score = ?, fitness_score = ?, "
            "books_score = ?, music_instruments_score = ?, movies_media_score = ? "
            "WHERE profile_id = ?",
            statement)) {
        std::cerr << "Update query preparation failed." << std::endl;
        return false;
    }

    int param = 1;
    // Sliders
    sqlite3_bind_double(statement.get(), param++, profile.electronics_slider);
    sqlite3_bind_double(statement.get(), param++, profile.home_slider);
    sqlite3_bind_double(statement.get(), param++, profile.personal_care_slider);
    sqlite3_bind_double(statement.get(), param++, profile.wearables_slider);
    sqlite3_bind_double(statement.get(), param++, profile.luxury_slider);
    sqlite3_bind_double(statement.get(), param++, profile.children_slider);
    sqlite3_bind_double(statement.get(), param++, profile.pet_slider);
    sqlite3_bind_double(statement.get(), param++, profile.car_slider);
    sqlite3_bind_double(statement.get(), param++, profile.outdoor_slider);
    sqlite3_bind_double(statement.get(), param++, profile.creative_slider);
    
    // All 41 category scores
    sqlite3_bind_int(statement.get(), param++, profile.computing_devices_score);
    sqlite3_bind_int(statement.get(), param++, profile.peripherals_score);
    sqlite3_bind_int(statement.get(), param++, profile.displays_score);
    sqlite3_bind_int(statement.get(), param++, profile.storage_electronics_score);
    sqlite3_bind_int(statement.get(), param++, profile.audio_score);
    sqlite3_bind_int(statement.get(), param++, profile.video_score);
    sqlite3_bind_int(statement.get(), param++, profile.wearables_tech_score);
    sqlite3_bind_int(statement.get(), param++, profile.accessories_electronics_score);
    sqlite3_bind_int(statement.get(), param++, profile.power_charging_score);
    sqlite3_bind_int(statement.get(), param++, profile.furniture_score);
    sqlite3_bind_int(statement.get(), param++, profile.home_decor_score);
    sqlite3_bind_int(statement.get(), param++, profile.storage_home_score);
    sqlite3_bind_int(statement.get(), param++, profile.cleaning_score);
    sqlite3_bind_int(statement.get(), param++, profile.home_organization_score);
    sqlite3_bind_int(statement.get(), param++, profile.skincare_score);
    sqlite3_bind_int(statement.get(), param++, profile.personal_hygiene_score);
    sqlite3_bind_int(statement.get(), param++, profile.men_fashion_score);
    sqlite3_bind_int(statement.get(), param++, profile.women_fashion_score);
    sqlite3_bind_int(statement.get(), param++, profile.children_fashion_score);
    sqlite3_bind_int(statement.get(), param++, profile.fashion_general_score);
    sqlite3_bind_int(statement.get(), param++, profile.jewelry_score);
    sqlite3_bind_int(statement.get(), param++, profile.luxury_score);
    sqlite3_bind_int(statement.get(), param++, profile.toys_score);
    sqlite3_bind_int(statement.get(), param++, profile.educational_toys_score);
    sqlite3_bind_int(statement.get(), param++, profile.games_puzzles_score);
    sqlite3_bind_int(statement.get(), param++, profile.baby_gear_score);
    sqlite3_bind_int(statement.get(), param++, profile.pet_toys_score);
    sqlite3_bind_int(statement.get(), param++, profile.pet_health_score);
    sqlite3_bind_int(statement.get(), param++, profile.car_accessories_score);
    sqlite3_bind_int(statement.get(), param++, profile.car_vehicle_score);
    sqlite3_bind_int(statement.get(), param++, profile.power_tools_score);
    sqlite3_bind_int(statement.get(), param++, profile.hand_tools_score);
    sqlite3_bind_int(statement.get(), param++, profile.industrial_score);
    sqlite3_bind_int(statement.get(), param++, profile.safety_score);
    sqlite3_bind_int(statement.get(), param++, profile.gardening_supplies_score);
    sqlite3_bind_int(statement.get(), param++, profile.outdoor_score);
    sqlite3_bind_int(statement.get(), param++, profile.camping_score);
    sqlite3_bind_int(statement.get(), param++, profile.fitness_score);
    sqlite3_bind_int(statement.get(), param++, profile.books_score);
    sqlite3_bind_int(statement.get(), param++, profile.music_instruments_score);
    sqlite3_bind_int(statement.get(), param++, profile.movies_media_score);
    sqlite3_bind_int(statement.get(), param++, profile_id);

    if (sqlite3_step(statement.get()) != SQLITE_DONE) {
        std::cerr << "SQL Error: " << sqlite3_errmsg(db.get()) << std::endl;
        return false;
    }

    return true;
}

void adjustSliders(UserProfile &profile, const std::string& user_label) {
    printDivider();
    std::cout << "      ADJUST YOUR GIFTYFY PREFERENCES" << std::endl;
    printDivider();
    renderNavigationBar("Adjust Preferences", user_label, "[A] Decrease   [S] Increase   [Enter] Confirm");
    std::cout << "\nUse A to decrease, S to increase, Enter to confirm for each category group.\n" << std::endl;
    std::cout << "Current values: 0 = not important, 1 = neutral, 2 = very important (multiplier)\n" << std::endl;
    
    renderSlider("Electronics & Tech   ", profile.electronics_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::string dummy;
    std::getline(std::cin, dummy);
    
    renderSlider("Home & Decor         ", profile.home_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Personal Care        ", profile.personal_care_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Fashion & Wearables  ", profile.wearables_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Luxury Items         ", profile.luxury_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Children & Family    ", profile.children_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Pets & Companions    ", profile.pet_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Cars & Tools         ", profile.car_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Outdoor & Fitness    ", profile.outdoor_slider);
    std::cout << "Press Enter to continue to next category: ";
    std::getline(std::cin, dummy);
    
    renderSlider("Books & Entertainment", profile.creative_slider);
}

void displayResults(const std::vector<RankedItem> &results, const std::string &profile_name, const std::string& user_label) {
    printDivider();
    std::cout << "Profile: " << profile_name << std::endl;
    printDivider();
    renderNavigationBar("Recommendations", user_label, "[1] Dashboard   [2] Profiles   [X] Exit");
    std::cout << "Best Items: " << std::endl;
    printDivider();
    std::cout << std::endl;
    
    if (results.empty()) {
        std::cout << "No items found." << std::endl;
        return;
    }
    
    size_t display_count = std::min(size_t(3), results.size());
    for (size_t i = 0; i < display_count; i++) {
        const std::string reset = esc_reset();
        const std::string purple = esc_fg(177,98,134);
        const std::string blue = esc_fg(69,133,136);
        const std::string green = esc_fg(152,151,26);
        const std::string aqua = esc_fg(104,157,106);
        const std::string yellow = esc_fg(215,153,33);

        std::cout << "[" << (i+1) << "] " << esc_bold() << purple << results[i].item_name << reset << std::endl;
        std::cout << "    " << blue << "ID: " << reset << results[i].item_id << std::endl;
        std::cout << "    " << blue << "Retailer: " << reset << results[i].retailer << std::endl;
        std::cout << "    " << green << "Price: $" << reset << std::fixed << std::setprecision(2) << results[i].price << std::endl;
        std::cout << "    " << aqua << "Link: " << reset << results[i].associate_link << std::endl;
        std::cout << "    " << yellow << "Match Score: " << esc_bold() << std::fixed << std::setprecision(2) << results[i].match_percentage << "%" << reset << std::endl;
        std::cout << std::endl;
    }
    
    printDivider();
    std::cout << "Press Enter to return to the dashboard: ";
    std::string input;
    std::getline(std::cin, input);
}

void ensureAdminExists() { //hard coded for now, but this app was meant to be run locally, so no problem
    const std::string adminUser = "admin";
    const std::string adminPass = "admin123";
    const std::string adminEmail = "FarhanIsBest@gmail.com";

    if (!usernameExists(adminUser)) {
        if (createUserAccount(adminUser, adminPass, adminEmail, true)) {
            std::cout << "Admin account created: " << adminUser << std::endl;
        } else {
            std::cerr << "Failed to create admin account." << std::endl;
        }
        return;
    }

    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database for admin bootstrap." << std::endl;
        return;
    }

    char* error_message = nullptr;
    if (sqlite3_exec(db.get(),
            "UPDATE users_login SET password_ = 'admin123', email_ = 'FarhanIsBest@gmail.com', is_admin = 1 WHERE username_ = 'admin';",
            nullptr,
            nullptr,
            &error_message) != SQLITE_OK) {
        std::cerr << "Failed to update admin account: "
                  << (error_message ? error_message : sqlite3_errmsg(db.get())) << std::endl;
        if (error_message) {
            sqlite3_free(error_message);
        }
        return;
    }
    if (error_message) {
        sqlite3_free(error_message);
    }
}

UserProfile selectOrCreateProfile(int user_id, UserAccount &user) {
    while (true) {
        clearScreen();
        printDivider();
        std::cout << "Loading preferences for: " << user.username << std::endl;
        printDivider();
        std::string actions = "[N] Create Profile   [X] Exit";
        if (user.is_admin) {
            actions = "[A] Admin Console   " + actions;
        }
        actions += "   [L] Logout";
        renderNavigationBar("Profile Selection", buildUserLabel(user), actions);
        std::cout << std::endl;
        
        std::vector<UserProfile> profiles = getUserProfiles(user_id);
        
        std::cout << "Select a profile:" << std::endl;
        for (size_t i = 0; i < profiles.size(); i++) {
            std::cout << "[" << (i+1) << "] " << profiles[i].name << std::endl;
        }
        if (user.is_admin) {
            std::cout << "[A] Admin Console / SQL Tools" << std::endl;
        }
        std::cout << "[N] Create Profile" << std::endl;
        std::cout << "[L] Logout" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        printDivider();
        std::cout << "Select an option: ";
        
        std::string choice;
        std::getline(std::cin, choice);
        
        if (choice == "X" || choice == "x") {
            std::cout << "Thank you for using Giftyfy. Goodbye!" << std::endl;
            exit(0);
        } else if (choice == "L" || choice == "l") {
            UserProfile empty;
            empty.profile_id = -1;
            clearScreen();
            return empty;
        } else if ((choice == "A" || choice == "a") && user.is_admin) {
            runAdminConsole(user);
        } else if (choice == "N" || choice == "n") {
            std::cout << "Enter new profile name: ";
            std::string profile_name;
            std::getline(std::cin, profile_name);
            
            if (createNewProfile(user_id, profile_name)) {
                clearScreen();
                std::cout << "Profile created successfully!" << std::endl;
                continue;
            } else {
                std::cout << "Failed to create profile." << std::endl;
                continue;
            }
        } else {
            try {
                int selection = std::stoi(choice) - 1;
                if (selection >= 0 && selection < (int)profiles.size()) {
                    UserProfile selected = loadUserPreferences(profiles[selection].profile_id, user_id);
                    clearScreen();
                    return selected;
                } else {
                    clearScreen();
                    std::cout << "Invalid selection. Please try again." << std::endl;
                }
            } catch (...) {
                clearScreen();
                std::cout << "Invalid option. Please try again." << std::endl;
            }
        }
    }
}

std::vector<Item> loadItemsFromDatabase() {
    std::vector<Item> items;
    
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database for loading items." << std::endl;
        return items;
    }
    
    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(),
            "SELECT item_id, item_name, retailer, associate_link, price, "
            "computing_devices_score, peripherals_score, displays_score, storage_electronics_score, "
            "audio_score, video_score, wearables_tech_score, accessories_electronics_score, power_charging_score, "
            "furniture_score, home_decor_score, storage_home_score, cleaning_score, home_organization_score, "
            "skincare_score, personal_hygiene_score, "
            "men_fashion_score, women_fashion_score, children_fashion_score, fashion_general_score, "
            "jewelry_score, luxury_score, "
            "toys_score, educational_toys_score, games_puzzles_score, baby_gear_score, "
            "pet_toys_score, pet_health_score, "
            "car_accessories_score, car_vehicle_score, "
            "power_tools_score, hand_tools_score, industrial_score, safety_score, "
            "gardening_supplies_score, outdoor_score, camping_score, fitness_score, "
            "books_score, music_instruments_score, movies_media_score "
            "FROM items",
            statement)) {
        std::cerr << "Failed to prepare query for loading items." << std::endl;
        return items;
    }
    
    while (sqlite3_step(statement.get()) == SQLITE_ROW) {
        Item item;
        item.item_id = sqlite3_column_int(statement.get(), 0);
        item.item_name = getSqliteText(statement.get(), 1);
        item.retailer = getSqliteText(statement.get(), 2);
        item.associate_link = getSqliteText(statement.get(), 3);
        item.price = sqlite3_column_double(statement.get(), 4);
        
        // Bug fix: the recommender used to normalize only the user side, which made
        // item scores and quiz answers live on different scales and skewed results.
        // Keep item scores on the same 0-255 scale as the stored quiz answers.
        for (int i = 0; i < NUM_CATEGORIES; i++) {
            item.scores[i] = sqlite3_column_double(statement.get(), 5 + i);
        }
        
        items.push_back(item);
    }
    
    if (items.empty()) {
        std::cout << "Warning: No items found in database. Please populate the items table." << std::endl;
    }
    
    return items;
}

std::vector<RankedItem> buildRecommendations(const UserProfile& user_profile) {
    double weights[NUM_CATEGORIES];
    double user_vector[NUM_CATEGORIES];

    weights[0] = user_profile.computing_devices_score * user_profile.electronics_slider;
    weights[1] = user_profile.peripherals_score * user_profile.electronics_slider;
    weights[2] = user_profile.displays_score * user_profile.electronics_slider;
    weights[3] = user_profile.storage_electronics_score * user_profile.electronics_slider;
    weights[4] = user_profile.audio_score * user_profile.electronics_slider;
    weights[5] = user_profile.video_score * user_profile.electronics_slider;
    weights[6] = user_profile.wearables_tech_score * user_profile.electronics_slider;
    weights[7] = user_profile.accessories_electronics_score * user_profile.electronics_slider;
    weights[8] = user_profile.power_charging_score * user_profile.electronics_slider;

    weights[9] = user_profile.furniture_score * user_profile.home_slider;
    weights[10] = user_profile.home_decor_score * user_profile.home_slider;
    weights[11] = user_profile.storage_home_score * user_profile.home_slider;
    weights[12] = user_profile.cleaning_score * user_profile.home_slider;
    weights[13] = user_profile.home_organization_score * user_profile.home_slider;

    weights[14] = user_profile.skincare_score * user_profile.personal_care_slider;
    weights[15] = user_profile.personal_hygiene_score * user_profile.personal_care_slider;

    weights[16] = user_profile.men_fashion_score * user_profile.wearables_slider;
    weights[17] = user_profile.women_fashion_score * user_profile.wearables_slider;
    weights[18] = user_profile.children_fashion_score * user_profile.wearables_slider;
    weights[19] = user_profile.fashion_general_score * user_profile.wearables_slider;

    weights[20] = user_profile.jewelry_score * user_profile.luxury_slider;
    weights[21] = user_profile.luxury_score * user_profile.luxury_slider;

    weights[22] = user_profile.toys_score * user_profile.children_slider;
    weights[23] = user_profile.educational_toys_score * user_profile.children_slider;
    weights[24] = user_profile.games_puzzles_score * user_profile.children_slider;
    weights[25] = user_profile.baby_gear_score * user_profile.children_slider;

    weights[26] = user_profile.pet_toys_score * user_profile.pet_slider;
    weights[27] = user_profile.pet_health_score * user_profile.pet_slider;

    weights[28] = user_profile.car_accessories_score * user_profile.car_slider;
    weights[29] = user_profile.car_vehicle_score * user_profile.car_slider;
    weights[30] = user_profile.power_tools_score * user_profile.car_slider;
    weights[31] = user_profile.hand_tools_score * user_profile.car_slider;
    weights[32] = user_profile.industrial_score * user_profile.car_slider;
    weights[33] = user_profile.safety_score * user_profile.car_slider;

    weights[34] = user_profile.gardening_supplies_score * user_profile.outdoor_slider;
    weights[35] = user_profile.outdoor_score * user_profile.outdoor_slider;
    weights[36] = user_profile.camping_score * user_profile.outdoor_slider;
    weights[37] = user_profile.fitness_score * user_profile.outdoor_slider;
    weights[38] = user_profile.books_score * user_profile.creative_slider;
    weights[39] = user_profile.music_instruments_score * user_profile.creative_slider;
    weights[40] = user_profile.movies_media_score * user_profile.creative_slider;

    for (int i = 0; i < NUM_CATEGORIES; i++) {
        user_vector[i] = weights[i];
    }

    std::vector<Item> database = loadItemsFromDatabase();
    // Keep a max-heap by distance so top() is the current worst kept result.
    // Then, a better candidate (smaller distance) can replace it.
    std::priority_queue<RankedItem, std::vector<RankedItem>, RankedItemWorseDistanceFirst> top_items;

    // Use a weighted Euclidean distance on normalized scores.
    // - Normalize user_vector to [0,1] by dividing by max possible (255*2 = 510).
    // - Normalize item scores to [0,1] by dividing by 255.
    // - Compute per-dimension weights from the user_vector; normalize them to sum=1 when possible.
    // - Distance D = sqrt( sum_i w_i * (u_i_norm - v_i_norm)^2 ).
    // - Normalize by D_max = sqrt( sum_i w_i * max_diff_i^2 ), where max_diff_i = max(u_i_norm, 1-u_i_norm).
    // - match_pct = (1 - D / D_max) * 100.

    const double max_user_score = 255.0 * 2.0; // 510

    // Precompute normalized user vector and raw weights
    double normalized_user[NUM_CATEGORIES];
    double raw_weights[NUM_CATEGORIES];
    double sum_raw_weights = 0.0;
    for (int i = 0; i < NUM_CATEGORIES; i++) {
        normalized_user[i] = user_vector[i] / max_user_score;
        raw_weights[i] = user_vector[i];
        sum_raw_weights += raw_weights[i];
    }

    for (const Item& item : database) {
        double normalized_item[NUM_CATEGORIES];
        for (int i = 0; i < NUM_CATEGORIES; i++) normalized_item[i] = item.scores[i] / 255.0;

        // Normalize weights to sum=1 unless all weights are zero
        double weights_norm[NUM_CATEGORIES];
        if (sum_raw_weights > 0.0) {
            for (int i = 0; i < NUM_CATEGORIES; i++) weights_norm[i] = raw_weights[i] / sum_raw_weights;
        } else {
            for (int i = 0; i < NUM_CATEGORIES; i++) weights_norm[i] = 1.0 / (double)NUM_CATEGORIES;
        }

        double d_sq = 0.0;
        double d_max_sq = 0.0;
        for (int i = 0; i < NUM_CATEGORIES; i++) {
            double diff = normalized_user[i] - normalized_item[i];
            d_sq += weights_norm[i] * (diff * diff);

            double max_diff = std::max(normalized_user[i], 1.0 - normalized_user[i]);
            d_max_sq += weights_norm[i] * (max_diff * max_diff);
        }

        double D = std::sqrt(d_sq);
        double D_max = std::sqrt(d_max_sq);

        double match_pct = 0.0;
        double distance_metric = 1.0;
        if (D_max <= 0.0) {
            match_pct = (D <= 0.0) ? 100.0 : 0.0;
            distance_metric = (D <= 0.0) ? 0.0 : 1.0;
        } else {
            match_pct = (1.0 - (D / D_max)) * 100.0;
            if (match_pct < 0.0) match_pct = 0.0;
            if (match_pct > 100.0) match_pct = 100.0;
            distance_metric = D / D_max;
        }

        if (top_items.size() < TOP_N_ITEMS) {
            top_items.push({item.item_id, item.item_name, item.retailer,
                           item.associate_link, item.price, distance_metric, match_pct});
        } else if (distance_metric < top_items.top().distance_squared) {
            top_items.pop();
            top_items.push({item.item_id, item.item_name, item.retailer,
                           item.associate_link, item.price, distance_metric, match_pct});
        }
    }

    std::vector<RankedItem> results;
    while (!top_items.empty()) {
        results.push_back(top_items.top());
        top_items.pop();
    }

    // Ensure results are ordered best-to-worst by match percentage
    std::sort(results.begin(), results.end(), [](const RankedItem &a, const RankedItem &b) {
        return a.match_percentage > b.match_percentage;
    });
    // this was added due to a annoying items flooding the top list due to sheer volume
    // Filter out items with no meaningful match (0%). If filtering removes everything,
    // fall back to the original results so the UI can still show something.
    std::vector<RankedItem> filtered;
    const double MATCH_THRESHOLD = 0.0001; // treat extremely small values as zero
    for (const auto &r : results) {
        if (r.match_percentage > MATCH_THRESHOLD) filtered.push_back(r);
    }

    if (!filtered.empty()) return filtered;
    return results;
}

bool displayQueryResults(const std::string& title, const std::string& query) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database." << std::endl;
        return false;
    }

    SqliteStmtPtr statement(nullptr, sqlite3_finalize);
    if (!prepareSqliteStatement(db.get(), query, statement)) {
        std::cerr << "Failed to prepare query." << std::endl;
        return false;
    }

    int column_count = sqlite3_column_count(statement.get());
    std::vector<std::string> column_names;
    column_names.reserve(column_count);
    for (int i = 0; i < column_count; i++) {
        column_names.push_back(sqlite3_column_name(statement.get(), i));
    }

    std::vector<std::vector<std::string>> rows;
    while (sqlite3_step(statement.get()) == SQLITE_ROW) {
        std::vector<std::string> row;
        row.reserve(column_count);
        for (int i = 0; i < column_count; i++) {
            row.push_back(getSqliteValue(statement.get(), i));
        }
        rows.push_back(std::move(row));
    }

    const std::size_t PAGE_SIZE = 12;
    std::size_t total_pages = rows.empty() ? 1 : (rows.size() + PAGE_SIZE - 1) / PAGE_SIZE;

    for (std::size_t page = 0; page < total_pages; ++page) {
        std::size_t start_row = page * PAGE_SIZE;
        std::size_t end_row = std::min(rows.size(), start_row + PAGE_SIZE);

        clearScreen();
        renderCompactQueryTable(title, column_names, rows, start_row, end_row, page + 1, total_pages);

        if (page + 1 < total_pages) {
            std::cout << "Press Enter for next page or B to go back: ";
            std::string choice;
            std::getline(std::cin, choice);
            if (choice == "B" || choice == "b") {
                clearScreen();
                break;
            }
        } else {
            std::cout << "Press Enter to return: ";
            std::string choice;
            std::getline(std::cin, choice);
        }
    }

    return true;
}

bool executeAdminSql(const std::string& sql) {
    SqliteDbPtr db(getDBConnection(), sqlite3_close);
    if (!db) {
        std::cerr << "Failed to connect to database." << std::endl;
        return false;
    }

    char* error_message = nullptr;
    if (sqlite3_exec(db.get(), sql.c_str(), nullptr, nullptr, &error_message) != SQLITE_OK) {
        std::cerr << "SQL Error: "
                  << (error_message ? error_message : sqlite3_errmsg(db.get())) << std::endl;
        if (error_message) {
            sqlite3_free(error_message);
        }
        return false;
    }

    if (error_message) {
        sqlite3_free(error_message);
    }

    std::cout << "SQL executed successfully." << std::endl;
    return true;
}

std::string trimCopy(const std::string& input) {
    size_t start = input.find_first_not_of(" \t\r\n");
    if (start == std::string::npos) {
        return "";
    }

    size_t end = input.find_last_not_of(" \t\r\n");
    return input.substr(start, end - start + 1);
}

bool isAllowedAdminQuery(const std::string& query) {
    std::string trimmed = trimCopy(query);
    if (trimmed.empty()) {
        return false;
    }

    std::string upper = trimmed;
    std::transform(upper.begin(), upper.end(), upper.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });

    if (upper.rfind("SELECT", 0) != 0) { //theoretically they can select 1; drop table * (⊙_⊙). but who cares
        return false;
    }

    return true;
}

void runAdminQueryConsole(const UserAccount& user) {
    while (true) {
        clearScreen();
        renderNavigationBar("Admin Query Runner", buildUserLabel(user), "[1] users_login   [2] user_profiles   [3] items   [4] sales   [5] Custom SELECT   [B] Back   [X] Exit");
        std::cout << "Run read-only queries against the database." << std::endl;
        std::cout << "[1] users_login" << std::endl;
        std::cout << "[2] user_profiles" << std::endl;
        std::cout << "[3] items" << std::endl;
        std::cout << "[4] sales" << std::endl;
        std::cout << "[5] Custom SELECT query" << std::endl;
        std::cout << "[B] Back to admin menu" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        std::cout << "Select an option: ";

        std::string choice;
        std::getline(std::cin, choice);

        if (choice == "1" || choice == "2" || choice == "3" || choice == "4") {
            std::string table_name;
            if (choice == "1") {
                table_name = "users_login";
            } else if (choice == "2") {
                table_name = "user_profiles";
            } else if (choice == "3") {
                table_name = "items";
            } else {
                table_name = "sales";
            }

            std::cout << "Enter optional SQL clause after the table name (blank for all rows)." << std::endl;
            std::cout << "Example: WHERE user_id = 1 ORDER BY profile_id DESC LIMIT 10" << std::endl;
            std::cout << "Clause: ";
            std::string clause;
            std::getline(std::cin, clause);

            std::string query = "SELECT * FROM " + table_name;
            if (!trimCopy(clause).empty()) {
                query += " ";
                query += clause;
            }

            if (!displayQueryResults(table_name, query)) {
                std::cout << "Query failed." << std::endl;
            }

            std::cout << "Press Enter to return: ";
            std::getline(std::cin, choice);
        } else if (choice == "5") {
            std::cout << "Enter a read-only SELECT query." << std::endl;
            std::cout << "It may reference any table in the database." << std::endl;
            std::cout << "Query: ";
            std::string query;
            std::getline(std::cin, query);

            if (!isAllowedAdminQuery(query)) {
                std::cout << "Only SELECT queries are allowed." << std::endl;
            } else if (!displayQueryResults("Custom Query", query)) {
                std::cout << "Query failed." << std::endl;
            }

            std::cout << "Press Enter to return: ";
            std::getline(std::cin, choice);
        } else if (choice == "B" || choice == "b") {
            clearScreen();
            return;
        } else if (choice == "X" || choice == "x") {
            exit(0);
        } else {
            std::cout << "Invalid option. Please try again." << std::endl;
            std::cout << "Press Enter to continue: ";
            std::getline(std::cin, choice);
        }
    }
}

void runAdminSqlConsole(const UserAccount& user) {
    while (true) {
        clearScreen();
        renderNavigationBar("Admin SQL Console", buildUserLabel(user), "[1] Execute SQL   [B] Back   [X] Exit");
        std::cout << "Run SQL statements such as CREATE TABLE, INSERT, UPDATE, DELETE, or ALTER." << std::endl;
        std::cout << "[1] Execute SQL statement" << std::endl;
        std::cout << "[B] Back to admin menu" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        std::cout << "Select an option: ";

        std::string choice;
        std::getline(std::cin, choice);

        if (choice == "1") {
            std::cout << "Enter SQL statement or script." << std::endl;
            std::cout << "Example: CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);" << std::endl;
            std::cout << "SQL: ";
            std::string sql;
            std::getline(std::cin, sql);

            if (trimCopy(sql).empty()) {
                std::cout << "No SQL entered." << std::endl;
            } else if (!executeAdminSql(sql)) {
                std::cout << "SQL execution failed." << std::endl;
            }

            std::cout << "Press Enter to return: ";
            std::getline(std::cin, choice);
        } else if (choice == "B" || choice == "b") {
            clearScreen();
            return;
        } else if (choice == "X" || choice == "x") {
            exit(0);
        } else {
            std::cout << "Invalid option. Please try again." << std::endl;
            std::cout << "Press Enter to continue: ";
            std::getline(std::cin, choice);
        }
    }
}

void runAdminConsole(const UserAccount& user) {
    while (true) {
        clearScreen();
        renderNavigationBar("Admin Console", buildUserLabel(user), "[1] Query / Table Viewer   [2] SQL Console   [B] Back   [X] Exit");
        std::cout << "Choose an admin tool." << std::endl;
        std::cout << "[1] Query / Table Viewer" << std::endl;
        std::cout << "[2] SQL Console" << std::endl;
        std::cout << "[B] Back to dashboard" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        std::cout << "Select an option: ";

        std::string choice;
        std::getline(std::cin, choice);

        if (choice == "1") {
            runAdminQueryConsole(user);
        } else if (choice == "2") {
            runAdminSqlConsole(user);
        } else if (choice == "B" || choice == "b") {
            clearScreen();
            return;
        } else if (choice == "X" || choice == "x") {
            exit(0);
        } else {
            std::cout << "Invalid option. Please try again." << std::endl;
            std::cout << "Press Enter to continue: ";
            std::getline(std::cin, choice);
        }
    }
}

void runUserSession(UserAccount current_user) {
    UserProfile user_profile = selectOrCreateProfile(current_user.user_id, current_user);

    if (user_profile.profile_id == -1) {
        return;
    }

    while (true) {
        // Check if profile is new (all category scores are 0)
        int score_sum = user_profile.computing_devices_score + user_profile.peripherals_score +
                       user_profile.displays_score + user_profile.storage_electronics_score +
                       user_profile.audio_score + user_profile.video_score + user_profile.wearables_tech_score +
                       user_profile.accessories_electronics_score + user_profile.power_charging_score +
                       user_profile.furniture_score + user_profile.home_decor_score + user_profile.storage_home_score +
                       user_profile.cleaning_score + user_profile.home_organization_score + user_profile.skincare_score +
                       user_profile.personal_hygiene_score + user_profile.men_fashion_score + user_profile.women_fashion_score +
                       user_profile.children_fashion_score + user_profile.fashion_general_score + user_profile.jewelry_score +
                       user_profile.luxury_score + user_profile.toys_score + user_profile.educational_toys_score +
                       user_profile.games_puzzles_score + user_profile.baby_gear_score + user_profile.pet_toys_score +
                       user_profile.pet_health_score + user_profile.car_accessories_score + user_profile.car_vehicle_score +
                       user_profile.power_tools_score + user_profile.hand_tools_score + user_profile.industrial_score +
                       user_profile.safety_score + user_profile.gardening_supplies_score + user_profile.outdoor_score +
                       user_profile.camping_score + user_profile.fitness_score + user_profile.books_score +
                       user_profile.music_instruments_score + user_profile.movies_media_score;

        if (score_sum == 0) {
            std::cout << "\nIt looks like this is a new profile. Let's set it up!" << std::endl;
            runQuiz(user_profile, buildUserLabel(current_user));
            adjustSliders(user_profile, buildUserLabel(current_user));

            if (saveProfileScores(user_profile.profile_id, current_user.user_id, user_profile)) {
                std::cout << "Profile preferences saved successfully!" << std::endl;
            } else {
                std::cout << "Error saving profile preferences." << std::endl;
            }
        }

        clearScreen();
        std::string dashboard_actions = "[1] Recommendations   [2] Edit Preferences   [3] Switch Profile";
        if (current_user.is_admin) {
            dashboard_actions += "   [4] Admin Console";
        }
        dashboard_actions += "   [L] Logout   [X] Exit";
        renderNavigationBar("Dashboard", buildUserLabel(current_user), dashboard_actions);
        std::cout << "Active profile: " << user_profile.name << std::endl;
        std::cout << std::endl;
        std::cout << "[1] View recommendations" << std::endl;
        std::cout << "[2] Edit preferences" << std::endl;
        std::cout << "[3] Switch profile" << std::endl;
        if (current_user.is_admin) {
            std::cout << "[4] Admin console" << std::endl;
        }
        std::cout << "[L] Logout" << std::endl;
        std::cout << "[X] Exit" << std::endl;
        std::cout << std::endl;
        std::cout << "Select an option: ";

        std::string choice;
        std::getline(std::cin, choice);

        if (choice == "1") {
            std::vector<RankedItem> results = buildRecommendations(user_profile);
            displayResults(results, user_profile.name, buildUserLabel(current_user));
        } else if (choice == "2") {
            runQuiz(user_profile, buildUserLabel(current_user));
            adjustSliders(user_profile, buildUserLabel(current_user));

            if (saveProfileScores(user_profile.profile_id, current_user.user_id, user_profile)) {
                std::cout << "Profile preferences saved successfully!" << std::endl;
            } else {
                std::cout << "Error saving profile preferences." << std::endl;
            }
            std::cout << "Press Enter to return to the dashboard: ";
            std::getline(std::cin, choice);
        } else if (choice == "3") {
            user_profile = selectOrCreateProfile(current_user.user_id, current_user);
            if (user_profile.profile_id == -1) {
                return;
            }
        } else if (choice == "4" && current_user.is_admin) {
            runAdminConsole(current_user);
        } else if (choice == "L" || choice == "l") {
            return;
        } else if (choice == "X" || choice == "x") {
            exit(0);
        } else {
            std::cout << "Invalid option. Please try again." << std::endl;
            std::cout << "Press Enter to continue: ";
            std::getline(std::cin, choice);
        }
    }
}

int main() {
    clearScreen();
    ensureAdminExists();
    while (true) {
        clearScreen();
        UserAccount current_user = handleAuthentication();
        runUserSession(current_user);
    }

    return 0;
}
