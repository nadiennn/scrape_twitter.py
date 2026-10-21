import os
import pandas as pd
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

API_TOKEN = os.getenv("APIFY_API_TOKEN")
MAX_TWEET = 1500   # dilebihkan, nanti dibersihkan jadi >1000

PERIODE = "since:2026-09-01 until:2026-10-21"

KATA_KUNCI = [
    f"MBG {PERIODE}",
    f"makan bergizi gratis {PERIODE}",
    f"program MBG sekolah {PERIODE}",
    f"menu MBG {PERIODE}",
    f"keracunan MBG {PERIODE}",
    f"anggaran MBG {PERIODE}",
]

client = ApifyClient(API_TOKEN)

run = client.actor("apidojo/tweet-scraper").call(run_input={
    "searchTerms": KATA_KUNCI,
    "maxItems": MAX_TWEET,
    "sort": "Latest",
})

items = list(client.dataset(run.default_dataset_id).iterate_items())
print(f"Dapat {len(items)} tweet mentah")

rows = []
for t in items:
    rows.append({
        "tanggal": t.get("createdAt"),
        "tweet": t.get("text") or t.get("fullText"),
        "like": t.get("likeCount"),
        "retweet": t.get("retweetCount"),
        "balasan": t.get("replyCount"),
        "views": t.get("viewCount"),
        "link": t.get("url"),
    })

df = pd.DataFrame(rows).drop_duplicates(subset="link")

# hanya simpan tweet yang benar-benar membahas MBG
df = df[df["tweet"].fillna("").str.contains("MBG|makan bergizi gratis", case=False)]

df.to_csv("tweet_mbg.csv", index=False, encoding="utf-8-sig")
print(f"Tersimpan {len(df)} tweet di tweet_mbg.csv")