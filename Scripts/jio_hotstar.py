import os
import requests
from pathlib import Path

API_URL = os.environ.get("HOTSTAR_API_URL")

if not API_URL:
    raise RuntimeError("HOTSTAR_API_URL secret is not configured")

OUTPUT_FILE = Path("jio_hotstar.m3u")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def fetch_channels():
    response = requests.get(
        API_URL,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        raise ValueError("Invalid API response: expected JSON array")

    return data


def build_playlist(channels):
    lines = ["#EXTM3U"]
    count = 0

    for channel in channels:
        name = str(channel.get("name") or "Unknown")
        logo = str(channel.get("logo") or "")
        group = str(channel.get("group") or "Other")
        mpd_url = str(channel.get("mpd_url") or "")

        key_id = channel.get("keyId")
        key = channel.get("key")

        if not mpd_url:
            continue

        lines.append(
            f'#EXTINF:-1 tvg-name="{name}" '
            f'tvg-logo="{logo}" '
            f'group-title="{group}",{name}'
        )

        lines.append(
            "#KODIPROP:inputstream.adaptive.manifest_type=mpd"
        )

        if key_id and key:
            lines.append(
                "#KODIPROP:inputstream.adaptive.license_type="
                "org.w3.clearkey"
            )

            lines.append(
                f"#KODIPROP:inputstream.adaptive.license_key="
                f"{key_id}:{key}"
            )

        lines.append(mpd_url)

        count += 1

    return "\n".join(lines) + "\n", count


def main():
    print("Fetching Hotstar API...")

    channels = fetch_channels()

    playlist, count = build_playlist(channels)

    OUTPUT_FILE.write_text(
        playlist,
        encoding="utf-8"
    )

    print(f"Playlist generated successfully.")
    print(f"Total channels: {count}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
