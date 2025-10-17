import discord
from discord.ext import commands
import os
import logging
from dotenv import load_dotenv
from utils.devigger_api import DeviggerAPI

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
devigger_api = DeviggerAPI(api_url=os.getenv('DEVIGGER_API_URL', 'http://api.crazyninjaodds.com/api/devigger/v1/sportsbook_devigger.aspx'), api_key=os.getenv('DEVIGGER_API_KEY', 'open'))

@bot.event
async def on_ready():
    logger.info(f'{bot.user} connected')
    activity = discord.Activity(type=discord.ActivityType.watching, name='for betting odds | !help_ev')
    await bot.change_presence(activity=activity)

@bot.command(name='ev')
async def calculate_ev(ctx, *, odds_input: str):
    try:
        await ctx.message.add_reaction('🧠')
        boost_percent = 0
        parts = odds_input.rsplit(None, 1)
        if len(parts) == 2:
            try:
                boost_percent = float(parts[1])
                odds_str = parts[0]
            except ValueError:
                odds_str = odds_input
        else:
            odds_str = odds_input
        
        if '/' in odds_str:
            if ':' not in odds_str:
                await ctx.send('Format: flex/sharp:final')
                return
            legs_str, final_str = odds_str.rsplit(':', 1)
            flex_odds, sharp_odds = [], []
            for pair in legs_str.split(','):
                f, s = pair.strip().split('/')
                flex_odds.append(float(f))
                sharp_odds.append(float(s))
            final_odds = float(final_str)
        else:
            if ':' not in odds_str:
                await ctx.send('Format: final:fair')
                return
            f, s = odds_str.split(':')
            flex_odds = [float(f)]
            sharp_odds = [float(s)]
            final_odds = float(f)
        
        if boost_percent > 0:
            final_odds = final_odds * (1 + boost_percent / 100)
        
        result = await devigger_api.calculate_ev(flex_odds, sharp_odds, final_odds, boost_percent)
        if not result.get('success'):
            await ctx.send(f'Error: {result.get("error")}')
            return
        
        data = result['data']
        embed = discord.Embed(title='EV Results', color=discord.Color.green() if data['ev_percent'] > 0 else discord.Color.red(), description=f'EV: {data["ev_percent"]:.2f}%')
        
        for i, (flex, sharp) in enumerate(zip(flex_odds, sharp_odds), 1):
            embed.add_field(name=f'Leg #{i}', value=f'Flex: {flex:+.0f} | Sharp: {sharp:+.0f}', inline=False)
        
        embed.add_field(name='Final', value=f'{final_odds:+.0f}', inline=False)
        embed.add_field(name='Fair', value=f'{data["fair_value"]:+.2f}', inline=False)
        embed.add_field(name='Kelly 1/4', value=f'{data["kelly_quarter"]:.4f}', inline=False)
        embed.add_field(name='Method', value='Worst-case', inline=False)
        
        await ctx.send(embed=embed)
        await ctx.message.remove_reaction('🧠', bot.user)
        await ctx.message.add_reaction('✅')
    except Exception as e:
        logger.error(str(e), exc_info=True)
        await ctx.send(f'Error: {str(e)}')

@bot.command(name='help_ev')
async def help_ev(ctx):
    embed = discord.Embed(title='Help', color=discord.Color.blue())
    embed.add_field(name='Simple', value='`!ev 450:350`', inline=False)
    embed.add_field(name='With Boost', value='`!ev 450:350 49`', inline=False)
    embed.add_field(name='Complex', value='`!ev -125/100,-200/150:600`', inline=False)
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status(ctx):
    embed = discord.Embed(title='Status', color=discord.Color.green())
    embed.add_field(name='Bot', value='Online', inline=True)
    api_ok = await devigger_api.check_status()
    embed.add_field(name='API', value='Online' if api_ok else 'Offline', inline=True)
    await ctx.send(embed=embed)

if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
