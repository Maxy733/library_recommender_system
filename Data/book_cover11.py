import pandas as pd
import aiohttp
import asyncio
import random
import time
import os
import shutil
import nest_asyncio

nest_asyncio.apply()

# === Config ===
EXISTING_FILE = "backup_9250.csv"
FINAL_OUTPUT = "books_10000.csv"
TARGET_COUNT = 10000
MAX_RESULTS = 40
BATCH_SIZE = 120
SAVE_EVERY = 250
CONNECTION_LIMIT = 150
PRINT_EVERY = 10
RETRIES = 2

# === Keywords ===
keywords = [
    "science", "history", "fiction", "mystery", "romance", "fantasy", "biography", "design", "space",
    "technology", "philosophy", "business", "psychology", "education", "self-help", "travel", "art",
    "culture", "inspiration", "coding", "novel", "spirituality", "crime", "comedy", "leadership",
    "politics", "cooking", "startup", "relationships", "ethics", "UX", "AI", "neuroscience"
]

suffixes = ["book", "story", "summary", "literature", "novel", "read", "volume", "text"]

# === Utility ===
def is_invalid(val):
    return pd.isna(val) or str(val).strip() == "" or str(val).lower().endswith(".jpg")

def save_checkpoint(df, count):
    df.to_csv(FINAL_OUTPUT, index=False)
    shutil.copy(FINAL_OUTPUT, f"backup_{count}.csv")
    print(f"\n💾 Saved {count} books → '{FINAL_OUTPUT}' + backup")

# === Load existing ===
if os.path.exists(EXISTING_FILE):
    df = pd.read_csv(EXISTING_FILE)
    all_books = df.to_dict("records")
    existing_titles = set(df["title"].dropna().str.lower().unique())
    count = len(df)
    print(f"✅ Loaded {count} books.")
else:
    all_books = []
    existing_titles = set()
    count = 0
    print("📦 Starting fresh...")

# === Fetch ===
async def fetch(session, query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={MAX_RESULTS}"
    for attempt in range(RETRIES):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return await response.json()
        except:
            if attempt < RETRIES - 1:
                await asyncio.sleep(0.25)
            else:
                return {}

async def fetch_with_sem(session, sem, query):
    async with sem:
        return await fetch(session, query)

# === Main Collector ===
async def collect_books():
    global count
    sem = asyncio.Semaphore(CONNECTION_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONNECTION_LIMIT)
    async with aiohttp.ClientSession(connector=connector) as session:
        while count < TARGET_COUNT:
            queries = [f"{kw} {random.choice(suffixes)}" for kw in random.choices(keywords, k=BATCH_SIZE)]
            tasks = [fetch_with_sem(session, sem, q) for q in queries]
            results = await asyncio.gather(*tasks)

            for data in results:
                for item in data.get("items", []):
                    info = item.get("volumeInfo", {})
                    title = info.get("title", "").strip()
                    authors = ", ".join(info.get("authors", [])).strip()
                    full_title = f"{title} / {authors}" if authors else title
                    if not full_title or full_title.lower() in existing_titles:
                        continue

                    cover = info.get("imageLinks", {}).get("thumbnail", "")
                    desc = info.get("description", "").strip()
                    if is_invalid(cover) or is_invalid(desc):
                        continue

                    identifiers = info.get("industryIdentifiers", [])
                    isbn = next((i["identifier"] for i in identifiers if i["type"] in ["ISBN_13", "ISBN_10"]), "")
                    pages = info.get("pageCount", "")
                    pub_date = info.get("publishedDate", "")
                    lang = info.get("language", "N/A")
                    genre = ", ".join(info.get("categories", [])) or "N/A"
                    rating = info.get("averageRating", "N/A")

                    book = {
                        "isbn": isbn,
                        "title": full_title,
                        "description": desc,
                        "publication_date": pub_date,
                        "pages": pages,
                        "language": lang,
                        "cover_image_url": cover,
                        "genre": genre,
                        "rating": rating
                    }

                    all_books.append(book)
                    existing_titles.add(full_title.lower())
                    count += 1

                    # Pretty output
                    print("--------------------------------------------------")
                    print(f"ISBN         : {isbn}")
                    print(f"Title        : {full_title}")
                    print(f"Description  : {desc[:150]}{'...' if len(desc) > 150 else ''}")
                    print(f"Published    : {pub_date}")
                    print(f"Pages        : {pages}")
                    print(f"Language     : {lang}")
                    print(f"Cover URL    : {cover}")
                    print(f"Genre        : {genre}")
                    print(f"Rating       : {rating}")
                    print("--------------------------------------------------")

                    if count % PRINT_EVERY == 0:
                        print(f"\n📚 {count}/{TARGET_COUNT}: {full_title}")

                    if count % SAVE_EVERY == 0:
                        save_checkpoint(pd.DataFrame(all_books), count)

                    if count >= TARGET_COUNT:
                        break
                if count >= TARGET_COUNT:
                    break

        save_checkpoint(pd.DataFrame(all_books), count)
        print(f"\n✅ Done! {count} books collected.")

