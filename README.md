# Music_Geumchi

# Discord Music Bot with yt-dlp (No YouTube API)
This Discord music bot utilizes the powerful yt-dlp library to play music directly from YouTube, bypassing the need for the YouTube Data API. This approach offers several advantages, including:

No API Key Required: Avoid the hassle of obtaining and managing API keys.
Reduced Rate Limiting: Less susceptible to rate limits imposed by the YouTube API.
Direct Stream Access: Access audio streams directly, potentially resulting in higher quality and more reliable playback.
Support for More Sites: yt-dlp supports a wider range of websites beyond YouTube.

## Features
Music Playback: Play music from YouTube URLs or search queries.
Queue Management: Add songs to a queue and manage playback order.
Looping: Loop the current song.
Song Skipping: Skip the current song.
Song Statistics: Track the most played songs.
Top Songs List: Display the top 5 most played songs.

# Install
Tested in 3.11.

Install FFmpeg
Windows: Follow the instructions at https://www.geeksforgeeks.org/how-to-install-ffmpeg-on-windows/ to install FFmpeg on your Windows system.   
Linux: Use your distribution's package manager (e.g., apt-get install ffmpeg on Debian/Ubuntu, yum install ffmpeg on CentOS/RHEL).
macOS: Use Homebrew (brew install ffmpeg).

Clone the Repository
```
git clone https://github.com/your-username/discord-music-bot.git
```

Install Dependencies
```
pip install -r requirements.txt
```

Configure Environment Variables
Rename example.env into .env
Add your Discord bot token: BOT_TOKEN=your_bot_token

Run the Server and Bot
```
python server.py
python bot.py
```
