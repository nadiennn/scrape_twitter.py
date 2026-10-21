"""
Scraping tweet MBG (Makan Bergizi Gratis) lewat Apify API (actor: xquik/x-tweet-scraper).
Hasil digabung ke data_mbg.csv, duplikat dibuang, lalu disaring
relevansinya ke data_mbg_final.csv.

Cara pakai:
1. config.py berisi  APIFY_TOKEN = apify_api_token = "MASUKKAN_TOKEN_ANDA_DISINI"
2. python apify_mbg.py
Aman dijalankan berulang (data lama tidak hilang).
"""
import datetime as dt
import os
import re
import time

import pandas as pd
from apify_client import ApifyClient

try:
    from config import APIFY_TOKEN
except ImportError:
    APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")

if not APIFY_TOKEN:
    raise SystemExit("APIFY_TOKEN belum diisi di config.py")

client = ApifyClient(APIFY_TOKEN)

ACTOR_ID = "xquik/x-tweet-scraper"
OUTPUT_FILE = "data_mbg.csv"
FINAL_FILE = "data_mbg_final.csv"
TARGET = 1000
STOP_AT = 1050          # berhenti kalau data relevan sudah segini (buffer)

# Ubah ke True kalau mau menghapus kolom username/nama/followers dari hasil final
ANONIMKAN = False

# Tahap 1: satu run per kata kunci
QUERIES = [
    "MBG",
    "makan bergizi gratis",
    "program MBG",
    "menu MBG",
    "keracunan MBG",
    "anggaran MBG",
    "MBG sekolah",
    "dapur MBG",
    "SPPG MBG",
    "badan gizi nasional",
]
MAX_PER_RUN = 300

# Tahap 2 (otomatis, hanya kalau tahap 1 belum cukup): pecah per rentang tanggal
WINDOW_QUERIES = ["MBG", "makan bergizi gratis"]
START_DATE = dt.date(2026, 8, 1)
END_DATE = dt.date(2026, 10, 21)
WINDOW_DAYS = 3

RELEVAN = re.compile(
    r"\bMBG\b|makan bergizi gratis|badan gizi nasional|\bSPPG\b",
    re.IGNORECASE,
)


def _get(obj, *names):
    for n in names:
        if isinstance(obj, dict) and n in obj:
            return obj[n]
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def normalisasi(it):
    a = it.get("author")
    a = a if isinstance(a, dict) else {}
    return {
        "tweet_id": str(it.get("id") or it.get("tweetId") or ""),
        "text": it.get("text"),
        "full_text": it.get("text"),
        "author_handle": it.get("authorUsername") or a.get("username") or a.get("userName"),
        "author_name": it.get("authorName") or a.get("name"),
        "author_followers": it.get("authorFollowers") or a.get("followers"),
        "created_at": it.get("createdAt"),
        "like_count": it.get("likeCount"),
        "retweet_count": it.get("retweetCount"),
        "reply_count": it.get("replyCount"),
        "quote_count": it.get("quoteCount"),
        "view_count": it.get("viewCount"),
        "lang": it.get("lang"),
        "url": it.get("url") or it.get("tweetUrl"),
        "source_actor": ACTOR_ID,
    }


def muat_data():
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE, dtype={"tweet_id": str})
        print(f"Data lama dimuat: {len(df)} baris")
        return df
    return pd.DataFrame()


def relevan(df):
    return int(df["full_text"].fillna("").str.contains(RELEVAN).sum()) if not df.empty else 0


def jalankan(term, max_items):
    run_input = {
        "searchTerms": [term],
        "maxItems": max_items,
        "queryType": "Latest",
        "outputPreset": "flat",
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    ds_id = _get(run, "default_dataset_id", "defaultDatasetId")
    items = client.dataset(ds_id).list_items().items
    rows = [normalisasi(i) for i in items]
    return [r for r in rows if r["tweet_id"]]


def tambah(df, rows):
    if not rows:
        return df
    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    df["tweet_id"] = df["tweet_id"].astype(str)
    df = df.drop_duplicates(subset="tweet_id")
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    return df


def simpan_final(df):
    if df.empty:
        print("Tidak ada data.")
        return
    final = df[df["full_text"].fillna("").str.contains(RELEVAN)]
    if ANONIMKAN:
        final = final.drop(columns=["author_handle", "author_name", "author_followers"],
                           errors="ignore")
    final.to_csv(FINAL_FILE, index=False, encoding="utf-8-sig")
    print("\n" + "=" * 50)
    print(f"Total mentah          : {len(df)} baris")
    print(f"Total relevan (final) : {len(final)} baris -> {FINAL_FILE}")
    print("=" * 50)
    if len(final) >= TARGET:
        print("Syarat >= 1000 baris TERPENUHI.")
    else:
        print(f"Masih kurang {TARGET - len(final)} baris.")


def proses(df, term, max_items):
    print(f"\n[+] {term}")
    try:
        rows = jalankan(term, max_items)
    except Exception as e:
        print(f"    [!] Error: {e}")
        return df
    print(f"    -> {len(rows)} tweet diterima")
    df = tambah(df, rows)
    print(f"    -> total relevan sejauh ini: {relevan(df)}")
    time.sleep(2)
    return df


def main():
    df = muat_data()

    # Tahap 1
    for q in QUERIES:
        if relevan(df) >= STOP_AT:
            break
        df = proses(df, f"{q} lang:id -filter:nativeretweets", MAX_PER_RUN)

    # Tahap 2: per rentang tanggal (hanya jika belum cukup)
    cur = START_DATE
    while relevan(df) < STOP_AT and cur < END_DATE:
        nxt = min(cur + dt.timedelta(days=WINDOW_DAYS), END_DATE)
        for q in WINDOW_QUERIES:
            if relevan(df) >= STOP_AT:
                break
            term = f"{q} lang:id -filter:nativeretweets since:{cur} until:{nxt}"
            df = proses(df, term, MAX_PER_RUN)
        cur = nxt

    simpan_final(df)


if __name__ == "__main__":
    main()