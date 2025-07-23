import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Step 1: Load and normalize CSV
df = pd.read_csv("cleaning_book_data_with_ratings.csv")
df.columns = df.columns.str.strip().str.lower()

# Filter rows with missing or empty ISBN
df_no_isbn = df[df['isbn'].isna() | (df['isbn'].str.strip() == '')].copy()

# Drop rows missing title, genre, or rating
df_no_isbn = df_no_isbn.dropna(subset=['title', 'genre', 'finalrating'])

# Connect to DB
conn = psycopg2.connect(
    dbname="railway",
    user="postgres",
    password="pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ",
    host="yamanote.proxy.rlwy.net",
    port="34649"
)
cur = conn.cursor()

# Step 2: Update existing records using title
update_query = """
    UPDATE books
    SET genre = %s,
        rating = %s
    WHERE title = %s;
"""

update_data = [
    (row['genre'], row['finalrating'], row['title'])
    for _, row in df_no_isbn.iterrows()
]

print(f"🔁 Attempting update for {len(update_data)} rows without ISBN using title only...")
execute_batch(cur, update_query, update_data)
conn.commit()

# Step 3: Optional insert if title not already present
insert_query = """
    INSERT INTO books (title, genre, rating)
    SELECT %s, %s, %s
    WHERE NOT EXISTS (
        SELECT 1 FROM books WHERE title = %s
    );
"""

insert_data = [
    (row['title'], row['genre'], row['finalrating'], row['title'])
    for _, row in df_no_isbn.iterrows()
]

print("➕ Attempting insert for unmatched titles...")
execute_batch(cur, insert_query, insert_data)
conn.commit()

# Close connection
cur.close()
conn.close()
print("✅ Done: books without ISBN processed using title only.")