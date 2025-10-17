import os

os.makedirs('utils', exist_ok=True)

devigger_code = """import aiohttp
import logging

class DeviggerAPI:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def calculate_ev(self, flex_odds, sharp_odds, final_odds, boost_percent=0):
        try:
            session = await self.get_session()
            num_legs = len(flex_odds)
            params = {'key': self.api_key, 'sport': 'sportsbook'}
            
            for i in range(num_legs):
                params[f'sportsbook_{i+1}'] = flex_odds[i]
                params[f'sharp_{i+1}'] = sharp_odds[i]
            
            params['finalodds'] = final_odds
            async with session.get(self.api_url, params=params) as resp:
                if resp.status != 200:
                    return {'success': False, 'error': f'API Error {resp.status}'}
                data = await resp.json()
            
            fair_value = data.get('fair_value', final_odds)
            ev_percent = ((final_odds - fair_value) / fair_value * 100) if fair_value != 0 else 0
            kelly_full = (final_odds * 0.55 - 1) / (final_odds - 1) if final_odds > 1 else 0
            kelly_quarter = kelly_full * 0.25
            
            return {
                'success': True,
                'data': {
                    'fair_value': fair_value,
                    'ev_percent': ev_percent,
                    'kelly_quarter': kelly_quarter,
                    'method': 'worst_case'
                }
            }
        except Exception as e:
            logging.error(f'DeviggerAPI error: {str(e)}')
            return {'success': False, 'error': str(e)}

    async def check_status(self):
        try:
            session = await self.get_session()
            async with session.get(self.api_url, params={'key': self.api_key}) as resp:
                return resp.status == 200
        except:
            return False
"""

bot_code = """import discord
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
"""

with open('utils/devigger_api.py', 'w', encoding='utf-8') as f:
    f.write(devigger_code)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(bot_code)

print('Created bot.py and utils/devigger_api.py')
