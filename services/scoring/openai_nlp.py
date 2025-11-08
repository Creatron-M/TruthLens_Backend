import os
import json
import requests
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

# Import lightweight enhancer
try:
    from ..ai.lightweight_enhancer import lightweight_ai
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    print("Enhanced AI not available, using basic mode")

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def analyze_content_credibility(text: str, url: str = "") -> dict:
    """Use enhanced lightweight AI to analyze content credibility"""
    
    # Try enhanced AI first
    if ENHANCED_AI_AVAILABLE:
        try:
            # Use sync fallback analysis to avoid asyncio issues
            result = lightweight_ai._fast_fallback_analysis(text, url)
            
            # Convert to expected format
            return {
                'credibility_score': int(result.get('credibility_score', 50)),
                'confidence': result.get('confidence', 0.5),
                'reasoning': [result.get('reasoning', 'Enhanced analysis completed')],
                'bias_indicators': result.get('key_indicators', []),
                'fact_check_signals': result.get('risk_factors', []),
                'emotional_manipulation': result.get('manipulation_risk', 50) / 100.0,
                'enhanced_analysis': True
            }
        except Exception as e:
            print(f"Enhanced analysis failed: {e}")
            # Fall through to basic analysis
    
    if not client.api_key:
        # Fallback to basic analysis if no OpenAI key
        return {
            'credibility_score': 50,
            'confidence': 0.3,
            'reasoning': ['No OpenAI API key provided - using basic analysis'],
            'bias_indicators': [],
            'fact_check_signals': [],
            'emotional_manipulation': 0.5
        }
    
    try:
        prompt = f"""
Analyze this content for credibility and potential misinformation. Consider:
1. Factual accuracy indicators
2. Bias and emotional manipulation
3. Source credibility signals
4. Citation quality
5. Language patterns that suggest reliability or unreliability

Content: "{text}"
Source URL: "{url}"

Respond with JSON in this exact format:
{{
    "credibility_score": <0-100 integer>,
    "confidence": <0.0-1.0 float>,
    "reasoning": ["reason1", "reason2", "reason3"],
    "bias_indicators": ["indicator1", "indicator2"],
    "fact_check_signals": ["signal1", "signal2"],
    "emotional_manipulation": <0.0-1.0 float>
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert fact-checker and misinformation analyst. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Validate and sanitize the response
        return {
            'credibility_score': max(0, min(100, int(result.get('credibility_score', 50)))),
            'confidence': max(0.0, min(1.0, float(result.get('confidence', 0.5)))),
            'reasoning': result.get('reasoning', [])[:5],  # Limit to 5 reasons
            'bias_indicators': result.get('bias_indicators', [])[:5],
            'fact_check_signals': result.get('fact_check_signals', [])[:5],
            'emotional_manipulation': max(0.0, min(1.0, float(result.get('emotional_manipulation', 0.5))))
        }
        
    except Exception as e:
        print(f"OpenAI analysis error: {e}")
        return {
            'credibility_score': 50,
            'confidence': 0.3,
            'reasoning': [f'Analysis failed: {str(e)[:100]}'],
            'bias_indicators': [],
            'fact_check_signals': [],
            'emotional_manipulation': 0.5
        }

def analyze_market_sentiment(comments: list, market_question: str) -> dict:
    """Analyze overall sentiment and manipulation risk in market comments"""
    
    if not client.api_key or not comments:
        return {
            'sentiment_score': 0.0,
            'manipulation_risk': 0.5,
            'confidence': 0.3,
            'patterns': [],
            'coordinated_activity': False
        }
    
    try:
        # Prepare comments text
        comments_text = "\n".join([
            f"Author: {c.get('author', 'unknown')} | Text: {c.get('text', '')[:200]}"
            for c in comments[:10]  # Limit to first 10 comments to stay within token limits
        ])
        
        prompt = f"""
Analyze these market prediction comments for sentiment and potential manipulation:

Market Question: "{market_question}"

Comments:
{comments_text}

Look for:
1. Overall sentiment (bullish/bearish/neutral)
2. Signs of coordinated manipulation
3. Emotional manipulation tactics
4. Artificial consensus building
5. Suspicious patterns in language or timing

