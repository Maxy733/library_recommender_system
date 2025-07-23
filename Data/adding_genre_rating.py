import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# Step 1: Load and clean the CSV
csv_path = "cleaning_book_data_with_ratings.csv"
df = pd.read_csv(csv_path)

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# Print column names for debugging
print("📄 Columns found in CSV:", df.columns.tolist())

# Step 2: Map actual CSV columns to DB target
col_map = {
    'isbn': 'isbn',           # must match the 'isbn' in the DB
    'genre': 'genre',
    'rating': 'finalrating'   # CSV column name is 'finalrating'
}

# Ensure required columns exist
missing = [v for v in col_map.values() if v not in df.columns]
if missing:
    raise Exception(f"❌ Missing required columns in CSV: {missing}")

# Keep only necessary columns and drop rows with missing data
df = df[[col_map['isbn'], col_map['genre'], col_map['rating']]].dropna()

# Step 3: Connect to PostgreSQL
print("🔌 Connecting to PostgreSQL...")
conn = psycopg2.connect(
    dbname="railway",
    user="postgres",
    password="pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ",
    host="yamanote.proxy.rlwy.net",
    port="34649"
)
cur = conn.cursor()

# Step 4: Prepare and execute batch update
update_query = """
    UPDATE books
    SET genre = %s,
        rating = %s
    WHERE isbn = %s;
"""

# Create list of tuples: (genre, rating, isbn)
data = [(row[col_map['genre']], row[col_map['rating']], row[col_map['isbn']]) for _, row in df.iterrows()]

print(f"🚀 Executing batch update for {len(data)} rows...")
execute_batch(cur, update_query, data)

# Finalize
conn.commit()
cur.close()
conn.close()
print("✅ PostgreSQL 'books' table successfully updated with genre and rating.")