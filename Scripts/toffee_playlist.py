import requests
from datetime import datetime

# ==============================
# CONFIG
# ==============================
API_URL = "https://raw.githubusercontent.com/sm-monirulislam/Toffee-Auto-Update/refs/heads/main/toffee_data.json"
OUTPUT_FILE = "Toffee.m3u"

# ==============================
# FETCH API
# ==============================
try:
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()
except Exception as e:
    print(f"API Error: {e}")
    exit()

channels = data.get("response", [])

if not channels:
    print("No channel data found.")
    exit()

# ==============================
# CREATE PLAYLIST
# ==============================
lines = [
    "#EXTM3U",
    f"# Toffee Live Channels",
    f"# Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    ""
]

for channel in channels:
    name = channel.get("name", "Unknown")
    link = channel.get("link", "")
    logo = channel.get("logo", "")
    category = channel.get("category_name", "Toffee")

    headers = channel.get("headers", {})

    if not link:
        continue

    # EXTINF
    lines.append(
        f'#EXTINF:-1 tvg-name="{name}" '
        f'tvg-logo="{logo}" '
        f'group-title="{category}",{name}'
    )

    # HLS headers
    if headers:
        header_parts = []

        for key, value in headers.items():
            if value is None:
                continue

            value = str(value)

            # Escape characters used by KODIPROP syntax
            value = value.replace("&", "%26")
            value = value.replace("=", "%3D")

            header_parts.append(f"{key}={value}")

        if header_parts:
            lines.append(
                "#KODIPROP:inputstream.adaptive.stream_headers="
                + "&".join(header_parts)
            )

    lines.append(link)
    lines.append("")

# ==============================
# SAVE FILE
# ==============================
try:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("=" * 40)
    print("Playlist created successfully!")
    print(f"File   : {OUTPUT_FILE}")
    print(f"Channels: {len(channels)}")
    print("=" * 40)

except Exception as e:
    print(f"File Error: {e}")
