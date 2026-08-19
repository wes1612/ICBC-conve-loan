PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id TEXT PRIMARY KEY,
    merchant_name TEXT NOT NULL,
    industry TEXT,
    profile_type TEXT
);

CREATE TABLE IF NOT EXISTS unstructured_reviews (
    review_id TEXT PRIMARY KEY,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    source_platform TEXT NOT NULL,
    review_date TEXT NOT NULL,
    rating REAL NOT NULL,
    sentiment_label TEXT NOT NULL,
    review_text TEXT NOT NULL,
    contains_image INTEGER NOT NULL DEFAULT 0,
    merchant_replied INTEGER NOT NULL DEFAULT 0,
    useful_count INTEGER NOT NULL DEFAULT 0,
    is_simulated INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS review_keyword_stats (
    keyword_id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id TEXT NOT NULL REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    frequency INTEGER NOT NULL,
    polarity TEXT NOT NULL,
    rank_no INTEGER NOT NULL,
    UNIQUE(merchant_id, keyword)
);

CREATE TABLE IF NOT EXISTS review_wordcloud_outputs (
    merchant_id TEXT PRIMARY KEY REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    wordcloud_image_path TEXT NOT NULL,
    wordcloud_shape TEXT NOT NULL DEFAULT 'circle',
    color_theme TEXT NOT NULL DEFAULT 'red',
    frequency_json TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_analysis_results (
    merchant_id TEXT PRIMARY KEY REFERENCES merchants(merchant_id) ON DELETE CASCADE,
    review_count INTEGER NOT NULL,
    avg_rating REAL NOT NULL,
    positive_review_ratio REAL NOT NULL,
    negative_review_ratio REAL NOT NULL,
    top5_keywords TEXT NOT NULL,
    composite_score REAL NOT NULL,
    qualitative_summary TEXT NOT NULL,
    negative_summary TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
