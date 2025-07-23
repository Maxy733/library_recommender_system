#for books
import pandas as pd
import requests
import time

# Load the uploaded data
df = pd.read_csv('cleaning_book_data_with_ratings.csv')

# Function to fetch additional book info from Google Books API
def get_book_extra_info(title, author=None):
    query = f'intitle:{title}'
    if author:
        query += f'+inauthor:{author}'
    url = f'https://www.googleapis.com/books/v1/volumes?q={query}'

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                volume_info = data['items'][0]['volumeInfo']
                return {
                    'publication_date': volume_info.get('publishedDate'),
                    'pages': volume_info.get('pageCount'),
                    'language': volume_info.get('language'),
                    'cover_image_url': volume_info.get('imageLinks', {}).get('thumbnail')
                }
    except Exception as e:
        print(f"Error fetching {title}: {e}")
    return {'publication_date': None, 'pages': None, 'language': None, 'cover_image_url': None}

# Prepare books dataframe with default fill for missing API info
extra_info_list = []
filtered_rows = []

for idx, row in df.head(15000).iterrows():  # Process all rows
    info = get_book_extra_info(row['Title'], row['Author'])

    # Fill missing values with defaults
    if info.get('publication_date') is None:
        info['publication_date'] = '2000-01-01'
    if info.get('pages') is None:
        info['pages'] = 200
    if info.get('language') is None:
        info['language'] = 'en'
    if info.get('cover_image_url') is None:
        info['cover_image_url'] = 'https://covers.openlibrary.org/b/isbn/9780143127741-L.jpg'

    extra_info_list.append(info)
    filtered_rows.append(row)

    print(f"{idx + 1}/{len(df)} ✅ Processed: {row['Title']} with fallback defaults applied if needed.")
    time.sleep(1)

extra_info_df = pd.DataFrame(extra_info_list)
filtered_df = pd.DataFrame(filtered_rows)

books_df = pd.DataFrame({
    'isbn': filtered_df['ISBN'].fillna('').astype(str),
    'title': filtered_df['Title'],
    'description': filtered_df['Short Description'],
    'publication_date': extra_info_df['publication_date'],
    'pages': extra_info_df['pages'],
    'language': extra_info_df['language'],
    'cover_image_url': extra_info_df['cover_image_url'],
    'publisher_id': 1
})

books_df.to_csv('books_extracted_with_api_full_filled.csv', index=False)

# Check first 3 rows to confirm results
print(books_df.head(3))
print("Filtered Books CSV file with default filled API data has been created.")
