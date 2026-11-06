import os
import re
import requests

GITHUB_USERNAME = "sm-monirulislam"
REPO_NAME = "SM-IPTV"
BRANCH_NAME = "main"
IMAGE_FOLDER = "images"

API_URLS = [
    "https://raw.githubusercontent.com/sm-monirulislam/AynaOTT_Auto_Update_Playlist/refs/heads/main/aynaott.m3u",
    "https://raw.githubusercontent.com/saeidrahmanbd/BDIX-IPTV/refs/heads/main/IPTV-Playlist.m3u",
    "https://raw.githubusercontent.com/sm-monirulislam/jago_bd_auto_update_playlist-/refs/heads/main/jago_bd_main.m3u"
]

OUTPUT_PLAYLIST = "Sports_data.m3u"

def clean_channel_name(name):
    name = name.lower()
    name = re.sub(r'[\(\[].*?[\)\]]', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def get_final_logo_url(channel_name, original_logo_url):
    # প্রথমে চেক করব চ্যানেলের নামের সাথে মিল রেখে লোকাল ফোল্ডারে কোনো ইমেজ ফাইল আছে কি না
    cleaned_name = clean_channel_name(channel_name)
    if cleaned_name:
        local_filename = f"{cleaned_name}.png"
        local_path = os.path.join(IMAGE_FOLDER, local_filename)
        
        # যদি লোকাল ফোল্ডারে ইমেজটি থাকে, তবে গিটহাবের র (Raw) ইউআরএল দেব
        if os.path.exists(local_path):
            return f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH_NAME}/{IMAGE_FOLDER}/{local_filename}"
            
    # যদি লোকাল ফোল্ডারে ইমেজ না থাকে, কিন্তু অরিজিনাল এপিআইতে লোগো লিংক থাকে, তবে সেটিই বসিয়ে দেব
    if original_logo_url:
        return original_logo_url
        
    return ""

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            extinf = line
            stream_url = ""
            if i + 1 < len(lines):
                stream_url = lines[i + 1].strip()
                i += 1
            
            logo_match = re.search(r'tvg-logo="([^"]+)"', extinf)
            old_logo_url = logo_match.group(1) if logo_match else ""
            
            name_match = re.search(r',(.+)$', extinf)
            channel_name = name_match.group(1).strip() if name_match else "Unknown"
            
            final_logo_url = get_final_logo_url(channel_name, old_logo_url)
            
            channels.append({
                "extinf": extinf,
                "url": stream_url,
                "name": channel_name,
                "logo_url": final_logo_url
            })
        i += 1
    return channels

all_channels = []

for api_url in API_URLS:
    try:
        print(f"Fetching: {api_url}")
        res = requests.get(api_url, timeout=15)
        if res.status_code == 200:
            all_channels.extend(parse_m3u(res.text))
    except Exception as e:
        print(f"Error fetching {api_url}: {e}")

unique_channels = []
duplicate_channels = []
seen_names = set()

for ch in all_channels:
    c_name = ch["name"].lower()
    if c_name not in seen_names:
        seen_names.add(c_name)
        unique_channels.append(ch)
    else:
        duplicate_channels.append(ch)

new_playlist_lines = ["#EXTM3U"]

for ch in unique_channels:
    extinf = ch["extinf"]
    if ch["logo_url"]:
        if 'tvg-logo="' in extinf:
            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{ch["logo_url"]}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{ch["logo_url"]}"')
    
    new_playlist_lines.append(extinf)
    new_playlist_lines.append(ch["url"])

for idx, ch in enumerate(duplicate_channels, start=1):
    extinf = ch["extinf"]
    if ch["logo_url"]:
        if 'tvg-logo="' in extinf:
            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{ch["logo_url"]}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{ch["logo_url"]}"')
    
    base_name = ch["name"]
    extinf = re.sub(r',(.+)$', f',{base_name}_{idx}', extinf)
    
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', extinf)
    if tvg_name_match:
        old_tvg_name = tvg_name_match.group(1)
        extinf = extinf.replace(f'tvg-name="{old_tvg_name}"', f'tvg-name="{old_tvg_name}_{idx}"')
    else:
        extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-name="{base_name}_{idx}"')

    new_playlist_lines.append(extinf)
    new_playlist_lines.append(ch["url"])

final_playlist_content = "\n".join(new_playlist_lines)

with open(OUTPUT_PLAYLIST, "w", encoding="utf-8") as f:
    f.write(final_playlist_content)

print(f"Playlist generated successfully: {OUTPUT_PLAYLIST}")
