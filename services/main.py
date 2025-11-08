from typing import Optional, Dict, List
from datetime import datetime
import asyncio
import time

from .models import MarketData, OracleReading, AnalysisResult, CustomQueryRequest, CustomQueryResponse, OracleStatus

# External dependencies
from .ingestors.markets import fetch_markets
from .ingestors.comments import fetch_comments
from .scoring.credibility import credibility_score
from .scoring.risk import risk_score
from .blockchain.client import submit_attestation, read_latest
from .utils.bytes32 import to_bytes32
from .utils.ipfs import put_json

# Enhanced AI services
try:
    from .ai.batch_processor import queue_analysis, process_urgent, flush_queue, get_processing_status
    from .ai.cache_manager import ai_cache
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    print("Enhanced AI services not available")

# ======================
# In-memory state (use Redis/DB in production)
# ======================

import threading
analysis_cache: Dict[str, AnalysisResult] = {}
markets_cache: Dict[str, any] = {}  # Cache for markets data
comments_cache: Dict[str, any] = {}  # Cache for comments data
ai_analysis_cache: Dict[str, any] = {}  # Cache for AI analysis results
cache_lock = threading.Lock()  # Thread safety for cache access
oracle_status = OracleStatus(
    total_markets=0,
    active_analyses=0,
    total_attestations=0,
    last_update=0,
    blockchain_connected=True
)

# Cache settings for MVP - EXTENDED intervals to minimize API calls
MARKETS_CACHE_TTL = 1800  # 30 minutes cache for markets data
COMMENTS_CACHE_TTL = 3600  # 60 minutes cache for comments data
ANALYSIS_CACHE_TTL = 7200  # 2 hours cache for AI analysis results

# ======================
# Service helpers
# ======================

def transform_markets(raw_markets: List[Dict]) -> List[MarketData]:
    markets: List[MarketData] = []
    for market in raw_markets:
        markets.append(MarketData(
            market_id=market.get('marketId', market.get('market_id', 'unknown')),
            name=market.get('marketId', '').replace('_market', '').replace('_', ' ').title(),
            question=market.get('question', 'Market analysis'),
            price_24h=market.get('price24h', market.get('price_24h', [])),
            volume_24h=market.get('volume24h', market.get('volume_24h', [])),
            current_price=market.get('current_price', 0),
            market_cap=market.get('market_cap', 0),
            change_24h=market.get('change_24h', 0)
        ))
    return markets

# ======================
# Public service functions used by routers
# ======================

def get_cached_markets() -> List[Dict]:
    """Get markets data with caching to reduce API calls"""
    current_time = time.time()
    
    with cache_lock:
        # Check if we have fresh cached data
        if ('markets_data' in markets_cache and 
            'timestamp' in markets_cache and
            current_time - markets_cache['timestamp'] < MARKETS_CACHE_TTL):
            print(f"✅ Using cached markets data (age: {int(current_time - markets_cache['timestamp'])}s)")
            return markets_cache['markets_data']
    
    # Cache miss or expired - fetch new data
    print("📊 Fetching fresh market data (cache miss/expired)...")
    raw_markets = fetch_markets()
    
    with cache_lock:
        markets_cache['markets_data'] = raw_markets
        markets_cache['timestamp'] = current_time
    
    return raw_markets

def get_cached_comments() -> List[Dict]:
    """Get comments data with EXTENDED caching to reduce API calls"""
    current_time = time.time()
    
    with cache_lock:
        # Check if we have fresh cached data
        if ('comments_data' in comments_cache and 
            'timestamp' in comments_cache and
            current_time - comments_cache['timestamp'] < COMMENTS_CACHE_TTL):
            print(f"✅ Using cached comments data (age: {int(current_time - comments_cache['timestamp'])}s)")
            return comments_cache['comments_data']
    
    # Cache miss or expired - fetch new data
    print("💬 Fetching fresh comments data (cache miss/expired)...")
    comments = fetch_comments()
    
    with cache_lock:
        comments_cache['comments_data'] = comments
        comments_cache['timestamp'] = current_time
        print(f"💾 Comments cached for {COMMENTS_CACHE_TTL/60:.0f} minutes")
    
    return comments

