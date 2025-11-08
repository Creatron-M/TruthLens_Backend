from typing import Optional, Dict, List
from pydantic import BaseModel

class MarketData(BaseModel):
    market_id: str
    name: str
    question: str
    price_24h: List[float]
    volume_24h: List[int]
    current_price: float
    market_cap: float
    change_24h: float

class OracleReading(BaseModel):
    market_id: str
    cred_score: int
    risk_index: int
    meta_uri: str
    signer: str
    timestamp: int

class AnalysisResult(BaseModel):
    market_id: str
    credibility_score: int
    risk_index: int
    confidence: float
    links_analyzed: int
    metadata: Dict
    tx_hash: Optional[str] = None
    ipfs_hash: Optional[str] = None

class CustomQueryRequest(BaseModel):
    question: str

class CustomQueryResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str]
    metadata: Dict

class OracleStatus(BaseModel):
    total_markets: int
    active_analyses: int
    total_attestations: int
    last_update: int
    blockchain_connected: bool

class UserSettings(BaseModel):
    profile: Dict
    notifications: Dict
    privacy: Dict
    api: Dict
    display: Dict

class AnalyticsData(BaseModel):
    markets_analyzed: int
    success_rate: float
    avg_confidence: float
    total_attestations: int
    performance_metrics: Dict
    time_series: List[Dict]

class HistoryData(BaseModel):
    analyses: List[Dict]
    total_count: int
    
class BlockchainData(BaseModel):
    transactions: List[Dict]
    total_attestations: int
    contract_address: str
    network: str

class SystemMetrics(BaseModel):
    uptime: int
    request_count: int
    error_rate: float
    response_times: Dict
    service_status: Dict