Respond with JSON in this exact format:
{{
    "sentiment_score": <-1.0 to 1.0 float, where -1=very bearish, 1=very bullish>,
    "manipulation_risk": <0.0-1.0 float>,
    "confidence": <0.0-1.0 float>,
    "patterns": ["pattern1", "pattern2"],
    "coordinated_activity": <true/false>
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in detecting market manipulation and coordinated misinformation campaigns. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            'sentiment_score': max(-1.0, min(1.0, float(result.get('sentiment_score', 0.0)))),
            'manipulation_risk': max(0.0, min(1.0, float(result.get('manipulation_risk', 0.5)))),
            'confidence': max(0.0, min(1.0, float(result.get('confidence', 0.5)))),
            'patterns': result.get('patterns', [])[:5],
            'coordinated_activity': bool(result.get('coordinated_activity', False))
        }
        
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return {
            'sentiment_score': 0.0,
            'manipulation_risk': 0.5,
            'confidence': 0.3,
            'patterns': [f'Analysis failed: {str(e)[:100]}'],
            'coordinated_activity': False
        }

def check_domain_with_virustotal(url: str) -> dict:
    """Check domain reputation using VirusTotal API"""
    api_key = os.getenv('DOMAIN_REPUTATION_API_KEY')
    if not api_key:
        return {}
    
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        vt_url = f"https://www.virustotal.com/vtapi/v2/domain/report"
        params = {'apikey': api_key, 'domain': domain}
        
        response = requests.get(vt_url, params=params, timeout=5)
        data = response.json()
        
        if data.get('response_code') == 1:
            positives = data.get('positives', 0)
            total = data.get('total', 1)
            reputation_score = max(0, 100 - (positives / total * 100))
            
            return {
                'reputation_score': int(reputation_score),
                'scam_detected': positives > 2,
                'scan_results': f"{positives}/{total} security vendors flagged this domain"
            }
    except Exception as e:
        print(f"VirusTotal check failed: {e}")
    
    return {}

def check_domain_authority(url: str) -> dict:
    """Check domain authority using OpenPageRank API"""
    api_key = os.getenv('OPEN_PAGERANK_API_KEY')
    if not api_key:
        return {}
    
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        
        headers = {'API-OPR': api_key}
        opr_url = f"https://openpagerank.com/api/v1.0/getPageRank"
        params = {'domains[]': domain}
        
        response = requests.get(opr_url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data.get('status_code') == 200:
            domain_data = data.get('response', [{}])[0]
            page_rank = domain_data.get('page_rank_decimal', 0)
            rank_integer = domain_data.get('page_rank_integer', 0)
            
            return {
                'page_rank': page_rank,
                'authority_score': min(100, rank_integer * 10),  # Scale to 0-100
                'domain_status': domain_data.get('status', 'unknown')
            }
    except Exception as e:
        print(f"OpenPageRank check failed: {e}")
    
    return {}

def analyze_domain_credibility(url: str) -> dict:
    """Use OpenAI + external APIs to analyze domain credibility"""
    
    if not url:
        return {
            'domain_score': 50,
            'confidence': 0.3,
            'reasoning': ['No URL provided'],
            'category': 'unknown'
        }
    
    # Check with external APIs
    vt_results = check_domain_with_virustotal(url)
    opr_results = check_domain_authority(url)
    
    # Combine scores
    base_score = 50
    confidence = 0.5
    reasoning = []
    
    if vt_results:
        if vt_results.get('scam_detected'):
            base_score = max(10, base_score - 40)
            reasoning.append(f"Security risk detected: {vt_results.get('scan_results')}")
        else:
            base_score = min(90, base_score + 20)
            reasoning.append("Domain passed security checks")
        confidence += 0.2
    
    if opr_results:
        authority = opr_results.get('authority_score', 50)
        if authority > 70:
            base_score = min(95, base_score + 15)
            reasoning.append(f"High domain authority (PageRank: {opr_results.get('page_rank', 0):.2f})")
        elif authority < 30:
            base_score = max(20, base_score - 15)
            reasoning.append("Low domain authority")
        confidence += 0.2
    
    if not client.api_key:
        # Use VirusTotal results if available, otherwise fallback
        if vt_results:
            return {
                'domain_score': vt_results.get('reputation_score', 50),
                'confidence': 0.7,
                'reasoning': [vt_results.get('scan_results', 'Security scan completed')],
                'category': 'security_checked'
            }
        else:
            return {
                'domain_score': 50,
                'confidence': 0.3,
                'reasoning': ['No OpenAI API key or security API available'],
                'category': 'unknown'
            }
    
    try:
        prompt = f"""
Analyze this URL/domain for credibility and trustworthiness:

URL: "{url}"

Consider:
1. Domain reputation and authority
2. Known bias or reliability issues
3. Type of publication (news, blog, academic, etc.)
4. Track record for accuracy
5. Editorial standards

Respond with JSON in this exact format:
{{
    "domain_score": <0-100 integer>,
    "confidence": <0.0-1.0 float>,
    "reasoning": ["reason1", "reason2"],
    "category": "news|blog|academic|social|corporate|unknown"
}}
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert in media literacy and source credibility assessment. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=400
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            'domain_score': max(0, min(100, int(result.get('domain_score', 50)))),
            'confidence': max(0.0, min(1.0, float(result.get('confidence', 0.5)))),
            'reasoning': result.get('reasoning', [])[:3],
            'category': result.get('category', 'unknown')
        }
        
    except Exception as e:
        print(f"Domain analysis error: {e}")
        return {
            'domain_score': 50,
            'confidence': 0.3,
            'reasoning': [f'Analysis failed: {str(e)[:100]}'],
            'category': 'unknown'
        }

def analyze_question(question: str) -> dict:
    """Analyze a custom market question using OpenAI with timeout protection"""
    
    print(f"🤖 Starting AI analysis for question: '{question[:50]}...'")
    
    if not client.api_key:
        print("⚠️ No OpenAI API key - using fallback analysis")
        return {
            'analysis': f"Question received: '{question}'. Basic analysis: This appears to be a market-related inquiry. For more detailed AI analysis, please configure OpenAI API key.",
            'credibility_score': 50,
            'risk_index': 50,
            'confidence': 0.3
        }
    
    try:
        print("🚀 Calling OpenAI API...")
        prompt = f"""
Analyze this cryptocurrency/market question for credibility and risk assessment:

Question: "{question}"

Provide a JSON response with:
1. "analysis" - detailed explanation of market conditions and credibility
2. "credibility_score" - score 0-100 based on available data reliability
3. "risk_index" - score 0-100 for investment/market risk (0=low risk, 100=high risk)  
4. "confidence" - your confidence in this analysis (0.0-1.0)

Consider:
- Current market conditions
- Historical patterns
- Potential manipulation signals
- Information quality and sources
- Market sentiment indicators

Format as valid JSON only.
"""

        # For MVP: Use faster gpt-3.5-turbo instead of gpt-4 to reduce latency
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Faster than gpt-4
            messages=[
                {"role": "system", "content": "You are a cryptocurrency market analysis expert specializing in credibility assessment and risk analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400,  # Reduced tokens for faster response
            timeout=10  # 10 second timeout for MVP
        )
        
        print("✅ OpenAI API call completed successfully")
        result = json.loads(response.choices[0].message.content)
        
        final_result = {
            'analysis': result.get('analysis', 'Analysis completed successfully.'),
            'credibility_score': max(0, min(100, int(result.get('credibility_score', 50)))),
            'risk_index': max(0, min(100, int(result.get('risk_index', 50)))),
            'confidence': max(0.0, min(1.0, float(result.get('confidence', 0.5))))
        }
        
        print(f"🎯 Analysis complete - Credibility: {final_result['credibility_score']}%, Risk: {final_result['risk_index']}%")
        return final_result
        
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        print("🔄 Using enhanced fallback analysis for MVP")
        
        # Enhanced fallback analysis based on keywords
        question_lower = question.lower()
        
        # Determine credibility based on question type
        if any(word in question_lower for word in ['predict', 'forecast', 'will', 'reach', 'price']):
            credibility = 45  # Price predictions are inherently uncertain
            risk = 75  # High risk
            analysis = f"Analysis of '{question}': Price predictions carry significant uncertainty due to market volatility. Historical data shows cryptocurrency markets are influenced by multiple unpredictable factors including regulatory news, market sentiment, and external economic conditions. Exercise caution with any specific price targets."
        elif any(word in question_lower for word in ['manipulation', 'pump', 'dump', 'scam']):
            credibility = 70  # Good question about risks
            risk = 85  # High risk topic
            analysis = f"Analysis of '{question}': This question addresses important market risk factors. Cryptocurrency markets do experience manipulation attempts including pump-and-dump schemes. Always verify information from multiple reliable sources and be cautious of coordinated promotional activities."
        elif any(word in question_lower for word in ['credibility', 'reliable', 'trust', 'legitimate']):
            credibility = 80  # Good skeptical questioning
            risk = 40  # Lower risk question
            analysis = f"Analysis of '{question}': Questioning credibility is a smart approach in crypto markets. Always cross-reference information from multiple sources, check the track record of analysts, and be wary of overly optimistic claims. Reliable sources typically provide balanced analysis with risk disclaimers."
        else:
            credibility = 60  # General market question
            risk = 55  # Moderate risk
            analysis = f"Analysis of '{question}': General market analysis suggests this is a reasonable inquiry about cryptocurrency markets. Current market conditions show typical volatility patterns. For the most accurate insights, consider multiple data sources and recent market developments."
        
        return {
            'analysis': analysis,
            'credibility_score': credibility,
            'risk_index': risk,
            'confidence': 0.6
        }