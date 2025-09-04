import pandas as pd
import aiohttp
import asyncio
import random
import os
import shutil
import nest_asyncio

nest_asyncio.apply()

# === Config ===
EXISTING_FILE = "backup_17400.csv"
FINAL_OUTPUT = "books_150000.csv"
TARGET_COUNT = 20000
MAX_RESULTS = 40
SAVE_EVERY = 200
CONNECTION_LIMIT = 400   # 🔥 crank this up
PRINT_EVERY = 10
RETRIES = 2
PAGES_PER_KEYWORD = 3    # 🔥 fetch multiple pages per keyword

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
    mode = "w" if not os.path.exists(FINAL_OUTPUT) else "a"
    header = not os.path.exists(FINAL_OUTPUT)
    df.to_csv(FINAL_OUTPUT, mode=mode, index=False, header=header)
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
async def fetch(session, query, start_index=0):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={MAX_RESULTS}&startIndex={start_index}"
    for attempt in range(RETRIES):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                return await resp.json() or {}
        except:
            if attempt < RETRIES - 1:
                await asyncio.sleep(0.2)
    return {}

# === Collector ===
async def collect_books():
    global count
    sem = asyncio.Semaphore(CONNECTION_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONNECTION_LIMIT)

    async with aiohttp.ClientSession(connector=connector) as session:
        keyword_index = 0

        while count < TARGET_COUNT:
            # Rotate through keywords instead of random picks
            kw = keywords[keyword_index % len(keywords)]
            keyword_index += 1
            query = f"{kw} {random.choice(suffixes)}"

            tasks = []
            for p in range(PAGES_PER_KEYWORD):
                start_index = p * MAX_RESULTS
                tasks.append(fetch(session, query, start_index=start_index))

            # Process results as they arrive
            for coro in asyncio.as_completed(tasks):
                data = await coro
                for item in data.get("items", []):
                    info = item.get("volumeInfo", {})
                    title = info.get("title", "")
                    authors = ", ".join(info.get("authors", []))
                    full_title = f"{title} / {authors}" if authors else title

                    if not full_title or full_title.lower() in existing_titles:
                        continue

                    cover = info.get("imageLinks", {}).get("thumbnail", "")
                    desc = info.get("description", "")
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

                    # Output
                    if count % PRINT_EVERY == 0:
                        print(f"📚 {count}/{TARGET_COUNT}: {full_title}")

                    if count % SAVE_EVERY == 0:
                        save_checkpoint(pd.DataFrame(all_books[-SAVE_EVERY:]), count)

                    if count >= TARGET_COUNT:
                        break
                if count >= TARGET_COUNT:
                    break

        save_checkpoint(pd.DataFrame(all_books[-SAVE_EVERY:]), count)
        print(f"\n✅ Done! {count} books collected.")

# === Execute ===
if __name__ == "__main__":
    asyncio.run(collect_books())