# 🎵 Mystogan-Bot

**Mystogan-Bot** is a high-performance music bot for Discord, built from the ground up to deliver a rich, seamless music experience. Built with a modern architecture using Python and `discord.py`, this bot focuses on stability, efficiency, and an intuitive, interactive user interface.

![Example image of the bot's player] ## ✨ Key Features

-   **High-Quality Playback**: Uses `yt-dlp` to fetch audio from YouTube and YouTube Music, always prioritizing the best available quality.
-   **Interactive UI**: Control playback entirely through buttons (`Back`, `Pause/Resume`, `Skip`, `Stop`), keeping the chat clean.
-   **Lazy Loading**: Playlists of any size are added to the queue instantly. Song details are only fetched right before playback, making the bot feel incredibly fast.
-   **Unified "Now Playing" Panel**: The player message displays not only the current track but also the next songs in the queue, all in a single, self-updating embed.
-   **Advanced Queue System**: Add individual songs or full playlists, and view upcoming tracks with a paginated `!queue` command.
-   **Playback History**: Loved the song that just ended? Use the "Back" button to listen to it again.
-   **Automatic Disconnect**: The bot intelligently leaves the voice channel if it's left alone or if the queue ends and remains inactive, saving resources.
-   **Modern Architecture**: Built on a solid foundation using dependency injection (`dependency-injector`) and Cogs for better organization and scalability.
-   **Detailed Logging**: Logs all activity and errors to a `bot_music.log` file for easy debugging.

## 🛠️ Tech Stack

-   **Language**: Python 3.10+
-   **Discord Library**: `discord.py`
-   **Audio Extraction**: `yt-dlp`
-   **Dependency Management**: `PDM`
-   **Architecture**: `dependency-injector`
-   **Audio Processing**: `imageio-ffmpeg`

## 🚀 Getting Started

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/mystogan-bot.git](https://github.com/your-username/mystogan-bot.git)
    cd mystogan-bot
    ```

2.  **Install dependencies with PDM:**
    ```bash
    pdm install
    ```

3.  **Set up your environment variables:**
    Create a `.env` file in the project root and add your Discord token:
    ```
    BOT_DISCORD_TOKEN="YOUR_TOKEN_HERE"
    ```

4.  **Run the bot:**
    ```bash
    pdm run start
    ```