def get_cached_ai_analysis(question_hash: str) -> Optional[Dict]:
    """Get cached AI analysis to reduce OpenAI API calls"""
    current_time = time.time()
    
    with cache_lock:
        if (question_hash in ai_analysis_cache and 
            current_time - ai_analysis_cache[question_hash]['timestamp'] < ANALYSIS_CACHE_TTL):
            age_minutes = (current_time - ai_analysis_cache[question_hash]['timestamp']) / 60
            print(f"✅ Using cached AI analysis (age: {age_minutes:.1f} minutes)")
            return ai_analysis_cache[question_hash]['result']
    
    return None

def cache_ai_analysis(question_hash: str, result: Dict):
    """Cache AI analysis result to reduce future OpenAI calls"""
    current_time = time.time()
    
    with cache_lock:
        ai_analysis_cache[question_hash] = {
            'result': result,
            'timestamp': current_time
        }
        print(f"💾 AI analysis cached for {ANALYSIS_CACHE_TTL/60:.0f} minutes")

def get_markets_service() -> List[MarketData]:
    raw_markets = get_cached_markets()
    return transform_markets(raw_markets)

def get_oracle_reading_service(market_id: str) -> OracleReading:
    # Check cache first
    if market_id in analysis_cache:
        cached = analysis_cache[market_id]
        return OracleReading(
            market_id=market_id,
            cred_score=cached.credibility_score,
            risk_index=cached.risk_index,
            meta_uri=cached.ipfs_hash or "",
            signer="0x123...",  # Mock signer address
            timestamp=int(datetime.now().timestamp())
        )

    # Try blockchain read
    try:
        market_id_bytes = to_bytes32(market_id)
        reading = read_latest(market_id_bytes)  # expected tuple
        return OracleReading(
            market_id=market_id,
            cred_score=reading[0],
            risk_index=reading[1],
            meta_uri=reading[2],
            signer=reading[3],
            timestamp=reading[4]
        )
    except Exception:
        # Default neutral values if not found - avoid misleading perfect scores
        return OracleReading(
            market_id=market_id,
            cred_score=50,  # Neutral credibility
            risk_index=50,  # Neutral risk
            meta_uri="",
            signer="0x000...",
            timestamp=int(datetime.now().timestamp())
        )

def get_analysis_service(market_id: str) -> Optional[AnalysisResult]:
    return analysis_cache.get(market_id)

def analyze_custom_question_service(question: str) -> CustomQueryResponse:
    try:
        import hashlib
        from .scoring.openai_nlp import analyze_question

        # Validate question input
        if not question or len(question.strip()) < 5:
            raise ValueError("Question must be at least 5 characters long")

        # Create hash for caching (normalize question)
        question_normalized = question.strip().lower()
        question_hash = hashlib.md5(question_normalized.encode()).hexdigest()
        
        # Check cache first to reduce OpenAI API calls
        cached_result = get_cached_ai_analysis(question_hash)
        if cached_result:
            return CustomQueryResponse(**cached_result)

        print(f"🤖 Analyzing NEW custom question (not cached): {question}")
        analysis_result: Dict = analyze_question(question)

        analysis_text = analysis_result.get('analysis', 'Analysis completed')
        credibility = analysis_result.get('credibility_score', 50)
        risk_idx = analysis_result.get('risk_index', 50)

        timestamp_iso = datetime.now().isoformat()

        response_data = {
            "answer": analysis_text,
            "confidence": credibility / 100.0,
            "sources": ["CoinGecko API", "OpenAI Analysis", "TruthLens Oracle"],
            "metadata": {
                "question": question,
                "credibility_score": credibility,
                "risk_index": risk_idx,
                "timestamp": timestamp_iso
            }
        }

        # Cache the result to reduce future OpenAI API calls
        cache_ai_analysis(question_hash, response_data)

        response = CustomQueryResponse(**response_data)

        # Optional: submit to blockchain (only for new analysis, not cached)
        try:
            metadata = {
                "question": question,
                "analysis": analysis_text,
                "credibility_score": credibility,
                "risk_index": risk_idx,
                "timestamp": timestamp_iso
            }

            ipfs_uri = put_json(metadata)
            market_id_bytes = to_bytes32(f"custom_{hash(question) % 10000}")
            tx_hash = submit_attestation(market_id_bytes, credibility, risk_idx, ipfs_uri)
            response.metadata["tx_hash"] = tx_hash
        except Exception as blockchain_error:
            print(f"⚠️  Blockchain submission failed (non-critical): {blockchain_error}")

        return response

    except Exception as e:
        print(f"❌ Custom analysis error: {e}")
        # Let the router convert this into an HTTPException
        raise

