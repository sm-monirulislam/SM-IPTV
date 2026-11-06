import os
import re
import requests

GITHUB_USERNAME = "sm-monirulislam"
REPO_NAME = "SM-IPTV"
BRANCH_NAME = "main"
IMAGE_FOLDER = "images"
PLAYLIST_URL = "https://raw.githubusercontent.com/saeidrahmanbd/BDIX-IPTV/refs/heads/main/IPTV-Playlist.m3u"
OUTPUT_PLAYLIST = "Sports_data.m3u"

os.makedirs(IMAGE_FOLDER, exist_ok=True)

print("Fetching playlist...")
response = requests.get(PLAYLIST_URL)
playlist_content = response.text

lines = playlist_content.splitlines()
new_lines = []

for line in lines:
    if line.startswith("#EXTINF"):
        logo_match = re.search(r'tvg-logo="([^"]+)"', line)
        if logo_match:
            old_logo_url = logo_match.group(1)
            image_name = old_logo_url.split("/")[-1].split("?")[0]
            
            if image_name:
                local_image_path = os.path.join(IMAGE_FOLDER, image_name)
                
                if not os.path.exists(local_image_path):
                    try:
                        img_data = requests.get(old_logo_url, timeout=15).content
                        with open(local_image_path, "wb") as handler:
                            handler.write(img_data)
                        print(f"Downloaded: {image_name}")
                    except Exception as e:
                        print(f"Failed to download {image_name}: {e}")
                
                new_logo_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH_NAME}/{IMAGE_FOLDER}/{image_name}"
                line = line.replace(old_logo_url, new_logo_url)
                
    new_lines.append(line)

final_playlist = "\n".join(new_lines)

with open(OUTPUT_PLAYLIST, "w", encoding="utf-8") as f:
    f.write(final_playlist)

print(f"New playlist generated: {OUTPUT_PLAYLIST}")
