import pandas as pd
from sqlalchemy import create_engine, text

# === Connect to Railway PostgreSQL ===
engine = create_engine("postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway")

# === Step 1: Load CSV ===
df = pd.read_csv("books_17000_with_author.csv")
df = df.dropna(subset=["isbn", "author"])  # Keep rows with valid ISBN & author

# === Step 2: Load books and authors from DB ===
books_df = pd.read_sql("SELECT book_id, isbn FROM books", engine)
authors_df = pd.read_sql("SELECT author_id, name FROM authors", engine)

# === Step 3: Merge on isbn and author name ===
merged = pd.merge(df, books_df, on="isbn", how="inner")
merged = pd.merge(merged, authors_df, left_on="author", right_on="name", how="inner")

# === Step 4: Drop duplicates based on (isbn + author) to match original CSV rows
merged_unique = merged.drop_duplicates(subset=["isbn", "author"])

# === Step 5: Prepare final DataFrame with max limit
book_authors_df = merged_unique[["book_id", "author_id"]].drop_duplicates()
book_authors_df = book_authors_df.head(17603)  # Limit to 17,603 rows max

print(f"📊 Total rows to insert: {len(book_authors_df)}")

# === Step 6: Insert in batches with ON CONFLICT DO NOTHING ===
batch_size = 100
with engine.begin() as conn:
    for i in range(0, len(book_authors_df), batch_size):
        batch = book_authors_df.iloc[i:i + batch_size]
        for _, row in batch.iterrows():
            conn.execute(
                text("""
                    INSERT INTO book_authors (book_id, author_id)
                    VALUES (:book_id, :author_id)
                    ON CONFLICT DO NOTHING;
                """),
                {"book_id": int(row["book_id"]), "author_id": int(row["author_id"])}
            )
        print(f"✅ Inserted rows {i} to {i + len(batch) - 1}")

print("🎉 DONE — All book-author pairs from books_17000_with_author.csv have been inserted and the script has stopped.")