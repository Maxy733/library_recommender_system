
import pandas as pd
import requests
import time

# Load your dataset
df = pd.read_csv('cleaning_book_data_with_ratings.csv')

# Get unique authors (limit to 15,000 unique authors)
unique_authors = df['Author'].dropna().unique()[:15000]

# Function to fetch data from Open Library
def get_openlibrary_data(author_name):
    query = author_name.replace(" ", "+")
    url = f"https://openlibrary.org/search/authors.json?q={query}"
    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            if data['docs']:
                doc = data['docs'][0]
                return doc.get('birth_date'), doc.get('bio') if isinstance(doc.get('bio'), str) else None
    except:
        pass
    return None, None

# Collect all authors
authors_data = []

for idx, author_name in enumerate(unique_authors, start=1):
    name_parts = author_name.split()
    first_name = name_parts[0] if len(name_parts) > 0 else 'Unknown'
    last_name = name_parts[-1] if len(name_parts) > 1 else 'Unknown'

    birth_date, biography = get_openlibrary_data(author_name)

    authors_data.append({
        'first_name': first_name,
        'last_name': last_name,
        'date_of_birth': birth_date or pd.NaT,
        'nationality': 'Unknown',
        'biography': biography if biography else 'No biography available.'
    })

    print(f"{idx}/{len(unique_authors)} ✅ Processed: {author_name}")
    time.sleep(1)  # Be polite to the API

# Save to one CSV file
authors_df = pd.DataFrame(authors_data).drop_duplicates(subset=['first_name', 'last_name'])
authors_df.to_csv("authors_full_15000.csv", index=False)
print("✅ All authors saved to 'authors_full_15000.csv'")