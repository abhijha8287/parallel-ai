CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    decision TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    simulation_json TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

