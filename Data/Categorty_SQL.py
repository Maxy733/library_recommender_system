import pandas as pd
from sqlalchemy import create_engine

# Load CSV
df = pd.read_csv("cleaning_book_data_with_ratings.csv")

# Rename column below to match your actual column name if different
if 'Category' in df.columns:
    category_col = 'Category'
elif 'Genre' in df.columns:
    category_col = 'Genre'
else:
    raise ValueError("❌ No recognizable category column found in the dataset.")

# Extract unique non-null categories
df['Category'] = df[category_col].astype(str).str.strip()
categories = df['Category'].dropna().unique()

# Create DataFrame for insertion
category_df = pd.DataFrame({
    'category_name': categories,
    'description': ['No description available.'] * len(categories)
})

# Connect to PostgreSQL (replace with your actual credentials)
engine = create_engine(
    "postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway"
)

# Insert into 'categories' table
category_df.to_sql('categories', engine, if_exists='append', index=False)

print("✅ Categories inserted into PostgreSQL successfully.")