import os
import re
import json
import urllib.request
from datetime import datetime, timedelta
from io import StringIO

# -------------------------
# API URL (GitHub RAW)
# -------------------------
API_URL = "https://raw.githubusercontent.com/sm-monirulislam/SM-IPTV/refs/heads/main/Scripts/Catagory.json"

output_live = "Combined_Live_TV.m3u"

EXTINF_PREFIX = "#EXTINF:"
re_group_title = re.compile(r'group-title="(.*?)"')


# ========================================================
# FETCH FILE LIST FROM API
# ========================================================

def fetch_m3u_list():
    try:
        req = urllib.request.Request(
            API_URL,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if isinstance(data, list):
                return data

            if isinstance(data, dict):
                return data.get("files", [])

            return []

    except Exception as e:
        print("Error: API fetch failed:", e)
        return []


# ========================================================
# MAIN
# ========================================================

def main():
    m3u_files = fetch_m3u_list()

    if not m3u_files:
        print("Error: No files received from API")
        return

    live_buf = StringIO()
    total_found = 0

    for file_name in m3u_files:

        if not os.path.exists(file_name):
            print(f"Missing File: {file_name}")
            continue

        group_name = os.path.splitext(os.path.basename(file_name))[0]

        with open(file_name, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.strip() for l in f if l.strip()]

        i = 0
        while i < len(lines):
            if lines[i].startswith(EXTINF_PREFIX):
                line = lines[i]

                if 'group-title="' in line:
                    line = re_group_title.sub(
                        f'group-title="{group_name}"', line
                    )
                else:
                    line = re.sub(
                        r'#EXTINF:-1(.*?),',
                        rf'#EXTINF:-1\1 group-title="{group_name}",',
                        line
                    )

                block = [line]
                i += 1

                while i < len(lines) and not lines[i].startswith(EXTINF_PREFIX):
                    block.append(lines[i])
                    i += 1

                live_buf.write("\n".join(block) + "\n\n")
                total_found += 1
            else:
                i += 1

    # -------------------------------
    # HEADER
    # -------------------------------
    bd_time = datetime.utcnow() + timedelta(hours=6)

    header = (
        "#=================================\n"
        "# Developed by: Monirul Islam\n"
        "# Telegram: https://t.me/monirul_Islam_SM\n"
        "# Channel: https://t.me/sm_iptv_bd\n"
        f"# Last Updated: {bd_time.strftime('%Y-%m-%d %H:%M:%S')} (BD Time)\n"
        f"# Channels Count: {total_found}\n"
        "# Usage: Personal / Educational\n"
        "#=================================\n\n"
    )

    final_output = header + "#EXTM3U\n\n" + live_buf.getvalue()

    with open(output_live, "w", encoding="utf-8") as f:
        f.write(final_output)

    print("=================================")
    print("DONE")
    print("Total Channels:", total_found)
    print("=================================")


if __name__ == "__main__":
    main()