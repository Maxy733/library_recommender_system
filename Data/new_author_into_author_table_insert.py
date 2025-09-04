import pandas as pd
from sqlalchemy import create_engine, text

# Connect to your Railway PostgreSQL
engine = create_engine("postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway")

# Load the CSV
df = pd.read_csv("books_17000_with_author.csv")

# Drop missing authors and get unique names
author_names = df['author'].dropna().unique()
author_df = pd.DataFrame({"name": author_names})

# Optional: Remove duplicates already in the DB
with engine.connect() as conn:
    existing = pd.read_sql("SELECT name FROM authors", conn)
    new_authors_df = author_df[~author_df['name'].isin(existing['name'])]
    
    # Insert only new authors
    new_authors_df.to_sql("authors", engine, if_exists="append", index=False)

print("✅ Authors inserted into 'authors' table (skipping duplicates).")