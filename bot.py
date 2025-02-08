# MIT License
#
# Copyright (c) 2024 Gaegeumchi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# Feel free to reach out to me on Discord @Gaegeumchi
#
# While you're welcome to use, modify, and distribute this code as you see fit, 
# I would greatly appreciate it if you could kindly remember and acknowledge me, 
# the original developer, in your future projects or endeavors that utilize 
# or are inspired by this work. Thank you!

import discord
from discord.ext import commands
import aiohttp
import asyncio
from collections import defaultdict
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('BOT_TOKEN')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

SERVER_URL = "http://localhost:5000" # Your server address

song_stats = defaultdict(int) # {Song title: Play count}
music_queue = defaultdict(list) 
current_voice_clients = {}
loop_status = defaultdict(bool) 

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -af "volume=0.8"',
}


# Resets song statistics every 12 hours
async def reset_song_stats():
    while True:
        await asyncio.sleep(12 * 60 * 60)
        print(f"[{datetime.datetime.now()}] Resetting song statistics.")
        song_stats.clear()

# Checks voice channel status every 10 seconds and disconnects the bot if conditions are met.
async def check_voice_channels():
    while True:
        await asyncio.sleep(10) # Check every 10 seconds
        for guild_id, voice_client in list(current_voice_clients.items()):
            if not voice_client.is_playing() and (not voice_client.channel.members or len(music_queue[guild_id]) == 0):
                await voice_client.disconnect()
                current_voice_clients.pop(guild_id, None)
                music_queue.pop(guild_id, None)
                loop_status.pop(guild_id, None)
                print(f"[{datetime.datetime.now()}] Bot disconnected due to empty voice channel or queue. (Guild ID: {guild_id})")

# Plays music
async def play_music(interaction, guild_id):
    if not music_queue[guild_id]:
        return

    voice_client = current_voice_clients.get(guild_id)
    if not voice_client or not voice_client.is_connected():
        channel = interaction.user.voice.channel
        voice_client = await channel.connect()
        current_voice_clients[guild_id] = voice_client

    if not voice_client.is_playing():
        url, title, thumbnail, author = music_queue[guild_id].pop(0)

        # Update song statistics
        song_stats[title] += 1

        voice_client.play(
            discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(interaction, guild_id, url, title, thumbnail, author), bot.loop
            )
        )
        embed = discord.Embed(title="🎵 Now Playing", description=f"**{title}**", color=discord.Color.blue())
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=f"{author}")
        await interaction.followup.send(embed=embed)

# Plays the next song.
async def play_next(interaction, guild_id, url, title, thumbnail, author):
    if loop_status[guild_id]:
        music_queue[guild_id].append((url, title, thumbnail, author))  # Add the current song back to the queue for looping

    if music_queue[guild_id]:
        await play_music(interaction, guild_id)
    else:
        if not hasattr(play_next, 'message_sent'):
            await interaction.channel.send("No more songs in the queue.")
            play_next.message_sent = True
        else:
            play_next.message_sent = False


@bot.tree.command(name="play", description="Plays music from a YouTube URL or search query.")
async def play(interaction: discord.Interaction, query: str):
    guild_id = interaction.guild.id
    if guild_id not in music_queue:
        music_queue[guild_id] = []
    try:
        await interaction.response.defer()
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{SERVER_URL}/play", json={"query": query, "guild_id": str(guild_id), "user": interaction.user.name}) as resp:
                response = await resp.json()
        print("Server response:", response)
        if response.get("status") == "error": # Handle cases where status is "error"
            await interaction.followup.send(f"❌ {response['message']}")
            return

        if "audio_url" not in response:
            await interaction.followup.send(f"❌ Invalid data received from the server: {response}")
            return

        music_queue[guild_id].append((response["audio_url"], response["title"], response["thumbnail"], interaction.user.name))

        embed = discord.Embed(title="✅ Added to Queue", description=f"**{response['title']}**", color=discord.Color.green())
        embed.set_thumbnail(url=response["thumbnail"])
        embed.set_footer(text=f"{interaction.user.name}")
        await interaction.followup.send(embed=embed)

        voice_client = current_voice_clients.get(guild_id)
        if not voice_client or not voice_client.is_playing():
            await play_music(interaction, guild_id)

    except Exception as e:
        await interaction.followup.send(f"❌ An error occurred: {e}")
        print(f"An error occurred: {e}")


@bot.tree.command(name="loop", description="Loops the current song.")
async def loop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    loop_status[guild_id] = not loop_status[guild_id]
    status = "Enabled" if loop_status[guild_id] else "Disabled"
    await interaction.response.send_message(f"🔁 Loop playback is **{status}**.")


@bot.tree.command(name="list", description="View the queue.")
async def list_queue(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    if not music_queue[guild_id]:
        await interaction.response.send_message("The queue is empty.")
        return

    msg = "\n".join([f"{i+1}. {item[1]}" for i, item in enumerate(music_queue[guild_id])])
    await interaction.response.send_message(f"🎶 Queue:\n{msg}")


@bot.tree.command(name="top", description="View the top 5 most played songs.")
async def top(interaction: discord.Interaction):
    if not song_stats:
        await interaction.response.send_message("No song data in the current statistics.")
        return

    sorted_stats = sorted(song_stats.items(), key=lambda x: x[1], reverse=True)
    top_songs = sorted_stats[:5]

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    embed = discord.Embed(title="🎶 Top 5 Most Played Songs", color=discord.Color.gold())
    for rank, (title, count) in enumerate(top_songs, start=1):
        embed.add_field(name=f"#{rank} - {title}", value=f"Play Count: {count} times", inline=False)
    embed.set_footer(text=f"Statistics Time: {current_time}")

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="skip", description="Skips the current song.")
async def skip(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    voice_client = current_voice_clients.get(guild_id)

    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭ Skipping the song.")
        await play_next(interaction, guild_id, None, None, None, None)  # Play the next song
    else:
        await interaction.response.send_message("There is no song playing.")


@bot.tree.command(name="stop", description="Stops playback and leaves the voice channel.")
async def stop(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    voice_client = current_voice_clients.get(guild_id)

    if voice_client:
        await voice_client.disconnect()
        current_voice_clients.pop(guild_id, None)
        music_queue.pop(guild_id, None)
        loop_status.pop(guild_id, None)
        await interaction.response.send_message("⏹ Stopped playback and left the voice channel.")
    else:
        await interaction.response.send_message("Not connected to a voice channel.")


@bot.event
async def on_ready():
    print(f"Bot logged in: {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Music"))
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands {len(synced)} synced.")
    except Exception as e:
        print(f"Error syncing commands: {e}")

    asyncio.create_task(check_voice_channels())
    asyncio.create_task(reset_song_stats())  # Refresh song lists

bot.run(TOKEN)
