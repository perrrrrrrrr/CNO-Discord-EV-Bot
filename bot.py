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
        devig_method = None
        
        # Parse input - format: odds [boost] [devig_method]
        parts = odds_input.split()
        odds_str = parts[0]
        
        # Check for boost (numeric)
        if len(parts) > 1:
            try:
                boost_percent = float(parts[1])
                # Check for devig method (non-numeric)
                if len(parts) > 2:
                    devig_method = parts[2]
            except ValueError:
                # parts[1] is not a number, might be devig method
                devig_method = parts[1]
        
        # Pass the odds string directly to API - it handles juice specifications
        # Format: flex/sharp:final or with juice like +285/15%:+300
        result = await devigger_api.calculate_ev(odds_str, boost_percent, devig_method)
        if not result.get('success'):
            await ctx.send(f'Error: {result.get("error")}')
            return
        
        data = result['data']
        embed = discord.Embed(color=discord.Color.green() if data['ev_percent'] > 0 else discord.Color.red())
        
        # Expected Value section
        ev_emoji = '✅' if data['ev_percent'] > 0 else '💩'
        embed.add_field(name=f'{ev_emoji} Expected Value', value=f"EV: {data['ev_percent']:.2f}%", inline=False)
        
        # Worst-case method section with leg details
        legs_text = "Worst-case: (Multiplicative)\n"
        for i, leg in enumerate(data.get('legs', []), 1):
            odds_str = leg.get('odds', '')
            juice = leg.get('market_juice', 0)
            fv_prob = leg.get('fair_value', 0)  # This is already a probability (decimal)
            # Convert probability to odds
            if fv_prob > 0 and fv_prob < 1:
                fv_odds = (100 * (1 - fv_prob)) / fv_prob if fv_prob >= 0.5 else -(100 * fv_prob) / (1 - fv_prob)
            else:
                fv_odds = 0
            legs_text += f"Leg#{i} ({odds_str}); Market Juice = {juice:.1f}%; Fair Value = {fv_odds:+.0f} ({fv_prob*100:.1f}%)\n"
        embed.add_field(name='📊 Worst-case Analysis', value=legs_text.strip(), inline=False)
        
        # Odds section - show final odds from the input
        odds_text = f"Final: {odds_str}"
        if boost_percent > 0:
            odds_text = f"Final Boost: {odds_str} (+{boost_percent}%)"
        embed.add_field(name='📍 Odds', value=odds_text, inline=False)
        
        # Fair Value & Kelly
        kelly_data = data.get('kelly_data', {})
        kelly_full = kelly_data.get('full', 0)
        kelly_half = kelly_data.get('half', 0)
        kelly_quarter = kelly_data.get('quarter', 0)
        fb_percent = data.get('fb_percent', 0)
        devig_method_display = data.get('devig_method', 'Worst-case')
        
        fv_kelly_text = f"FV: {data['fair_value']:+.0f}, Method: {devig_method_display}\n"
        fv_kelly_text += f"(Full={kelly_full:.2f}u, 1/2={kelly_half:.2f}u, 1/4={kelly_quarter:.2f}u, FB={fb_percent:.2f}%)"
        embed.add_field(name='⚖️ Fair Value & Kelly', value=fv_kelly_text, inline=False)
        
        await ctx.send(embed=embed)
        await ctx.message.remove_reaction('🧠', bot.user)
        await ctx.message.add_reaction('✅')
    except Exception as e:
        logger.error(str(e), exc_info=True)
        await ctx.send(f'Error: {str(e)}')

@bot.command(name='help_ev')
async def help_ev(ctx):
    embed = discord.Embed(title='Help - EV Calculator', color=discord.Color.blue())
    embed.add_field(name='Simple', value='`!ev 450:350`\n`!ev -110/-110:300`', inline=False)
    embed.add_field(name='With Boost', value='`!ev 450:350 49`', inline=False)
    embed.add_field(name='With Devig Method', value='`!ev 450:350 m`\n`!ev 450:350 49 m`', inline=False)
    embed.add_field(name='Juice Examples', value='`!ev +285/15%:+300`\n`!ev +285/[-116/-106]:+300`\n`!ev -270/[-135=-110/-110]:+300`\n`!ev +600/%:+300`', inline=False)
    embed.add_field(name='Devig Methods', value='`m` (Mult), `a` (Add), `p` (Power), `s` (Shin), `wc` (worst-case, default)', inline=False)
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
