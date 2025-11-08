from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List
import time

from services import (
    MarketData,
    OracleReading,
    AnalysisResult,
    CustomQueryRequest,
    CustomQueryResponse,
    OracleStatus,
    UserSettings,
    AnalyticsData,
    HistoryData,
    BlockchainData,
    SystemMetrics,
    get_markets_service,
    get_oracle_reading_service,
    get_analysis_service,
    analyze_custom_question_service,
    get_status_service,
    get_settings_service,
    update_settings_service,
    generate_api_key_service,
    get_analytics_service,
    get_history_service,
    get_blockchain_service,
    get_metrics_service,
    perform_analysis,
)

# Import enhanced AI services
try:
    from services.ai.performance_monitor import performance_monitor
    from services.ai.batch_processor import queue_analysis, process_urgent, flush_queue, get_processing_status
    from services.ai.cache_manager import ai_cache
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    print("Enhanced AI services not available")

api_router = APIRouter()

@api_router.get("/")
async def root():
    """API Root endpoint"""
    return {
        "name": "TruthLens Oracle API",
        "version": "1.0.0",
        "description": "AI-powered credibility and manipulation risk analysis",
        "endpoints": [
            "/markets", "/oracle/{marketId}", "/analyze", "/status"
        ]
    }

@api_router.get("/markets", response_model=List[MarketData])
async def get_markets():
    """Get available prediction markets"""
    try:
        return get_markets_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching markets: {str(e)}")

