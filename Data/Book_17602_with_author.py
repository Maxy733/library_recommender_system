import pandas as pd

# Load your file
df = pd.read_csv("books_17000.csv")

# Step 1: Extract author from title using '/'
df[['title_clean', 'author']] = df['title'].str.split('/', n=1, expand=True)
df['title'] = df['title_clean'].str.strip()
df['author'] = df['author'].str.strip()
df.drop(columns=['title_clean'], inplace=True)

# Step 2: Reorder the columns
desired_order = ['isbn', 'author', 'title', 'description', 'publication_date', 'pages', 'language', 'cover_image_url', 'genre', 'rating']

# Ensure all columns exist (fill missing ones with empty or NaN)
for col in desired_order:
    if col not in df.columns:
        df[col] = ""

# Reorder
df = df[desired_order]

# Save the result
df.to_csv("books_17000_with_author.csv", index=False)
print("✅ Saved as books_17000_with_author.csv")