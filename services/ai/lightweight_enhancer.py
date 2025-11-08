import os
import json
import time
import hashlib
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

@dataclass
class AnalysisCache:
    """Lightweight caching for AI results"""
    content_hash: str
    result: Dict
    timestamp: float
    ttl: int = 3600  # 1 hour cache

class LightweightAIEnhancer:
    """Enhanced AI with optimizations for low-resource environments"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.cache = {}
        self.domain_reputation_cache = {}
        self.pattern_cache = {}
        
        # Pre-loaded patterns for fast detection
        self.load_manipulation_patterns()
        self.load_domain_patterns()
    
    def _get_cache_key(self, content: str, analysis_type: str) -> str:
        """Generate cache key for content"""
        return hashlib.md5(f"{content}:{analysis_type}".encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: AnalysisCache) -> bool:
        """Check if cached result is still valid"""
        return time.time() - cache_entry.timestamp < cache_entry.ttl
    
    def _cache_result(self, key: str, result: Dict, ttl: int = 3600):
        """Cache analysis result"""
        self.cache[key] = AnalysisCache(
            content_hash=key,
            result=result,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def load_manipulation_patterns(self):
        """Load pre-defined manipulation patterns for fast detection"""
        self.manipulation_patterns = {
            'pump_signals': [
                'to the moon', 'diamond hands', 'hodl', 'buy the dip',
                'rocket', '🚀', 'moon', '💎', 'ape in', 'yolo'
            ],
            'dump_signals': [
                'sell everything', 'crash incoming', 'bubble burst',
                'ponzi', 'scam', 'rug pull', 'exit liquidity'
            ],
            'urgency_words': [
                'now', 'immediately', 'last chance', 'limited time',
                'don\'t miss', 'act fast', 'urgent', 'breaking'
            ],
            'emotional_triggers': [
                'fear', 'greed', 'fomo', 'panic', 'euphoria',
                'devastating', 'amazing', 'incredible', 'shocking'
            ]
        }
    
    def load_domain_patterns(self):
        """Load domain reputation patterns"""
        self.domain_patterns = {
            'high_reputation': [
                'reuters.com', 'bloomberg.com', 'wsj.com', 'ft.com',
                'coindesk.com', 'cointelegraph.com', 'sec.gov', 'cftc.gov'
            ],
            'medium_reputation': [
                'yahoo.com', 'marketwatch.com', 'investing.com',
                'coinmarketcap.com', 'coingecko.com'
            ],
            'low_reputation': [
                'blogspot.com', 'wordpress.com', 't.me', 'telegram',
                '.biz', '.info', 'pump.fun'
            ]
        }
    
    @lru_cache(maxsize=1000)
    def fast_pattern_analysis(self, content: str) -> Dict[str, float]:
        """Lightning-fast pattern-based analysis using cached patterns"""
        content_lower = content.lower()
        
        # Count pattern matches
        pump_score = sum(1 for pattern in self.manipulation_patterns['pump_signals'] 
                        if pattern in content_lower)
        dump_score = sum(1 for pattern in self.manipulation_patterns['dump_signals']
                        if pattern in content_lower)
        urgency_score = sum(1 for pattern in self.manipulation_patterns['urgency_words']
                           if pattern in content_lower)
        emotion_score = sum(1 for pattern in self.manipulation_patterns['emotional_triggers']
                           if pattern in content_lower)
        
        # Normalize scores (0-1 scale)
        content_length = len(content.split())
        pump_norm = min(1.0, pump_score / max(1, content_length * 0.1))
        dump_norm = min(1.0, dump_score / max(1, content_length * 0.1))
        urgency_norm = min(1.0, urgency_score / max(1, content_length * 0.05))
        emotion_norm = min(1.0, emotion_score / max(1, content_length * 0.1))
        
        return {
            'pump_indicators': pump_norm,
            'dump_indicators': dump_norm,
            'urgency_level': urgency_norm,
            'emotional_manipulation': emotion_norm,
            'overall_manipulation_risk': (pump_norm + dump_norm + urgency_norm + emotion_norm) / 4
        }
    
    @lru_cache(maxsize=500)
    def fast_domain_analysis(self, url: str) -> Dict[str, float]:
        """Fast domain reputation analysis"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
        except:
            return {'domain_score': 50.0, 'confidence': 0.3}
        
        # Check cached patterns
        if any(rep_domain in domain for rep_domain in self.domain_patterns['high_reputation']):
            return {'domain_score': 85.0, 'confidence': 0.9}
        elif any(rep_domain in domain for rep_domain in self.domain_patterns['medium_reputation']):
            return {'domain_score': 65.0, 'confidence': 0.7}
        elif any(rep_domain in domain for rep_domain in self.domain_patterns['low_reputation']):
            return {'domain_score': 25.0, 'confidence': 0.8}
        else:
            return {'domain_score': 50.0, 'confidence': 0.5}
    
    def enhanced_prompt_template(self, content: str, url: str = "", context: str = "") -> str:
        """Optimized prompt template for better AI responses"""
        
        # Get fast pre-analysis
        pattern_analysis = self.fast_pattern_analysis(content)
        domain_analysis = self.fast_domain_analysis(url) if url else {}
        
        prompt = f"""
As a financial misinformation detection expert, analyze this content with focus on:

CONTENT: "{content[:500]}..."  # Truncate for efficiency
URL: "{url}"

PRE-ANALYSIS HINTS:
- Manipulation patterns detected: {pattern_analysis.get('overall_manipulation_risk', 0):.2f}
- Domain reputation: {domain_analysis.get('domain_score', 50)}/100

ANALYZE FOR:
1. Credibility (factual accuracy, logical consistency)
2. Manipulation risk (emotional triggers, urgency tactics)
3. Source reliability (domain authority, editorial standards)
4. Market impact potential (audience reach, timing)

RESPOND WITH STRUCTURED JSON:
{{
    "credibility_score": <0-100>,
    "manipulation_risk": <0-100>,
    "confidence": <0.0-1.0>,
    "key_indicators": ["indicator1", "indicator2", "indicator3"],
    "risk_factors": ["factor1", "factor2"],
    "reasoning": "Brief 2-sentence explanation"
}}

Focus on the most critical indicators. Be concise but accurate.
"""
        return prompt
    
    async def analyze_content_enhanced(self, content: str, url: str = "") -> Dict:
        """Enhanced content analysis with caching and optimization"""
        
        # Check cache first
        cache_key = self._get_cache_key(f"{content}:{url}", "content")
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            return self.cache[cache_key].result
        
        # Fast pre-screening
        if len(content.strip()) < 10:
            return {
                'credibility_score': 40,
                'manipulation_risk': 20,
                'confidence': 0.3,
                'reasoning': 'Content too short for reliable analysis'
            }
        
        try:
            # Use enhanced prompt
            prompt = self.enhanced_prompt_template(content, url)
            
            # Optimized API call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fastest model
                messages=[
                    {"role": "system", "content": "You are a concise financial misinformation analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,  # Limit response length
                temperature=0.1,  # Low temperature for consistency
                timeout=10  # Quick timeout
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            
            try:
                # Try to parse JSON
                result = json.loads(result_text)
            except:
                # Fallback parsing
                result = self._fallback_parse(result_text, content, url)
            
            # Enhance with fast pattern analysis
            pattern_results = self.fast_pattern_analysis(content)
            domain_results = self.fast_domain_analysis(url) if url else {}
            
            # Combine results intelligently
            final_result = self._combine_results(result, pattern_results, domain_results)
            
            # Cache the result
            self._cache_result(cache_key, final_result, ttl=1800)  # 30 min cache
            
            return final_result
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            # Fast fallback analysis
            return self._fast_fallback_analysis(content, url)
    
    def _combine_results(self, ai_result: Dict, pattern_result: Dict, domain_result: Dict) -> Dict:
        """Intelligently combine AI and pattern-based results"""
        
        # Get base scores
        ai_cred = ai_result.get('credibility_score', 50)
        ai_manip = ai_result.get('manipulation_risk', 50)
        
        # Adjust based on patterns
        pattern_adjustment = pattern_result.get('overall_manipulation_risk', 0) * 30
        domain_adjustment = (domain_result.get('domain_score', 50) - 50) * 0.6
        
        # Calculate final scores
        final_credibility = max(0, min(100, ai_cred + domain_adjustment - pattern_adjustment))
        final_manipulation = max(0, min(100, ai_manip + pattern_adjustment))
        
        # Calculate confidence based on consistency
        consistency = 1.0 - abs(ai_manip/100 - pattern_result.get('overall_manipulation_risk', 0.5)) * 0.5
        final_confidence = min(0.95, max(0.1, consistency * ai_result.get('confidence', 0.5)))
        
        return {
            'credibility_score': round(final_credibility, 1),
            'manipulation_risk': round(final_manipulation, 1),
            'confidence': round(final_confidence, 2),
            'reasoning': ai_result.get('reasoning', 'Analysis completed'),
            'key_indicators': ai_result.get('key_indicators', []),
            'risk_factors': ai_result.get('risk_factors', []),
            'pattern_signals': pattern_result,
            'domain_analysis': domain_result,
            'analysis_time': datetime.now().isoformat(),
            'cache_hit': False
        }
    
    def _fast_fallback_analysis(self, content: str, url: str = "") -> Dict:
        """Ultra-fast fallback when AI is unavailable"""
        
        pattern_results = self.fast_pattern_analysis(content)
        domain_results = self.fast_domain_analysis(url) if url else {'domain_score': 50}
        
        # Simple scoring logic
        credibility = domain_results['domain_score'] - (pattern_results['overall_manipulation_risk'] * 40)
        manipulation = pattern_results['overall_manipulation_risk'] * 80 + 10
        
        return {
            'credibility_score': max(10, min(90, credibility)),
            'manipulation_risk': max(10, min(90, manipulation)),
            'confidence': 0.4,
            'reasoning': 'Fallback pattern-based analysis (AI unavailable)',
            'key_indicators': ['pattern-based-analysis'],
            'risk_factors': [k for k, v in pattern_results.items() if v > 0.3],
            'pattern_signals': pattern_results,
            'domain_analysis': domain_results,
            'analysis_time': datetime.now().isoformat(),
            'fallback_mode': True
        }
    
    def _fallback_parse(self, text: str, content: str, url: str) -> Dict:
        """Parse AI response when JSON parsing fails"""
        
        # Simple regex-based extraction
        import re
        
        cred_match = re.search(r'credibility["\']?\s*:\s*(\d+)', text, re.IGNORECASE)
        manip_match = re.search(r'manipulation["\']?\s*:\s*(\d+)', text, re.IGNORECASE)
        conf_match = re.search(r'confidence["\']?\s*:\s*(0\.\d+|\d+)', text, re.IGNORECASE)
        
        credibility = int(cred_match.group(1)) if cred_match else 50
        manipulation = int(manip_match.group(1)) if manip_match else 50
        confidence = float(conf_match.group(1)) if conf_match else 0.5
        
        return {
            'credibility_score': credibility,
            'manipulation_risk': manipulation,
            'confidence': min(1.0, confidence),
            'reasoning': text[:200] + "..." if len(text) > 200 else text,
            'key_indicators': ['ai-response-parsed'],
            'risk_factors': ['parsing-fallback']
        }
    
    def batch_analyze(self, contents: List[Tuple[str, str]]) -> List[Dict]:
        """Efficient batch analysis with smart caching"""
        results = []
        
        for content, url in contents:
            # Check cache first
            cache_key = self._get_cache_key(f"{content}:{url}", "content")
            
            if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
                result = self.cache[cache_key].result.copy()
                result['cache_hit'] = True
                results.append(result)
            else:
                # Process non-cached items
                results.append(self._fast_fallback_analysis(content, url))
        
        return results
    
    def cleanup_cache(self):
        """Clean expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, cache_entry in self.cache.items()
            if current_time - cache_entry.timestamp > cache_entry.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        print(f"Cleaned {len(expired_keys)} expired cache entries")

# Global instance
lightweight_ai = LightweightAIEnhancer()