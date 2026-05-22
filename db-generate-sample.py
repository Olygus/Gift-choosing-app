from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timedelta


SCORE_COLS = [
    "computing_devices_score",
    "peripherals_score",
    "displays_score",
    "storage_electronics_score",
    "audio_score",
    "video_score",
    "wearables_tech_score",
    "accessories_electronics_score",
    "power_charging_score",
    "furniture_score",
    "home_decor_score",
    "storage_home_score",
    "cleaning_score",
    "home_organization_score",
    "skincare_score",
    "personal_hygiene_score",
    "men_fashion_score",
    "women_fashion_score",
    "children_fashion_score",
    "fashion_general_score",
    "jewelry_score",
    "luxury_score",
    "toys_score",
    "educational_toys_score",
    "games_puzzles_score",
    "baby_gear_score",
    "pet_toys_score",
    "pet_health_score",
    "car_accessories_score",
    "car_vehicle_score",
    "power_tools_score",
    "hand_tools_score",
    "industrial_score",
    "safety_score",
    "gardening_supplies_score",
    "outdoor_score",
    "camping_score",
    "fitness_score",
    "books_score",
    "music_instruments_score",
    "movies_media_score",
]

SLIDER_COLS = [
    "electronics_slider",
    "home_slider",
    "personal_care_slider",
    "wearables_slider",
    "luxury_slider",
    "children_slider",
    "pet_slider",
    "car_slider",
    "outdoor_slider",
    "creative_slider",
]

PROFILE_COLS = ["profile_id", "name_", "user_id", *SCORE_COLS, *SLIDER_COLS]
ITEM_COLS = ["item_id", "item_name", "retailer", "associate_link", "price", *SCORE_COLS]

ADMIN_USER_ID = 1
ADMIN_PROFILE_ID = 1


def slugify(text: str) -> str:
    text = text.lower().replace("&", "and")
    chars = []
    for char in text:
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-", "/"}:
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def link_for(retailer: str, name: str) -> str:
    slug = slugify(name)
    if retailer == "Amazon":
        return f"https://www.amazon.com/s?k={slug}"
    if retailer == "Best Buy":
        return f"https://www.bestbuy.com/site/searchpage.jsp?st={slug}"
    if retailer == "B&H Photo":
        return f"https://www.bhphotovideo.com/c/search?Ntt={slug}"
    if retailer == "Apple Store":
        return f"https://www.apple.com/us/search/{slug}"
    if retailer == "Target":
        return f"https://www.target.com/s?searchTerm={slug}"
    if retailer == "Walmart":
        return f"https://www.walmart.com/search?q={slug}"
    if retailer == "Wayfair":
        return f"https://www.wayfair.com/keyword.php?keyword={slug}"
    if retailer == "IKEA":
        return f"https://www.ikea.com/us/en/search/?q={slug}"
    if retailer == "Sephora":
        return f"https://www.sephora.com/search?keyword={slug}"
    if retailer == "Ulta":
        return f"https://www.ulta.com/search?search={slug}"
    if retailer == "Nordstrom":
        return f"https://www.nordstrom.com/sr?keyword={slug}"
    if retailer == "Macy's":
        return f"https://www.macys.com/shop/featured/{slug}"
    if retailer == "Zara":
        return f"https://www.zara.com/us/en/search?searchTerm={slug}"
    if retailer == "H&M":
        return f"https://www2.hm.com/en_us/search-results.html?q={slug}"
    if retailer == "Uniqlo":
        return f"https://www.uniqlo.com/us/en/search/?q={slug}"
    if retailer == "Tiffany & Co.":
        return f"https://www.tiffany.com/search/?q={slug}"
    if retailer == "Cartier":
        return f"https://www.cartier.com/en-us/search/?q={slug}"
    if retailer == "Saks Fifth Avenue":
        return f"https://www.saksfifthavenue.com/search?keyword={slug}"
    if retailer == "Neiman Marcus":
        return f"https://www.neimanmarcus.com/search.jsp?Ntt={slug}"
    if retailer == "LEGO":
        return f"https://www.lego.com/en-us/search?q={slug}"
    if retailer == "Melissa & Doug":
        return f"https://www.melissaanddoug.com/search?q={slug}"
    if retailer == "Pottery Barn Kids":
        return f"https://www.potterybarnkids.com/search/results.html?words={slug}"
    if retailer == "Chewy":
        return f"https://www.chewy.com/s?query={slug}"
    if retailer == "Petco":
        return f"https://www.petco.com/shop/en/petcostore/search?query={slug}"
    if retailer == "AutoZone":
        return f"https://www.autozone.com/searchresult?searchText={slug}"
    if retailer == "Advance Auto Parts":
        return f"https://shop.advanceautoparts.com/web/SearchResults?searchTerm={slug}"
    if retailer == "Home Depot":
        return f"https://www.homedepot.com/s/{slug}"
    if retailer == "Lowe's":
        return f"https://www.lowes.com/search?searchTerm={slug}"
    if retailer == "Harbor Freight":
        return f"https://www.harborfreight.com/search?q={slug}"
    if retailer == "REI":
        return f"https://www.rei.com/search?q={slug}"
    if retailer == "Dick's Sporting Goods":
        return f"https://www.dickssportinggoods.com/search/SearchDisplay?searchTerm={slug}"
    if retailer == "Barnes & Noble":
        return f"https://www.barnesandnoble.com/s/{slug}"
    if retailer == "Guitar Center":
        return f"https://www.guitarcenter.com/search?typeAheadSuggestion=true&Ntt={slug}"
    if retailer == "Sweetwater":
        return f"https://www.sweetwater.com/store/search?s={slug}"
    if retailer == "Criterion":
        return f"https://www.criterion.com/search?q={slug}"
    if retailer == "Sony":
        return f"https://electronics.sony.com/search?q={slug}"
    if retailer == "Logitech":
        return f"https://www.logitech.com/en-us/search.html?q={slug}"
    if retailer == "Anker":
        return f"https://www.anker.com/search?q={slug}"
    if retailer == "Samsung":
        return f"https://www.samsung.com/us/search/{slug}/"
    if retailer == "Canon":
        return f"https://www.usa.canon.com/search?query={slug}"
    if retailer == "Dell":
        return f"https://www.dell.com/en-us/search/{slug}"
    raise ValueError(f"Unsupported retailer: {retailer}")


