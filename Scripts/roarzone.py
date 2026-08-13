import requests

API_URL = "https://raw.githubusercontent.com/sm-monirulislam/RoarZone-Auto-Update-playlist/refs/heads/main/RoarZone.m3u"
OUTPUT_FILE = "RoarZone.m3u"

response = requests.get(API_URL, timeout=30)
response.raise_for_status()

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Updated {OUTPUT_FILE}")
