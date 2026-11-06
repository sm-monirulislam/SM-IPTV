import os
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

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

os.makedirs(IMAGE_FOLDER, exist_ok=True)

def clean_name(name):
    name = name.lower()
    name = re.sub(r'[\(\[].*?[\)\]]', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def download_single_logo(channel_name, original_logo_url):
    if not original_logo_url:
        return "", ""
    
    image_name = original_logo_url.split("/")[-1].split("?")[0]
    
    if not image_name or not image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg')):
        cleaned_ch = clean_name(channel_name)
        image_name = f"{cleaned_ch}.png" if cleaned_ch else "default.png"
        
    local_image_path = os.path.join(IMAGE_FOLDER, image_name)
    
    try:
        img_data = requests.get(original_logo_url, timeout=10).content
        with open(local_image_path, "wb") as handler:
            handler.write(img_data)
    except Exception as e:
        print(f"Failed to download logo for {channel_name}: {e}")
        if not os.path.exists(local_image_path):
            return channel_name, original_logo_url
            
    github_logo_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/{BRANCH_NAME}/{IMAGE_FOLDER}/{image_name}"
    return channel_name, github_logo_url

def smart_group_title(channel_name, original_group):
    name_lower = channel_name.lower()
    
    if any(k in name_lower for k in ['sports', 'cricket', 'football', 't sports', 'willow', 'ten', 'sony sports', 'euro']):
        return "Sports"
    elif any(k in name_lower for k in ['news', '24', 'somoy', 'jamuna', 'bbc', 'cnn', 'indiatoday', 'abp']):
        return "News"
    elif any(k in name_lower for k in ['movie', 'hbo', 'star movies', 'zee cinema', 'cines', 'flix']):
        return "Movies"
    elif any(k in name_lower for k in ['kids', 'cartoon', 'pogo', 'nick', 'disney', 'hungama']):
        return "Kids"
    elif any(k in name_lower for k in ['islamic', 'quran', 'peace', 'madani']):
        return "Islamic"
    elif original_group and original_group.strip() and original_group.lower() != "fancode":
        return original_group.strip()
    else:
        return "General"

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
            
            group_match = re.search(r'group-title="([^"]+)"', extinf)
            old_group = group_match.group(1) if group_match else ""
            
            name_match = re.search(r',(.+)$', extinf)
            channel_name = name_match.group(1).strip() if name_match else "Unknown"
            
            channels.append({
                "extinf": extinf,
                "url": stream_url,
                "name": channel_name,
                "old_logo_url": old_logo_url,
                "group": smart_group_title(channel_name, old_group)
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

# ডুপ্লিকেট রিমুভ করার আগে ইউনিক লোগো লিংকগুলো কালেক্ট করা যাতে এক লোগো বারবার ডাউনলোড না হয়
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

# সব ইউনিক এবং ডুপ্লিকেট চ্যানেলের লোগো একসাথে প্যারালালি (একসাথে ১০০টি পর্যন্ত) ডাউনলোড করার জন্য থ্রেড পুল ব্যবহার করা
print("Starting parallel logo downloads...")
logo_mapping = {}

all_unique_to_download = unique_channels + duplicate_channels

with ThreadPoolExecutor(max_workers=100) as executor:
    futures = {executor.submit(download_single_logo, ch["name"], ch["old_logo_url"]): ch for ch in all_unique_to_download}
    
    for future in as_completed(futures):
        ch_name, final_url = future.result()
        if final_url:
            logo_mapping[ch_name] = final_url

new_playlist_lines = ["#EXTM3U"]

print("Building playlist...")
for ch in unique_channels:
    extinf = ch["extinf"]
    ch_name = ch["name"]
    new_logo_url = logo_mapping.get(ch_name, ch["old_logo_url"])
    
    if new_logo_url:
        if 'tvg-logo="' in extinf:
            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{new_logo_url}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{new_logo_url}"')
            
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]*"', f'group-title="{ch["group"]}"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{ch["group"]}"')
    
    new_playlist_lines.append(extinf)
    new_playlist_lines.append(ch["url"])

for idx, ch in enumerate(duplicate_channels, start=1):
    extinf = ch["extinf"]
    ch_name = ch["name"]
    new_logo_url = logo_mapping.get(ch_name, ch["old_logo_url"])
    
    if new_logo_url:
        if 'tvg-logo="' in extinf:
            extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{new_logo_url}"', extinf)
        else:
            extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 tvg-logo="{new_logo_url}"')
            
    if 'group-title="' in extinf:
        extinf = re.sub(r'group-title="[^"]*"', f'group-title="Back Channel"', extinf)
    else:
        extinf = extinf.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="Back Channel"')
    
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
