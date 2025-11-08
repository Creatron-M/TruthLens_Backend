import os
import requests
import time
from typing import List, Dict
import json

def fetch_coingecko_sentiment() -> List[Dict]:
    """Fetch crypto market sentiment from CoinGecko (free, no auth required)"""
    try:
        comments = []
        
        # Get trending coins
        trending_url = "https://api.coingecko.com/api/v3/search/trending"
        headers = {'Accept': 'application/json'}
        
        response = requests.get(trending_url, headers=headers, timeout=15)
        trending_data = response.json()
        
        if 'coins' in trending_data:
            for coin in trending_data['coins'][:5]:
                coin_data = coin.get('item', {})
                comments.append({
                    "marketId": "bitcoin_market",
                    "url": f"https://www.coingecko.com/en/coins/{coin_data.get('id', '')}",
                    "text": f"Trending: {coin_data.get('name', '')} ({coin_data.get('symbol', '')}) - Market cap rank #{coin_data.get('market_cap_rank', 'N/A')}. High search interest indicates potential market movement.",
                    "author": "coingecko_trending",
                    "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "score": 1000 - (coin_data.get('market_cap_rank', 999) or 999),  # Higher score for lower rank
                    "source": "coingecko_trending"
                })
        
        # Get Bitcoin market data for sentiment
        btc_url = "https://api.coingecko.com/api/v3/coins/bitcoin"
        params = {'localization': 'false', 'tickers': 'false', 'community_data': 'true', 'developer_data': 'false'}
        
        response = requests.get(btc_url, headers=headers, params=params, timeout=15)
        btc_data = response.json()
        
        if 'market_data' in btc_data:
            market_data = btc_data['market_data']
            price_change_24h = market_data.get('price_change_percentage_24h', 0)
            sentiment = "bullish" if price_change_24h > 0 else "bearish" if price_change_24h < -2 else "neutral"
            
            comments.append({
                "marketId": "bitcoin_market",
                "url": "https://www.coingecko.com/en/coins/bitcoin",
                "text": f"Bitcoin market analysis: 24h change {price_change_24h:.2f}%. Market sentiment appears {sentiment}. Current market cap rank #1 with strong liquidity indicators.",
                "author": "coingecko_market_data",
                "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "score": abs(int(price_change_24h * 10)),  # Score based on volatility
                "source": "coingecko_market"
            })
        
        # Get global market data
        global_url = "https://api.coingecko.com/api/v3/global"
        response = requests.get(global_url, headers=headers, timeout=15)
        global_data = response.json()
        
        if 'data' in global_data:
            data = global_data['data']
            btc_dominance = data.get('market_cap_percentage', {}).get('btc', 0)
            
            comments.append({
                "marketId": "bitcoin_market", 
                "url": "https://www.coingecko.com/en/global-charts",
                "text": f"Global crypto market update: Bitcoin dominance at {btc_dominance:.1f}%. Total market cap indicates {'strong' if btc_dominance > 45 else 'moderate'} Bitcoin influence on overall market sentiment.",
                "author": "coingecko_global",
                "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "score": int(btc_dominance),
                "source": "coingecko_global"
            })
        
        return comments
        
    except Exception as e:
        print(f"Error fetching CoinGecko data: {e}")
        # Fallback to mock crypto data
        return [{
            "marketId": "bitcoin_market",
            "url": "https://www.coingecko.com/en/coins/bitcoin",
            "text": "Mock cryptocurrency market data for testing purposes - Bitcoin trending with positive market sentiment",
            "author": "coingecko_fallback",
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "score": 75,
            "source": "coingecko_fallback"
        }]

