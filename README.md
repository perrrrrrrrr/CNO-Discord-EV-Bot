# Discord Betting Bot with Ollama & Devigger API

A Discord bot that analyzes sports betting odds images using Ollama vision models and calculates expected value (EV) using the Crazy Ninja Devigger API.

## Features

- 📸 **Image Analysis**: Upload betting odds screenshots and let Ollama extract all the data
- 🧮 **EV Calculation**: Automatically calculate expected value using worst-case scenario
- 🎯 **Best Bet Finder**: Find the optimal combination of legs for maximum EV
- 💰 **Boost Support**: Factor in sportsbook boosts to your EV calculations
- 🤖 **Easy Discord Commands**: Simple commands for analyzing bets

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.ai/) installed and running locally
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- Ollama vision model (llava or similar) downloaded

## Installation

### 1. Clone or Download this Project

```powershell
cd "C:\Projects\AI Devigger"
```

### 2. Install Ollama

Download and install Ollama from https://ollama.ai/

Then download a vision model:
```powershell
ollama pull llava
```

### 3. Create Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your Discord bot token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

## Getting a Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section in the left sidebar
4. Click "Add Bot"
5. Under the TOKEN section, click "Reset Token" to reveal your token
6. Copy the token and paste it into your `.env` file
7. Enable these Privileged Gateway Intents:
   - Message Content Intent
8. Go to OAuth2 → URL Generator
9. Select scopes: `bot`
10. Select permissions: `Send Messages`, `Embed Links`, `Attach Files`, `Read Message History`
11. Copy the generated URL and use it to invite the bot to your server

## Usage

### Start the Bot

```powershell
python bot.py
```

### Discord Commands

Once the bot is running and in your Discord server:

#### 1. Analyze Betting Odds Image
```
!analyze
```
Attach an image of betting odds when you send this command. The bot will use Ollama to extract all betting lines.

#### 2. Calculate Best EV Bet
```
!calculate <num_legs> <boost_percent>
```
**Examples:**
- `!calculate 2 0` - Find best 2-leg parlay with no boost
- `!calculate 3 50` - Find best 3-leg parlay with 50% boost
- `!calculate 4 25` - Find best 4-leg parlay with 25% boost

#### 3. Check Bot Status
```
!status
```
Check if Ollama and other services are connected properly.

#### 4. Clear Stored Bets
```
!clear
```
Clear the betting odds stored for your channel.

#### 5. Help
```
!help
```
Display all available commands.

## How It Works

1. **Image Upload**: You upload a screenshot of betting odds to Discord
2. **Ollama Analysis**: The bot sends the image to your local Ollama instance with a vision model (llava)
3. **Data Extraction**: Ollama reads the image and extracts team names, odds, markets, and leagues
4. **EV Calculation**: The bot sends all possible leg combinations to the Crazy Ninja Devigger API
5. **Optimization**: It finds the combination with the highest EV using worst-case scenario
6. **Recommendation**: The bot shows you the best bet and whether it has positive EV

## API Reference

### Crazy Ninja Devigger API

The bot uses the open API endpoint:
- **URL**: `http://api.crazyninjaodds.com/api/devigger/v1/sportsbook_devigger.aspx`
- **Documentation**: http://crazyninjamike.com/Public/sportsbooks/sportsbook_devigger_help.aspx
- **API Key**: `open` (no authentication required)

### Ollama

- **Default Host**: `http://localhost:11434`
- **Model**: `llava` (vision model)
- Can be configured in `.env` file

## Configuration

Edit `.env` file to customize:

```ini
# Discord Bot Token (REQUIRED)
DISCORD_TOKEN=your_discord_bot_token_here

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llava

# Devigger API
DEVIGGER_API_URL=http://api.crazyninjaodds.com/api/devigger/v1/sportsbook_devigger.aspx
DEVIGGER_API_KEY=open

# Bot Settings
COMMAND_PREFIX=!
LOG_LEVEL=INFO
```

## Troubleshooting

### Bot won't start
- Make sure you've set `DISCORD_TOKEN` in your `.env` file
- Ensure you've activated your virtual environment
- Check that all dependencies are installed: `pip install -r requirements.txt`

### Ollama errors
- Make sure Ollama is running: Open a terminal and type `ollama serve`
- Check that you've downloaded a vision model: `ollama pull llava`
- Verify Ollama is accessible at `http://localhost:11434`

### Image analysis not working
- Ensure the image is clear and betting odds are visible
- Try different Ollama vision models (e.g., `llava:13b`, `bakllava`)
- Check Ollama logs for errors

### EV calculation failing
- Verify internet connection (Devigger API is online)
- Check that odds are in American format (+150, -110, etc.)
- Review bot logs for API errors

## Project Structure

```
AI Devigger/
├── bot.py                 # Main Discord bot
├── utils/
│   ├── ollama_analyzer.py # Ollama image analysis
│   └── devigger_api.py    # Devigger API client
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from .env.example)
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Development

### Adding New Features

The bot is modular:
- `bot.py` - Discord commands and bot logic
- `utils/ollama_analyzer.py` - Image analysis functionality
- `utils/devigger_api.py` - EV calculation logic

### Logging

Logs are written to console. Adjust log level in `.env`:
```ini
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Support

For issues or questions:
1. Check Ollama is running: `ollama serve`
2. Verify Discord bot token is valid
3. Check logs for error messages
4. Ensure all dependencies are installed

## License

This project is for educational purposes. Please gamble responsibly and check your local laws regarding sports betting.

## Credits

- [Ollama](https://ollama.ai/) - Local AI models
- [Crazy Ninja Odds](http://crazyninjamike.com/) - Devigger API
- [discord.py](https://discordpy.readthedocs.io/) - Discord bot library
