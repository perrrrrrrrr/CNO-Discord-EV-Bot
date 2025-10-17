import aiohttp
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