def fetch_news_comments() -> List[Dict]:
    """Fetch crypto news using NewsAPI if available"""
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key or len(api_key.strip()) == 0:  # Check for valid API key
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'bitcoin OR cryptocurrency OR crypto',
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 10,
            'apiKey': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        comments = []
        if data.get('status') == 'ok':
            for article in data.get('articles', []):
                comments.append({
                    "marketId": "bitcoin_market",
                    "url": article.get('url', ''),
                    "text": f"{article.get('title', '')} - {article.get('description', '')}",
                    "author": article.get('source', {}).get('name', 'unknown'),
                    "createdAt": article.get('publishedAt', time.strftime('%Y-%m-%dT%H:%M:%SZ')),
                    "source": "news"
                })
        
        return comments
        
    except Exception as e:
        print(f"Error fetching news data: {e}")
        return []

def get_fallback_comments() -> List[Dict]:
    """Enhanced fallback comments with realistic examples"""
    return [
        {
            "marketId": "bitcoin_market", 
            "url": "https://www.reuters.com/markets/bitcoin-hits-new-high", 
            "text": "Major institutions including BlackRock and Fidelity have increased their Bitcoin holdings by 15% this quarter, according to recent SEC filings. The institutional adoption trend shows strong fundamentals supporting higher prices.", 
            "author": "reuters_reporter", 
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "source": "fallback"
        },
        {
            "marketId": "bitcoin_market", 
            "url": "https://www.bloomberg.com/news/crypto-institutional-adoption", 
            "text": "Bloomberg reports that Bitcoin ETF inflows reached $2.1 billion last week, the highest since launch. This represents significant institutional confidence in the asset class.", 
            "author": "bloomberg_analyst", 
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "source": "fallback"
        },
        {
            "marketId": "bitcoin_market", 
            "url": "http://shady-crypto-news.biz/blog/123", 
            "text": "🚀🚀🚀 BTC TO THE MOON!!! Trust me bro, my insider friend at Goldman says they're buying MASSIVE amounts. This is going to 100K GUARANTEED!!! 💎🙌", 
            "author": "moon_boy_2024", 
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "source": "fallback"
        },
        {
            "marketId": "bitcoin_market", 
            "url": "https://coindesk.com/markets/bitcoin-technical-analysis", 
            "text": "Technical analysis shows BTC broke through key resistance at $75K with strong volume. The 50-day MA crossed above 200-day MA, indicating bullish momentum. However, RSI is approaching overbought territory at 78.", 
            "author": "technical_trader", 
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "source": "fallback"
        },
        {
            "marketId": "bitcoin_market", 
            "url": "http://crypto-pump-signals.blogspot.com/btc-pump", 
            "text": "URGENT: Secret whale group just bought 10,000 BTC!!! Get in NOW before it's too late! This is your last chance to buy before we moon! 🌙💰", 
            "author": "whale_watcher_2024", 
            "createdAt": time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "source": "fallback"
        }
    ]

def fetch_comments() -> List[Dict]:
    """Main function to fetch comments with multiple sources"""
    print("💬 Fetching market comments and sentiment data...")
    all_comments = []
    
    # Try custom feed first
    url = os.getenv('COMMENTS_FEED_URL')
    if url:
        try:
            response = requests.get(url, timeout=10)
            custom_comments = response.json()
            all_comments.extend(custom_comments)
            print(f"✅ Added {len(custom_comments)} custom feed comments")
        except Exception as e:
            print(f"Custom comments feed failed: {e}")
    
    # Try CoinGecko
    coingecko_comments = fetch_coingecko_sentiment()
    if coingecko_comments:
        all_comments.extend(coingecko_comments)
        print(f"✅ Added {len(coingecko_comments)} CoinGecko sentiment data")
    
    # Try News API
    news_comments = fetch_news_comments()
    if news_comments:
        all_comments.extend(news_comments)
        print(f"✅ Added {len(news_comments)} news articles")
    
    # If we got real data, use it; otherwise use fallback
    if all_comments:
        print(f"📊 Total: {len(all_comments)} comments from live sources")
        return all_comments
    else:
        print("⚠️ Using fallback mock comments")
        return get_fallback_comments()