def get_status_service() -> OracleStatus:
    return oracle_status

# ======================
# Settings Management
# ======================

# In-memory settings storage (use database in production)
user_settings_store = {
    "profile": {
        "name": "TruthLens User",
        "email": "user@truthlens.io",
        "avatar": "",
        "language": "en",
        "timezone": "UTC"
    },
    "notifications": {
        "email": True,
        "browser": True,
        "analysis": True,
        "alerts": True,
        "frequency": "realtime"
    },
    "privacy": {
        "dataSharing": False,
        "analytics": True,
        "marketing": False,
        "publicProfile": False
    },
    "api": {
        "key": "tl_prod_abc123def456ghi789",
        "rateLimit": 1000,
        "accessLevel": "premium"
    },
    "display": {
        "theme": "light",
        "currency": "USD",
        "timeFormat": "12h"
    }
}

def get_settings_service():
    """Get user settings"""
    from .models import UserSettings
    return UserSettings(**user_settings_store)

def update_settings_service(settings: dict):
    """Update user settings"""
    global user_settings_store
    # Deep merge the settings
    for category, values in settings.items():
        if category in user_settings_store:
            user_settings_store[category].update(values)
        else:
            user_settings_store[category] = values
    return get_settings_service()

def generate_api_key_service():
    """Generate a new API key"""
    import secrets
    new_key = f"tl_prod_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
    user_settings_store["api"]["key"] = new_key
    return {"api_key": new_key}

# ======================
# Analytics & Insights
# ======================

def get_analytics_service():
    """Get system analytics data"""
    from .models import AnalyticsData
    
    # Calculate metrics from cached data
    total_markets = len(analysis_cache)
    successful_analyses = len([a for a in analysis_cache.values() if a.confidence > 0.5])
    success_rate = (successful_analyses / total_markets) if total_markets > 0 else 0
    avg_confidence = sum(a.confidence for a in analysis_cache.values()) / total_markets if total_markets > 0 else 0
    
    # Generate mock time series data
    import time
    now = int(time.time())
    time_series = []
    for i in range(24):  # Last 24 hours
        timestamp = now - (i * 3600)
        time_series.append({
            "timestamp": timestamp,
            "markets_analyzed": max(0, total_markets - i),
            "confidence": max(0.3, avg_confidence - (i * 0.01)),
            "success_rate": max(0.5, success_rate - (i * 0.005))
        })
    
    return AnalyticsData(
        markets_analyzed=total_markets,
        success_rate=success_rate,
        avg_confidence=avg_confidence,
        total_attestations=oracle_status.total_attestations,
        performance_metrics={
            "response_time": 245,
            "uptime": 99.9,
            "error_rate": 0.1,
            "throughput": 150
        },
        time_series=time_series[::-1]  # Reverse for chronological order
    )

def get_history_service():
    """Get analysis history data"""
    from .models import HistoryData
    
    # Convert cached analyses to history format
    analyses = []
    for market_id, analysis in analysis_cache.items():
        analyses.append({
            "id": market_id,
            "market_name": market_id.replace('_', ' ').title(),
            "credibility_score": analysis.credibility_score,
            "risk_index": analysis.risk_index,
            "confidence": analysis.confidence,
            "timestamp": analysis.metadata.get("timestamp", int(time.time())),
            "status": "completed",
            "tx_hash": analysis.tx_hash
        })
    
    return HistoryData(
        analyses=analyses,
        total_count=len(analyses)
    )

def get_blockchain_service():
    """Get blockchain transaction data"""
    from .models import BlockchainData
    
    # Get transactions from cached analyses
    transactions = []
    for analysis in analysis_cache.values():
        if analysis.tx_hash:
            transactions.append({
                "hash": analysis.tx_hash,
                "market_id": analysis.market_id,
                "credibility": analysis.credibility_score,
                "risk": analysis.risk_index,
                "timestamp": analysis.metadata.get("timestamp", int(time.time())),
                "status": "confirmed",
                "gas_used": 45000
            })
    
    return BlockchainData(
        transactions=transactions,
        total_attestations=len(transactions),
        contract_address="0x742d35Cc6634C0532925a3b8D697D9D3C8f8E8E8",
        network="BSC Testnet"
    )