GROUPS = [
    {
        "focus": "electronics_slider",
        "score": "computing_devices_score",
        "subtypes": [
            ("Gaming Laptop", "Dell", 1499.00, 699.00, 1099.00),
            ("Mechanical Keyboard", "Logitech", 249.00, 49.00, 129.00),
            ("4K Monitor", "B&H Photo", 449.00, 129.00, 239.00),
            ("Portable SSD", "Samsung", 199.00, 59.00, 119.00),
            ("Noise-Canceling Headphones", "Sony", 349.00, 79.00, 179.00),
            ("Mirrorless Camera", "Canon", 1299.00, 399.00, 799.00),
            ("Smartwatch", "Apple Store", 499.00, 129.00, 249.00),
            ("Power Bank", "Anker", 129.00, 29.00, 69.00),
            ("Wireless Mouse", "Best Buy", 99.00, 24.00, 49.00),
            ("USB-C Hub", "Amazon", 139.00, 39.00, 79.00),
        ],
    },
    {
        "focus": "home_slider",
        "score": "furniture_score",
        "subtypes": [
            ("Sectional Sofa", "Wayfair", 1499.00, 499.00, 899.00),
            ("Coffee Table", "IKEA", 399.00, 99.00, 189.00),
            ("Bookshelf", "IKEA", 249.00, 79.00, 149.00),
            ("Air Purifier", "Target", 299.00, 89.00, 169.00),
            ("Storage Baskets", "Walmart", 79.00, 19.00, 39.00),
            ("Table Lamp", "Wayfair", 169.00, 29.00, 69.00),
            ("Throw Rug", "Home Depot", 219.00, 59.00, 119.00),
            ("Dresser", "Wayfair", 699.00, 199.00, 399.00),
            ("Vacuum Cleaner", "Target", 449.00, 129.00, 249.00),
            ("Closet Organizer", "Amazon", 129.00, 39.00, 79.00),
        ],
    },
    {
        "focus": "personal_care_slider",
        "score": "skincare_score",
        "subtypes": [
            ("Vitamin C Serum", "Sephora", 89.00, 19.00, 39.00),
            ("Facial Moisturizer", "Ulta", 79.00, 15.00, 35.00),
            ("Electric Toothbrush", "Target", 149.00, 29.00, 69.00),
            ("Hair Dryer", "Walmart", 129.00, 24.00, 59.00),
            ("Shaving Kit", "Amazon", 99.00, 19.00, 49.00),
            ("Face Mask Set", "Sephora", 59.00, 12.00, 29.00),
            ("Body Lotion", "Ulta", 49.00, 10.00, 25.00),
            ("Beard Trimmer", "Target", 119.00, 25.00, 55.00),
            ("Cleansing Brush", "Amazon", 129.00, 29.00, 69.00),
            ("Travel Grooming Kit", "Walmart", 89.00, 18.00, 39.00),
        ],
    },
    {
        "focus": "wearables_slider",
        "score": "men_fashion_score",
        "subtypes": [
            ("Tailored Blazer", "Nordstrom", 229.00, 59.00, 129.00),
            ("Silk Dress", "Macy's", 279.00, 69.00, 159.00),
            ("Kids Winter Jacket", "Target", 219.00, 49.00, 119.00),
            ("Unisex Hoodie", "H&M", 169.00, 39.00, 89.00),
            ("Leather Sneakers", "Zara", 199.00, 59.00, 129.00),
            ("Cashmere Sweater", "Uniqlo", 239.00, 69.00, 149.00),
            ("Chino Pants", "Nordstrom", 179.00, 49.00, 99.00),
            ("Midi Skirt", "Macy's", 189.00, 49.00, 109.00),
            ("Graphic Tee", "H&M", 129.00, 29.00, 69.00),
            ("Formal Shirt", "Uniqlo", 169.00, 39.00, 89.00),
        ],
    },
    {
        "focus": "luxury_slider",
        "score": "jewelry_score",
        "subtypes": [
            ("Diamond Pendant", "Tiffany & Co.", 3999.00, 799.00, 1599.00),
            ("Gold Bracelet", "Cartier", 2999.00, 699.00, 1499.00),
            ("Designer Handbag", "Saks Fifth Avenue", 3999.00, 1499.00, 2199.00),
            ("Luxury Watch", "Neiman Marcus", 6999.00, 1999.00, 3499.00),
            ("Pearl Earrings", "Tiffany & Co.", 2299.00, 599.00, 1299.00),
            ("Silk Scarf", "Cartier", 899.00, 249.00, 499.00),
            ("Cufflinks Set", "Saks Fifth Avenue", 1299.00, 399.00, 789.00),
            ("Leather Wallet", "Neiman Marcus", 1599.00, 499.00, 899.00),
            ("Crystal Necklace", "Tiffany & Co.", 2499.00, 499.00, 1199.00),
            ("Premium Fragrance", "Cartier", 1299.00, 299.00, 699.00),
        ],
    },
    {
        "focus": "children_slider",
        "score": "toys_score",
        "subtypes": [
            ("STEM Robot Kit", "LEGO", 229.00, 69.00, 129.00),
            ("Building Blocks Set", "LEGO", 199.00, 49.00, 109.00),
            ("Board Game Bundle", "Target", 179.00, 39.00, 89.00),
            ("Baby Stroller", "Pottery Barn Kids", 799.00, 99.00, 159.00),
            ("Plush Toy", "Melissa & Doug", 129.00, 29.00, 69.00),
            ("Puzzle Mat", "Walmart", 149.00, 29.00, 79.00),
            ("Montessori Shape Sorter", "Amazon", 169.00, 39.00, 89.00),
            ("Ride-On Car", "Target", 219.00, 59.00, 119.00),
            ("Teething Ring", "Pottery Barn Kids", 89.00, 19.00, 39.00),
            ("Night Light Projector", "Melissa & Doug", 129.00, 29.00, 69.00),
        ],
    },
    {
        "focus": "pet_slider",
        "score": "pet_health_score",
        "subtypes": [
            ("Automatic Feeder", "Chewy", 229.00, 69.00, 129.00),
            ("Orthopedic Pet Bed", "Petco", 199.00, 59.00, 119.00),
            ("Cat Wand Toy", "Chewy", 99.00, 19.00, 49.00),
            ("Dog Chew Toy", "Petco", 89.00, 15.00, 39.00),
            ("Self-Cleaning Litter Box", "Amazon", 999.00, 99.00, 179.00),
            ("Grooming Kit", "Chewy", 149.00, 39.00, 79.00),
            ("Treat Puzzle", "Petco", 129.00, 29.00, 69.00),
            ("GPS Collar", "Amazon", 219.00, 59.00, 119.00),
            ("Pet Water Fountain", "Chewy", 169.00, 39.00, 89.00),
            ("Travel Carrier", "Petco", 189.00, 49.00, 99.00),
        ],
    },
    {
        "focus": "car_slider",
        "score": "car_accessories_score",
        "subtypes": [
            ("Dash Camera", "AutoZone", 229.00, 69.00, 129.00),
            ("Roof Cargo Box", "Advance Auto Parts", 799.00, 149.00, 219.00),
            ("Seat Cover Set", "Walmart", 129.00, 29.00, 69.00),
            ("Tire Inflator", "AutoZone", 179.00, 39.00, 99.00),
            ("Car Vacuum", "Amazon", 149.00, 39.00, 79.00),
            ("Phone Mount", "Target", 89.00, 19.00, 39.00),
            ("Jump Starter", "Advance Auto Parts", 219.00, 59.00, 119.00),
            ("Windshield Cover", "Walmart", 79.00, 15.00, 35.00),
            ("Floor Mats", "AutoZone", 129.00, 29.00, 69.00),
            ("Battery Charger", "Amazon", 199.00, 49.00, 109.00),
        ],
    },
    {
        "focus": "outdoor_slider",
        "score": "power_tools_score",
        "subtypes": [
            ("Cordless Drill", "Home Depot", 255.00, 79.00, 159.00),
            ("Circular Saw", "Harbor Freight", 249.00, 69.00, 149.00),
            ("Tool Set", "Home Depot", 129.00, 29.00, 69.00),
            ("Torque Wrench", "Harbor Freight", 199.00, 49.00, 109.00),
            ("Shop Vacuum", "Lowe's", 219.00, 69.00, 129.00),
            ("Welding Helmet", "Harbor Freight", 179.00, 39.00, 99.00),
            ("Safety Glasses", "Home Depot", 89.00, 19.00, 39.00),
            ("Work Gloves", "Lowe's", 79.00, 15.00, 35.00),
            ("Socket Set", "Amazon", 149.00, 39.00, 79.00),
            ("Angle Grinder", "Home Depot", 239.00, 59.00, 129.00),
        ],
    },
    {
        "focus": "outdoor_slider",
        "score": "gardening_supplies_score",
        "subtypes": [
            ("Garden Hose", "Home Depot", 99.00, 19.00, 49.00),
            ("Lawn Mower", "Lowe's", 799.00, 129.00, 199.00),
            ("Camping Tent", "REI", 229.00, 59.00, 129.00),
            ("Sleeping Bag", "Dick's Sporting Goods", 179.00, 39.00, 89.00),
            ("Hiking Backpack", "REI", 199.00, 49.00, 109.00),
            ("Picnic Blanket", "Target", 79.00, 15.00, 39.00),
            ("Adjustable Dumbbells", "Amazon", 299.00, 99.00, 179.00),
            ("Yoga Mat", "Walmart", 89.00, 19.00, 39.00),
            ("Bird Feeder", "Home Depot", 129.00, 29.00, 69.00),
            ("Running Water Bottle", "Dick's Sporting Goods", 69.00, 15.00, 35.00),
        ],
    },
    {
        "focus": "creative_slider",
        "score": "books_score",
        "subtypes": [
            ("Hardcover Bestseller", "Barnes & Noble", 169.00, 39.00, 89.00),
            ("Paperback Novel", "Barnes & Noble", 89.00, 15.00, 39.00),
            ("Acoustic Guitar", "Guitar Center", 699.00, 79.00, 159.00),
            ("MIDI Keyboard", "Sweetwater", 249.00, 69.00, 149.00),
            ("Vinyl Record Player", "Target", 299.00, 99.00, 169.00),
            ("Blu-ray Collection", "Criterion", 129.00, 29.00, 69.00),
            ("Sketchbook Set", "Barnes & Noble", 79.00, 19.00, 39.00),
            ("Harmonica", "Guitar Center", 89.00, 19.00, 39.00),
            ("Film Projector", "Amazon", 499.00, 59.00, 129.00),
            ("Music Stand", "Sweetwater", 69.00, 15.00, 35.00),
        ],
    },
]


