import pandas as pd
from dateutil import parser

# Load the original CSV file
df = pd.read_csv("Book_Table.csv")

# Preview the data (optional)
print("📘 Preview of original book data:")
print(df.head())

# Function to safely parse dates
def parse_date_safe(date_str):
    try:
        return parser.parse(str(date_str)).date()
    except:
        return pd.NaT

# Step 1: Parse and clean the publication_date
df['publication_date'] = df['publication_date'].apply(parse_date_safe)

# Step 2: Drop rows with missing essential fields
df_cleaned = df.dropna(subset=['title', 'publication_date'])

# Step 3: Drop the publisher_id column (to avoid FK constraint issues)
if 'publisher_id' in df_cleaned.columns:
    df_cleaned = df_cleaned.drop(columns=['publisher_id'])

# Step 4: Save the cleaned dataframe to a new CSV file
df_cleaned.to_csv("cleaned_books.csv", index=False)

print(f"✅ Cleaned book data saved to 'cleaned_books.csv' with {len(df_cleaned)} records.")
#postgresql://postgres:pAflkfysMwUFGUPGzcbLBfUvoVJJjazQ@yamanote.proxy.rlwy.net:34649/railway