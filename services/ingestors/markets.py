import os
import requests
from typing import List, Dict

def fetch_coingecko_data() -> List[Dict]:
    """Fetch real-time crypto market data from CoinGecko (free)"""
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': 'bitcoin,ethereum,binancecoin',
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        markets = []
        for coin_id, coin_data in data.items():
            # Create mock price history for the last 24h
            current_price = coin_data['usd']
            change_24h = coin_data.get('usd_24h_change', 0)
            
            # Simulate price history
            price_24h = []
            for i in range(7):  # Last 7 data points
                variance = (change_24h / 100) * (i / 6)
                historical_price = current_price * (1 - variance)
                price_24h.append(round(historical_price, 2))
            
            # Simulate volume history
            current_volume = coin_data.get('usd_24h_vol', 1000000)
            volume_24h = []
            for i in range(7):
                volume_variance = 0.1 * (0.5 - (i % 3) / 6)
                volume = current_volume * (1 + volume_variance)
                volume_24h.append(int(volume))
            
            markets.append({
                "marketId": f"{coin_id.replace('-', '_')}_market",
                "question": f"Will {coin_id.title()} price be above ${current_price * 1.1:.2f} next week?",
                "price24h": price_24h,
                "volume24h": volume_24h,
                "current_price": current_price,
                "market_cap": coin_data.get('usd_market_cap', 0),
                "change_24h": change_24h
            })
        
        return markets
        
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        return []

def get_fallback_data() -> List[Dict]:
    """Fallback mock data when APIs are unavailable"""
    return [{
        "marketId": "bitcoin_market",
        "question": "Will BTC close above $80k this month?",
        "price24h": [42000, 43500, 44700, 46100, 45900, 47000, 48200],
        "volume24h": [1000000, 1200000, 950000, 5000000, 600000, 700000, 800000],
        "current_price": 48200,
        "market_cap": 950000000000,
        "change_24h": 2.5
    }]

def fetch_markets() -> List[Dict]:
    """Main function to fetch market data with multiple fallbacks"""
    print("📊 Fetching real-time market data from external APIs...")
    
    # Try custom feed first
    url = os.getenv('MARKET_FEED_URL')
    if url:
        try:
            response = requests.get(url, timeout=10)
            print("✅ Using custom market feed")
            return response.json()
        except Exception as e:
            print(f"Custom feed failed: {e}")
    
    # Try CoinGecko (rate limited - use sparingly)
    coingecko_data = fetch_coingecko_data()
    if coingecko_data and len(coingecko_data) > 0:
        print(f"✅ Using CoinGecko data ({len(coingecko_data)} markets) - API call made")
        return coingecko_data
    
    # Fallback to mock data
    print("⚠️ Using fallback mock data")
    return get_fallback_data()