USER_ROWS = [
    (2, "james", "james123", "james@gmail.com", 0),
    (3, "jamie", "jamie123", "jamie@outlook.com", 0),
    (4, "serkis_dergarabidian", "serkis123", "serkis@linux.com", 0),
    (5, "jemma", "jemma123", "jemma@proton.me", 0),
]

PROFILE_SPECS = [
    (2, "mum", 2, "home"),
    (3, "dad", 2, "electronics"),
    (4, "mum", 3, "home"),
    (5, "sister", 3, "fashion"),
    (6, "brother", 3, "electronics"),
    (7, "anna", 4, "luxury"),
    (8, "anna", 5, "children"),
    (9, "dad", 5, "car"),
    (10, "mum", 5, "home"),
    (11, "etab", 5, "children"),
    (12, "bibana", 5, "home"),
    (13, "clair", 5, "luxury"),
    (14, "suhair", 5, "personal"),
]

PROFILE_FOCUS = {
    "home": (["furniture_score", "home_decor_score", "storage_home_score", "cleaning_score", "home_organization_score"], "home_slider", 1.7),
    "electronics": (["computing_devices_score", "peripherals_score", "displays_score", "storage_electronics_score", "audio_score", "video_score", "wearables_tech_score", "accessories_electronics_score", "power_charging_score"], "electronics_slider", 1.7),
    "fashion": (["men_fashion_score", "women_fashion_score", "children_fashion_score", "fashion_general_score"], "wearables_slider", 1.7),
    "luxury": (["jewelry_score", "luxury_score"], "luxury_slider", 1.8),
    "children": (["toys_score", "educational_toys_score", "games_puzzles_score", "baby_gear_score"], "children_slider", 1.6),
    "car": (["car_accessories_score", "car_vehicle_score"], "car_slider", 1.7),
    "personal": (["skincare_score", "personal_hygiene_score"], "personal_care_slider", 1.7),
}


