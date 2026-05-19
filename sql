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