@api_router.get("/oracle/{market_id}", response_model=OracleReading)
async def get_oracle_reading(market_id: str):
    """Get latest oracle reading for a specific market"""
    try:
        return get_oracle_reading_service(market_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Oracle reading not found: {str(e)}")

@api_router.get("/analyze/{market_id}", response_model=AnalysisResult)
async def get_analysis(market_id: str):
    """Get cached analysis result for a market"""
    result = get_analysis_service(market_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found for this market")
    return result

@api_router.post("/analyze", response_model=CustomQueryResponse)
async def analyze_custom_question(query: CustomQueryRequest):
    """Analyze a custom market question with AI"""
    try:
        return analyze_custom_question_service(query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.post("/trigger-analysis")
async def trigger_analysis(background_tasks: BackgroundTasks):
    """Trigger analysis for all markets"""
    background_tasks.add_task(perform_analysis)
    return {"message": "Analysis started", "status": "processing"}

@api_router.get("/status", response_model=OracleStatus)
async def get_status():
    """Get oracle system status"""
    return get_status_service()

@api_router.get("/health")
async def get_health():
    """Health check endpoint for system monitoring - lightweight check without API calls"""
    try:
        # Get status without triggering expensive API calls
        status = get_status_service()
        
        # Check if we have any cached markets data (don't fetch new)
        from services.main import markets_cache
        has_markets = 'markets_data' in markets_cache and len(markets_cache.get('markets_data', [])) > 0
        
        return {
            "status": "healthy", 
            "timestamp": int(time.time() * 1000),
            "services": {
                "api": "online",
                "markets": "online" if has_markets else "degraded",
                "oracle": "online" if status.blockchain_connected else "degraded",
                "analysis": "online"  # Analysis service is always online if we reach this point
            },
            "metrics": {
                "total_markets": status.total_markets,
                "active_analyses": status.active_analyses,
                "blockchain_connected": status.blockchain_connected,
                "last_update": status.last_update
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": int(time.time() * 1000),
            "error": str(e),
            "services": {
                "api": "online",
                "markets": "offline",
                "oracle": "offline", 
                "analysis": "offline"
            }
        }

# ======================
# Settings Endpoints
# ======================

@api_router.get("/settings", response_model=UserSettings)
async def get_settings():
    """Get user settings"""
    try:
        return get_settings_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@api_router.post("/settings")
async def update_settings(settings: dict):
    """Update user settings"""
    try:
        # Validate settings structure
        allowed_keys = {"profile", "notifications", "privacy", "api", "display"}
        if not isinstance(settings, dict) or not any(key in allowed_keys for key in settings.keys()):
            raise HTTPException(status_code=400, detail="Invalid settings structure")
        return update_settings_service(settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@api_router.post("/settings/api-key")
async def generate_api_key():
    """Generate a new API key"""
    try:
        return generate_api_key_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate API key: {str(e)}")

# ======================
# Analytics & Insights Endpoints
# ======================

@api_router.get("/analytics", response_model=AnalyticsData)
async def get_analytics():
    """Get system analytics data"""
    try:
        return get_analytics_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@api_router.get("/analytics/history", response_model=HistoryData)
async def get_history():
    """Get analysis history data"""
    try:
        return get_history_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@api_router.get("/analytics/blockchain", response_model=BlockchainData)
async def get_blockchain():
    """Get blockchain transaction data"""
    try:
        return get_blockchain_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blockchain data: {str(e)}")

@api_router.get("/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get detailed system metrics"""
    try:
        return get_metrics_service()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

# ======================
# Enhanced Market Endpoints
# ======================

@api_router.get("/markets/{market_id}/history")
async def get_market_history(market_id: str):
    """Get historical data for a specific market"""
    try:
        # Mock historical data - in production, fetch from database
        import time
        now = int(time.time())
        history = {
            "market_id": market_id,
            "price_history": [
                {"timestamp": now - i * 3600, "price": 0.65 + (i * 0.01), "volume": 1000 - (i * 10)}
                for i in range(24, 0, -1)
            ],
            "analysis_history": [
                {
                    "timestamp": now - i * 3600,
                    "credibility": max(50, 85 - (i * 2)),
                    "risk": min(50, 15 + i),
                    "confidence": max(0.5, 0.9 - (i * 0.01))
                }
                for i in range(12, 0, -1)
            ]
        }
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get market history: {str(e)}")

# ======================
# Enhanced AI Endpoints
# ======================

@api_router.get("/ai/performance")
async def get_ai_performance_metrics():
    """Get AI performance metrics"""
    if not ENHANCED_AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced AI features not available")
    
    try:
        metrics = performance_monitor.get_metrics()
        suggestions = performance_monitor.get_optimization_suggestions()
        
        return {
            "success": True,
            "metrics": metrics,
            "optimization_suggestions": suggestions,
            "enhanced_features_enabled": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance monitoring error: {str(e)}")

@api_router.get("/ai/status")
async def get_ai_status():
    """Get AI service status and queue information"""
    if not ENHANCED_AI_AVAILABLE:
        return {
            "success": True,
            "enhanced_features_enabled": False,
            "status": "basic_mode",
            "message": "Enhanced AI features not available, using basic mode"
        }
    
    try:
        queue_status = get_processing_status()
        performance_metrics = performance_monitor.get_metrics()
        
        return {
            "success": True,
            "enhanced_features_enabled": True,
            "status": "enhanced_mode",
            "queue_status": queue_status,
            "performance": performance_metrics,
            "message": "Enhanced AI features active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI status error: {str(e)}")

@api_router.get("/ai/cache/stats")
async def get_cache_stats():
    """Get AI cache statistics"""
    if not ENHANCED_AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced AI features not available")
    
    try:
        stats = ai_cache.get_stats()
        return {
            "success": True,
            "cache_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache stats error: {str(e)}")

@api_router.post("/ai/cache/clear")
async def clear_ai_cache():
    """Clear AI cache"""
    if not ENHANCED_AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced AI features not available")
    
    try:
        ai_cache.clear()
        return {
            "success": True,
            "message": "AI cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")

@api_router.post("/ai/queue/flush")
async def flush_ai_queue():
    """Manually flush the AI processing queue"""
    if not ENHANCED_AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced AI features not available")
    
    try:
        results = flush_queue()
        return {
            "success": True,
            "message": f"Queue flushed, processed {len(results)} items",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Queue flush error: {str(e)}")

@api_router.get("/ai/config")
async def get_ai_config():
    """Get current AI configuration"""
    if not ENHANCED_AI_AVAILABLE:
        return {
            "enhanced_features_enabled": False,
            "config": {
                "mode": "basic",
                "features": ["openai_basic"]
            }
        }
    
    try:
        # Read config from ai_config.ini
        import configparser
        import os
        
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'ai_config.ini')
        config = configparser.ConfigParser()
        
        if os.path.exists(config_path):
            config.read(config_path)
            
            return {
                "enhanced_features_enabled": True,
                "config": {
                    "cache": dict(config['cache']) if 'cache' in config else {},
                    "performance": dict(config['performance']) if 'performance' in config else {},
                    "optimization": dict(config['optimization']) if 'optimization' in config else {}
                }
            }
        else:
            return {
                "enhanced_features_enabled": True,
                "config": {
                    "mode": "enhanced",
                    "message": "Config file not found, using defaults"
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Config error: {str(e)}")

@api_router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics for monitoring API usage reduction"""
    try:
        from services import get_cache_stats
        
        stats = get_cache_stats()
        return {
            "success": True,
            "cache_stats": stats,
            "message": "Extended cache times reduce API calls significantly"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache stats error: {str(e)}")

@api_router.post("/admin/clear-cache")
async def clear_cache():
    """Clear all caches to force fresh data (admin only)"""
    try:
        from services import clear_all_caches
        
        clear_all_caches()
        
        return {
            "success": True,
            "message": "All caches cleared - next API calls will fetch fresh data",
            "timestamp": int(time.time() * 1000),
            "note": "This will temporarily increase API usage until caches rebuild"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")
