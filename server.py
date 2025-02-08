# MIT License
# Copyright (c) 2024 Gaegeumchi

from flask import Flask, jsonify, request
import yt_dlp
import os
import asyncio
from collections import defaultdict

app = Flask(__name__)

# Set the download directory
DOWNLOAD_DIR = "downloads"

# Create the download directory if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)
    print(f"Created the {DOWNLOAD_DIR} directory.")
else:
    print(f"The {DOWNLOAD_DIR} directory already exists.")

# Manage music queue and status (centralized management on the server side)
music_queue = defaultdict(list)
current_voice_clients = {}
loop_status = defaultdict(bool)
song_stats = defaultdict(int)

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    # 'extract_flat': True # Added to get playback time information
}

@app.route('/play', methods=['POST'])
def add_to_queue():
    data = request.json
    query = data.get('query')
    guild_id = data.get('guild_id')
    user = data.get('user')

    try:
        if query.startswith("http"):
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                info = ydl.extract_info(query, download=False)
                print("yt_dlp extracted information:", info)

                # Check audio length (in seconds)
                duration = info.get('duration', 0)
                if duration > 30 * 60:
                    return jsonify({"status": "error", "message": "The audio is longer than 30 minutes."})

                title = info.get('title', 'No Title')
                thumbnail = info.get('thumbnail', '')
                audio_url = info.get('url')
        else:
            audio_url, title, thumbnail, _ = search_youtube(query)

        if not audio_url:
            return jsonify({"status": "error", "message": "Could not find the audio URL."})

        music_queue[guild_id].append((audio_url, title, thumbnail, user))
        song_stats[title] += 1
        return jsonify({"status": "success", "title": title, "thumbnail": thumbnail, "audio_url": audio_url})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/queue/<guild_id>', methods=['GET'])
def get_queue(guild_id):
    return jsonify({"queue": music_queue.get(guild_id, [])})

# downloader.py modification (modified search_youtube function)
def search_youtube(query):
    with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        print("yt-dlp search_youtube info:", info)
        print("URL:", info.get('url'))
        print("Thumbnail:", info.get('thumbnail'))

        # Check audio length (in seconds)
        duration = info.get('duration', 0)

        # Uncomming the length limit may cause issues with title search and thumbnail retrieval, so it's best to keep it commented out unless specifically needed.
        # if duration > 30 * 60:
        #     return None, "Audio longer than 30 minutes", None, None

        return info['url'], info['title'], info.get('thumbnail', ''), info['uploader']

if __name__ == "__main__":
    app.run(port=5000, debug=True)