import numpy as np
from .openai_nlp import analyze_market_sentiment

def zscores(arr):
    arr = np.array(arr, dtype=float)
    if arr.size == 0:
        return arr
    m, s = arr.mean(), arr.std()
    return (arr - m) / s if s else np.zeros_like(arr)

def risk_score(market: dict, link_quality_variance: int = 20, comments: list = None):
    print("  🤖 Using OpenAI for advanced risk analysis...")
    
    # On-chain anomaly detection (unchanged)
    pz = zscores(market.get('price24h', []))
    vz = zscores(market.get('volume24h', []))
    last_p = abs(pz[-1]) if pz.size else 0
    last_v = abs(vz[-1]) if vz.size else 0
    onchain_anomaly = min(100, round(60 + 10*max(last_p, last_v)))
    
    # Order flow imbalance (placeholder - could be enhanced with real data)
    order_flow_imbalance = 40
    
    # Advanced sentiment analysis with OpenAI
    if comments:
        market_question = market.get('question', 'Market prediction')
        sentiment_analysis = analyze_market_sentiment(comments, market_question)
        
        # Convert sentiment analysis to risk components
        manipulation_risk_component = sentiment_analysis['manipulation_risk'] * 100
        
        # High absolute sentiment can indicate manipulation
        sentiment_extremity = abs(sentiment_analysis['sentiment_score']) * 50
        
        # Coordinated activity is a strong risk signal
        coordination_penalty = 30 if sentiment_analysis['coordinated_activity'] else 0
        
        # Combine sentiment factors
        sentiment_volatility = min(100, round(
            0.5 * manipulation_risk_component + 
            0.3 * sentiment_extremity + 
            0.2 * coordination_penalty
        ))
        
        print(f"    📊 Sentiment score: {sentiment_analysis['sentiment_score']:.2f}")
        print(f"    🎯 Manipulation risk: {sentiment_analysis['manipulation_risk']:.2f}")
        print(f"    🤝 Coordinated activity: {sentiment_analysis['coordinated_activity']}")
        print(f"    📈 Sentiment volatility component: {sentiment_volatility}")
        
        if sentiment_analysis['patterns']:
            print(f"    🔍 Detected patterns: {', '.join(sentiment_analysis['patterns'][:2])}")
            
    else:
        sentiment_volatility = 30  # fallback
        sentiment_analysis = None
    
    # Illiquidity penalty
    illiquidity_penalty = 10 if (market.get('volume24h', [0])[-1] < 800) else 0
    
    # Calculate final risk score
    risk = round(
        0.30 * onchain_anomaly +           # Reduced from 35% to make room for sentiment
        0.20 * order_flow_imbalance +      # Reduced from 25%
        0.30 * sentiment_volatility +      # Increased from 20% - now AI-powered
        0.10 * link_quality_variance +
        0.10 * illiquidity_penalty
    )
    risk = min(100, max(0, risk))
    
    # Enhanced reasoning with AI insights
    reasons = [
        f"On-chain anomaly detection: {onchain_anomaly}/100",
        f"Order flow analysis: {order_flow_imbalance}/100 (placeholder)",
        f"AI sentiment analysis: {sentiment_volatility}/100",
        f"Source quality variance: {link_quality_variance}",
        f"Illiquidity penalty: {illiquidity_penalty}"
    ]
    
    # Add AI-specific insights
    if sentiment_analysis:
        if sentiment_analysis['coordinated_activity']:
            reasons.append("⚠️ Coordinated manipulation activity detected")
        
        if sentiment_analysis['manipulation_risk'] > 0.7:
            reasons.append("🚨 High manipulation risk in sentiment patterns")
            
        if abs(sentiment_analysis['sentiment_score']) > 0.8:
            reasons.append("📊 Extreme sentiment detected (potential manipulation)")
    
    print(f"  🎯 Final risk score: {risk}/100")
    
    return risk, reasons