import pandas as pd
from sqlalchemy import create_engine, text

# Connect to your PostgreSQL database
engine = create_engine("postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway")

# Load books and authors from the database
books_df = pd.read_sql("SELECT book_id, title FROM books", engine)
authors_df = pd.read_sql("SELECT author_id, first_name, last_name FROM authors", engine)

# Load the source data containing book-author mappings
source_df = pd.read_csv("cleaning_book_data_with_ratings.csv")

# Clean and prepare
source_df = source_df.dropna(subset=["Title", "Author"])
source_df['first_name'] = source_df['Author'].str.split().str[0]
source_df['last_name'] = source_df['Author'].str.split().str[-1]

# Merge to find matching author_id and book_id
merged = pd.merge(source_df, books_df, left_on="Title", right_on="title", how="inner")
merged = pd.merge(merged, authors_df, on=["first_name", "last_name"], how="inner")

# Prepare book_authors data
book_authors_df = merged[["book_id", "author_id"]].drop_duplicates()

# Insert into book_authors table
book_authors_df.to_sql("book_authors", engine, if_exists="append", index=False)

print("✅ book_authors table has been populated.")