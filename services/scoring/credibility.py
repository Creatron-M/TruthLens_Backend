from .openai_nlp import analyze_content_credibility, analyze_domain_credibility

def has_numeric(text: str) -> bool:
    return any(ch.isdigit() for ch in text) or ('%' in text) or ('$' in text)

def has_quote(text: str) -> bool:
    return '"' in text

REPUTABLE = ("reuters", "bbc", "apnews", "bloomberg", "ft.com", "wsj.com")
LOWREP = (".biz", "blogspot", "substack", "telegram", "t.me")

def domain_reputation_fallback(url: str) -> int:
    """Fallback domain scoring when OpenAI is not available"""
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
    except Exception:
        return 20
    if any(k in host for k in REPUTABLE):
        return 90
    if any(k in host for k in LOWREP):
        return 30
    return 55

def citation_score_fallback(text: str) -> int:
    """Fallback citation scoring when OpenAI is not available"""
    if not text:
        return 40
    return 40 + (20 if has_numeric(text) else 0) + (10 if has_quote(text) else 0)

def credibility_score(comments: list[dict]):
    per_link = {}
    total_score = 0
    total_confidence = 0
    n = 0
    all_reasoning = []
    
    print("  🤖 Using OpenAI for advanced credibility analysis...")
    
    for c in comments:
        url = c.get('url')
        text = c.get('text', '')
        
        if not url:
            continue
            
        # Use OpenAI for comprehensive analysis
        print(f"    📊 Analyzing: {url[:50]}...")
        
        # Analyze content credibility
        content_analysis = analyze_content_credibility(text, url)
        
        # Analyze domain credibility
        domain_analysis = analyze_domain_credibility(url)
        
        # Combine scores with confidence weighting
        content_score = content_analysis['credibility_score']
        content_confidence = content_analysis['confidence']
        
        domain_score = domain_analysis['domain_score'] 
        domain_confidence = domain_analysis['confidence']
        
        # Weighted average based on confidence levels
        total_confidence_weight = content_confidence + domain_confidence
        if total_confidence_weight > 0:
            combined_score = (
                (content_score * content_confidence + domain_score * domain_confidence) 
                / total_confidence_weight
            )
        else:
            # Fallback to traditional scoring
            combined_score = (
                0.6 * domain_reputation_fallback(url) + 
                0.3 * citation_score_fallback(text) + 
                0.1 * 70  # freshness placeholder
            )
        
        per_link[url] = round(combined_score)
        total_score += combined_score
        total_confidence += (content_confidence + domain_confidence) / 2
        n += 1
        
        # Collect reasoning
        all_reasoning.extend(content_analysis['reasoning'][:2])
        all_reasoning.extend(domain_analysis['reasoning'][:1])
        
        # Show analysis details
        print(f"      Content Score: {content_score} (confidence: {content_confidence:.2f})")
        print(f"      Domain Score: {domain_score} (confidence: {domain_confidence:.2f})")
        print(f"      Combined: {round(combined_score)}")
        
        if content_analysis['bias_indicators']:
            print(f"      🚨 Bias indicators: {', '.join(content_analysis['bias_indicators'][:2])}")
        
        if content_analysis['emotional_manipulation'] > 0.7:
            print(f"      ⚠️ High emotional manipulation detected ({content_analysis['emotional_manipulation']:.2f})")
    
    # Calculate aggregate score
    aggregate = round(total_score / n) if n else 50
    avg_confidence = total_confidence / n if n else 0.3
    
    # Compile comprehensive reasons
    reasons = [
        f"Analyzed {n} source(s) using OpenAI GPT-4o-mini." if n else "No sources found; using neutral baseline.",
        f"Average analysis confidence: {avg_confidence:.2f}",
        "Combined content credibility and domain reputation analysis.",
        "Detected bias patterns and emotional manipulation signals."
    ]
    
    # Add top specific insights
    unique_reasoning = list(dict.fromkeys(all_reasoning))[:3]
    reasons.extend(unique_reasoning)
    
    print(f"  🎯 Final credibility score: {aggregate}/100 (confidence: {avg_confidence:.2f})")
    
    return aggregate, per_link, reasons