def get_metrics_service():
    """Get detailed system metrics"""
    from .models import SystemMetrics
    import time
    
    return SystemMetrics(
        uptime=int(time.time() - 1640995200),  # Since project start
        request_count=sum(len(analysis_cache) * 10, 1500),  # Mock data
        error_rate=0.02,
        response_times={
            "p50": 120,
            "p90": 250,
            "p95": 380,
            "p99": 500
        },
        service_status={
            "api": "healthy",
            "database": "healthy", 
            "blockchain": "healthy" if oracle_status.blockchain_connected else "degraded",
            "ai_service": "healthy"
        }
    )

# ======================
# Long-running tasks
# ======================

async def perform_analysis():
    """Perform credibility and risk analysis for all markets and update cache/status."""
    global oracle_status, analysis_cache

    print("🔄 Starting TruthLens analysis...")
    try:
        markets = get_cached_markets()
        comments = get_cached_comments()

        results: List[AnalysisResult] = []

        for market in markets:
            market_id = market.get('marketId', 'unknown')
            print(f"🔍 Analyzing market: {market_id}")

            # Filter relevant comments
            market_comments = [c for c in comments if c.get('marketId') == market_id]

            # Calculate scores
            cred, per_link, cred_reasons = credibility_score(market_comments)
            link_var = (max(per_link.values()) - min(per_link.values())) if len(per_link) > 1 else 0
            risk, risk_reasons = risk_score(market, link_var, market_comments)

            # Prepare metadata
            metadata = {
                'marketId': market_id,
                'credScore': cred,
                'riskIndex': risk,
                'perLink': per_link,
                'credReasons': cred_reasons,
                'riskReasons': risk_reasons,
                'analysis_time': datetime.now().isoformat()
            }

            # Store to IPFS
            ipfs_uri = put_json(metadata)

            # Create result
            result = AnalysisResult(
                market_id=market_id,
                credibility_score=int(cred),
                risk_index=int(risk),
                confidence=0.85,  # Placeholder; wire your own logic if available
                links_analyzed=len(per_link),
                metadata=metadata,
                ipfs_hash=ipfs_uri
            )

            # Submit to blockchain (best-effort)
            try:
                market_id_bytes = to_bytes32(market_id)
                tx_hash = submit_attestation(market_id_bytes, int(cred), int(risk), ipfs_uri)
                result.tx_hash = tx_hash
                print(f"✅ Blockchain submission: {tx_hash}")
            except Exception as e:
                print(f"❌ Blockchain submission failed: {e}")

            # Cache result
            analysis_cache[market_id] = result
            results.append(result)

        # Update status
        oracle_status.total_markets = len(results)
        oracle_status.last_update = int(datetime.now().timestamp())
        oracle_status.total_attestations = len([r for r in results if r.tx_hash])

        print(f"🎉 Analysis complete! Processed {len(results)} markets")

    except Exception as e:
        print(f"❌ Analysis error: {e}")

# ======================
# Cache Management Functions
# ======================

def clear_all_caches():
    """Clear all caches to force fresh data (admin function)"""
    with cache_lock:
        global markets_cache, comments_cache, ai_analysis_cache, analysis_cache
        markets_cache.clear()
        comments_cache.clear()
        ai_analysis_cache.clear()
        analysis_cache.clear()
        print("🧹 All caches cleared - next requests will fetch fresh data")

def get_cache_stats():
    """Get cache statistics for monitoring"""
    with cache_lock:
        return {
            "markets_cache": {
                "size": len(markets_cache),
                "ttl_minutes": MARKETS_CACHE_TTL / 60,
                "has_data": 'markets_data' in markets_cache
            },
            "comments_cache": {
                "size": len(comments_cache), 
                "ttl_minutes": COMMENTS_CACHE_TTL / 60,
                "has_data": 'comments_data' in comments_cache
            },
            "ai_analysis_cache": {
                "size": len(ai_analysis_cache),
                "ttl_minutes": ANALYSIS_CACHE_TTL / 60
            },
            "analysis_cache": {
                "size": len(analysis_cache)
            }
        }

async def periodic_analysis():
    """Run analysis periodically every 60 minutes (reduced frequency)."""
    while True:
        await asyncio.sleep(3600)  # Increased from 30 to 60 minutes
        print("⏰ Running periodic analysis (reduced frequency)...")
        await perform_analysis()