from pathlib import Path
import sqlite3

DB_PATH = Path(r"C:\Users\13777\Documents\Codex\2026-08-01\new-chat\outputs\unstructured_reviews\icbc_unstructured_reviews.db")

def main():
    conn = sqlite3.connect(DB_PATH)
    checks = {
        "review_count": conn.execute("SELECT COUNT(*) FROM unstructured_reviews").fetchone()[0],
        "merchant_count": conn.execute("SELECT COUNT(*) FROM merchants").fetchone()[0],
        "analysis_count": conn.execute("SELECT COUNT(*) FROM review_analysis_results").fetchone()[0],
        "wordcloud_count": conn.execute("SELECT COUNT(*) FROM review_wordcloud_outputs").fetchone()[0],
        "keyword_rows": conn.execute("SELECT COUNT(*) FROM review_keyword_stats").fetchone()[0],
    }
    print(checks)
    assert checks["merchant_count"] == 5
    assert checks["review_count"] == 1000
    assert checks["analysis_count"] == 5
    assert checks["wordcloud_count"] == 5
    for row in conn.execute("SELECT merchant_id, review_count, top5_keywords, composite_score, negative_summary FROM review_analysis_results ORDER BY merchant_id"):
        print(row)
    conn.close()

if __name__ == "__main__":
    main()
