import aiohttp
import logging
import json

class DeviggerAPI:
    def __init__(self, api_url, api_key):
        self.api_url = api_url
        self.api_key = api_key
        self.session = None

    async def get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def calculate_ev(self, odds_str, boost_percent=0, devig_method=None):
        try:
            session = await self.get_session()
            
            # Map user-friendly names to API devig method codes
            devig_method_map = {
                'm': 'Multiplicative',           # Multiplicative
                'a': 'Additive',                 # Additive
                'p': 'Power',                    # Power
                's': 'Shin',                     # Shin
                'wc:p': 'WorstCase_Power',       # Worst-case (power)
                'wc:m': 'WorstCase_Multiplicative', # Worst-case (multiplicative)
                'wc:p,m': 'WorstCase_Power_Multiplicative', # Worst-case (power and multiplicative)
                'wa': 'WeightedAverage',         # Weighted average
                'multiplicative': 'Multiplicative',
                'additive': 'Additive',
                'power': 'Power',
                'shin': 'Shin',
                'worst-case': 'WorstCase_Multiplicative',
                'wc': 'WorstCase_Multiplicative'
            }
            
            # Use worst-case multiplicative as default
            if devig_method is None:
                devig_method_display = 'Worst-case'
                devig_method_code = 'WorstCase_Multiplicative'
            else:
                devig_method_code = devig_method_map.get(devig_method.lower(), devig_method)
                devig_method_display = {
                    'Multiplicative': 'Multiplicative',
                    'Additive': 'Additive',
                    'Power': 'Power',
                    'Shin': 'Shin',
                    'WorstCase_Power': 'Worst-case (Power)',
                    'WorstCase_Multiplicative': 'Worst-case',
                    'WorstCase_Power_Multiplicative': 'Worst-case (Multi/Power)',
                    'WeightedAverage': 'Weighted Average'
                }.get(devig_method_code, devig_method_code)
            
            # Parse odds string - pass it directly to API as LegOdds
            # Format can be: -110/-110 or +285/15% or +285/[-116/-106] etc.
            if ':' not in odds_str:
                return {'success': False, 'error': 'Format: flex/sharp:final or final:fair'}
            
            legs_str, final_str = odds_str.rsplit(':', 1)
            leg_odds_str = legs_str
            
            # Try to extract numeric final odds for display (might have juice specs)
            try:
                final_odds = float(final_str)
            except ValueError:
                # Final has juice spec, try to extract just the number
                final_odds = float(''.join(c for c in final_str if c in '+-0123456789'))
            
            # Build API request parameters - pass odds strings directly
            params = {
                'api': self.api_key,
                'LegOdds': leg_odds_str,
                'FinalOdds': final_str,  # Pass the original string with any juice specs
                'Correlation_Bool': '0',
                'Boost_Bool': '1' if boost_percent > 0 else '0',
                'Boost_Text': str(int(boost_percent)) if boost_percent > 0 else '0',
                'Boost_Type': '0',  # 0 = profit boost
                devig_method_code: '1',  # Use devig method as parameter name with value 1
                'Args': 'ev_p,fb_p,kelly,fo_o'
            }
            
            async with session.get(self.api_url, params=params) as resp:
                if resp.status != 200:
                    return {'success': False, 'error': f'API Error {resp.status}'}
                data = await resp.json()
            
            # Parse response - API returns nested structure
            try:
                final_data = data.get('Final', {})
                ev_percent = final_data.get('EV_Percentage', 0) * 100  # Convert to percentage
                kelly_units = final_data.get('Kelly_Full', 0)  # Already in units, not percentage
                fair_value_odds = final_data.get('FairValue_Odds', final_odds)  # Use API's FV directly
                fb_percent = final_data.get('FB_Percentage', 0) * 100  # Convert to percentage
                
                # Parse leg details - count how many legs are in response
                legs_data = []
                leg_count = 1
                while True:
                    leg_key = f'Leg#{leg_count}'
                    if leg_key not in data:
                        break
                    leg_data = data.get(leg_key, {})
                    legs_data.append({
                        'odds': leg_data.get('Odds', ''),
                        'market_juice': leg_data.get('MarketJuice', 0) * 100,  # Convert to percentage
                        'fair_value': leg_data.get('FairValue', 0)
                    })
                    leg_count += 1
            except:
                return {'success': False, 'error': 'Invalid API response format'}
            
            kelly_half = kelly_units * 0.5
            kelly_quarter = kelly_units * 0.25
            
            return {
                'success': True,
                'data': {
                    'fair_value': fair_value_odds,  # Use the API's fair value directly
                    'ev_percent': ev_percent,
                    'fb_percent': fb_percent,
                    'legs': legs_data,
                    'kelly_quarter': kelly_quarter,
                    'devig_method': devig_method_display,
                    'kelly_data': {
                        'full': kelly_units,
                        'half': kelly_half,
                        'quarter': kelly_quarter
                    },
                    'method': 'worst_case'
                }
            }
        except Exception as e:
            logging.error(f'DeviggerAPI error: {str(e)}')
            return {'success': False, 'error': str(e)}
            return {'success': False, 'error': str(e)}

    async def check_status(self):
        try:
            session = await self.get_session()
            async with session.get(self.api_url, params={'key': self.api_key}) as resp:
                return resp.status == 200
        except:
            return False