def clear_existing_rows(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sales")
    conn.execute("DELETE FROM items")
    conn.execute("DELETE FROM user_profiles WHERE profile_id != ?", (ADMIN_PROFILE_ID,))
    conn.execute("DELETE FROM users_login WHERE user_id != ?", (ADMIN_USER_ID,))


def ensure_admin_rows(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO users_login (user_id, username_, password_, email_, is_admin) VALUES (?, ?, ?, ?, 1)",
        (ADMIN_USER_ID, "admin", "admin123", "FarhanIsBest@gmail.com"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO user_profiles (profile_id, name_, user_id) VALUES (?, ?, ?)",
        (ADMIN_PROFILE_ID, "admin", ADMIN_USER_ID),
    )


def build_profile_rows() -> list[tuple]:
    rows = []
    for profile_id, name, user_id, focus_key in PROFILE_SPECS:
        scores = {col: 0 for col in SCORE_COLS}
        sliders = {col: 0.0 for col in SLIDER_COLS}
        score_fields, slider_field, slider_value = PROFILE_FOCUS[focus_key]
        for field in score_fields:
            scores[field] = 180
        if focus_key == "luxury":
            scores["jewelry_score"] = 220
            scores["luxury_score"] = 210
        elif focus_key == "electronics":
            scores["computing_devices_score"] = 200
        elif focus_key == "children":
            scores["toys_score"] = 190
        elif focus_key == "car":
            scores["car_accessories_score"] = 190
        elif focus_key == "personal":
            scores["skincare_score"] = 190
        sliders[slider_field] = slider_value
        if focus_key in {"home", "personal"}:
            sliders["creative_slider"] = 0.9
        if focus_key in {"electronics", "car"}:
            sliders["outdoor_slider"] = 0.9
        rows.append((profile_id, name, user_id, *[scores[col] for col in SCORE_COLS], *[sliders[col] for col in SLIDER_COLS]))
    return rows


def build_item_values(name: str, retailer: str, price: float, active_score_column: str, active_score_value: int) -> tuple:
    scores = {col: 0 for col in SCORE_COLS}
    scores[active_score_column] = active_score_value
    return (name, retailer, link_for(retailer, name), price, *[scores[col] for col in SCORE_COLS])


def build_item_rows() -> list[tuple]:
    rows = []
    item_id = 1
    for group_index, group in enumerate(GROUPS):
        score_col = group["score"]
        subtypes = group["subtypes"]
        for subtype_index, (base_name, retailer, high_price, low_price, mid_price) in enumerate(subtypes):
            for label, price, score in (
                ("Premium", high_price, 220 + ((group_index * 7 + subtype_index * 5) % 36)),
                ("Budget", low_price, 40 + ((group_index * 11 + subtype_index * 3) % 81)),
            ):
                name = f"{label} {base_name}"
                rows.append((item_id, *build_item_values(name, retailer, price, score_col, score)))
                item_id += 1
        if group_index < 10:
            for extra_index, (base_name, retailer, _high_price, _low_price, mid_price) in enumerate(subtypes[:3]):
                name = f"Enhanced {base_name}"
                rows.append((item_id, *build_item_values(name, retailer, mid_price, score_col, 140 + ((group_index * 5 + extra_index * 4) % 41))))
                item_id += 1
    return rows


def build_sale_rows(item_rows: list[tuple]) -> list[tuple]:
    rows = []
    start = datetime(2026, 1, 1, 9, 0, 0)
    price_factors = [0.82, 0.89, 0.95, 1.03, 1.08, 1.14, 0.92, 1.18, 0.87, 1.05]
    commission_rates = [0.03, 0.045, 0.05, 0.06, 0.075, 0.08, 0.09, 0.10, 0.12, 0.15, 0.18]
    user_cycle = [2, 3, 4, 5]
    for sale_id in range(1, 301):
        item = item_rows[(sale_id - 1) % len(item_rows)]
        item_id, _name, retailer, _link, item_price = item[:5]
        sale_price = round(item_price * price_factors[(sale_id - 1) % len(price_factors)], 2)
        commission_rate = commission_rates[(sale_id - 1) % len(commission_rates)]
        profit = round(sale_price * commission_rate, 2)
        sold_at = (start + timedelta(hours=3 * (sale_id - 1))).strftime("%Y-%m-%d %H:%M:%S")
        rows.append((sale_id, user_cycle[(sale_id - 1) % 4], item_id, retailer, sale_price, commission_rate, profit, sold_at))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Populate Giftify sample data")
    parser.add_argument("db_path", nargs="?", default="giftify.db", help="SQLite database path")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        clear_existing_rows(conn)
        ensure_admin_rows(conn)

        conn.executemany(
            "INSERT INTO users_login (user_id, username_, password_, email_, is_admin) VALUES (?, ?, ?, ?, ?)",
            USER_ROWS,
        )

        conn.executemany(
            "INSERT INTO user_profiles (" + ", ".join(PROFILE_COLS) + ") VALUES (" + ", ".join(["?"] * len(PROFILE_COLS)) + ")",
            build_profile_rows(),
        )

        item_rows = build_item_rows()
        if len(item_rows) != 250:
            raise RuntimeError(f"Expected 250 items, got {len(item_rows)}")
        for row in item_rows:
            if len(row) != len(ITEM_COLS):
                raise RuntimeError("Each item must populate every item column, including zero-valued category scores.")
        conn.executemany(
            "INSERT INTO items (" + ", ".join(ITEM_COLS) + ") VALUES (" + ", ".join(["?"] * len(ITEM_COLS)) + ")",
            item_rows,
        )

        sale_rows = build_sale_rows(item_rows)
        if len(sale_rows) != 300:
            raise RuntimeError(f"Expected 300 sales, got {len(sale_rows)}")
        conn.executemany(
            "INSERT INTO sales (sale_id, user_id, item_id, retailer_name, sale_price, commission_rate, profit, sold_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            sale_rows,
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()