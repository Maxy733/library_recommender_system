import pandas as pd
from sqlalchemy import create_engine

# === Connect to Railway PostgreSQL ===
engine = create_engine("postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway")

# === Load cleaned book data ===
df = pd.read_csv("books_17000_with_author.csv")

# Drop rows with missing required fields (you can customize this)
df = df.dropna(subset=["isbn", "title"])

# Optional: Convert publication_date to datetime
if 'publication_date' in df.columns:
    df['publication_date'] = pd.to_datetime(df['publication_date'], errors='coerce')

# Optional: Ensure correct types for numeric fields
if 'pages' in df.columns:
    df['pages'] = pd.to_numeric(df['pages'], errors='coerce')
if 'rating' in df.columns:
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

# === Insert into books table ===
# (Skip book_id if it's auto-generated)
columns_to_insert = ['isbn', 'title', 'description', 'publication_date', 'pages', 
                     'language', 'cover_image_url', 'genre', 'rating', 'author']

df[columns_to_insert].to_sql("books", engine, if_exists="append", index=False)

print("✅ All book records inserted into books table.")