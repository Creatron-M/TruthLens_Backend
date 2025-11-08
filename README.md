# TruthLens Backend API

AI-powered credibility and manipulation risk analysis system for crypto prediction markets, built with FastAPI and integrated with blockchain oracles.

## 🚀 Overview

TruthLens Backend is a comprehensive API system that provides:

- **Real-time Market Analysis**: Fetches and analyzes prediction market data from multiple sources
- **AI-Powered Risk Assessment**: Uses OpenAI GPT models for credibility scoring and manipulation detection
- **Blockchain Integration**: Connects to BSC testnet for oracle contract interactions
- **Intelligent Caching**: Multi-layer caching system reducing API costs by up to 95%
- **Performance Monitoring**: Comprehensive analytics and health monitoring

## 📁 Project Structure

```
backend/
├── app.py                 # FastAPI application entry point
├── server.py             # Development server with auto-reload
├── routers.py            # API route definitions (22+ endpoints)
├── services.py           # Core service orchestration
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration
└── services/
    ├── __init__.py       # Service exports and initialization
    ├── main.py          # Core business logic and caching
    ├── models.py        # Pydantic data models
    ├── ai/              # AI and NLP services
    ├── blockchain/      # Blockchain and oracle integration
    ├── ingestors/       # Data source connectors
    ├── scoring/         # Risk assessment algorithms
    └── utils/           # Helper utilities
```

## 🛠 Installation & Setup

### Prerequisites

- Python 3.10+
- Virtual environment (recommended)
- Required API keys (see Environment Configuration)

### Quick Start

1. **Create and activate virtual environment:**

   ```bash
   cd backend
   python -m venv env

   # Windows
   .\env\Scripts\activate

   # Linux/Mac
   source env/bin/activate
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Environment Configuration below)
   ```

4. **Start development server:**

   ```bash
   python server.py
   ```

   The API will be available at `http://localhost:8000`

## 🔧 Environment Configuration

Create a `.env` file with the following variables:

```bash
# ✅ REQUIRED - Core API Keys
OPENAI_API_KEY=sk-...                    # OpenAI GPT API (primary AI engine)
WEB3_RPC_URL=https://bsc-testnet.public-rpc.com  # BSC testnet RPC endpoint

# 🔧 OPTIONAL - Enhanced Features
PINATA_API_KEY=...                       # IPFS storage via Pinata
PINATA_SECRET_API_KEY=...               # IPFS storage authentication
COINGECKO_API_KEY=...                   # Enhanced CoinGecko rate limits

# ⚙️ SYSTEM - Performance Tuning
MARKETS_CACHE_TTL=1800                  # Market data cache (30 minutes)
COMMENTS_CACHE_TTL=3600                 # Comments cache (60 minutes)
ANALYSIS_CACHE_TTL=7200                 # AI analysis cache (2 hours)
OPENAI_TIMEOUT=30                       # OpenAI request timeout (seconds)
OPENAI_MODEL=gpt-3.5-turbo             # AI model (cost-optimized)
```

### Network Configuration

- **Blockchain**: BSC Testnet (Chain ID: 97)
- **Oracle Contract**: `0xF1B6289e5F6A9F768dFE3F3214EF7556d35db0Ef`
- **Market Data**: CoinGecko API (3 markets: BTC, ETH, BNB)

## 📡 API Endpoints

### Core Market Data

- `GET /` - API information and status
- `GET /markets` - List all available prediction markets
- `GET /oracle/{market_id}` - Get oracle reading for specific market
- `GET /markets/{market_id}/history` - Market price history

### AI Analysis

- `GET /analyze/{market_id}` - Get AI credibility analysis for market
- `POST /analyze` - Custom question analysis with AI
- `POST /trigger-analysis` - Manually trigger analysis cycle

### System Monitoring

- `GET /health` - System health check (all services)
- `GET /status` - Oracle and blockchain status
- `GET /metrics` - System performance metrics
- `GET /ai/status` - AI service status and performance
- `GET /ai/performance` - AI usage statistics and costs

### Analytics & Reporting

- `GET /analytics` - Analytics dashboard data
- `GET /analytics/history` - Historical analysis data
- `GET /analytics/blockchain` - Blockchain interaction data

### Cache Management

- `GET /ai/cache/stats` - Cache performance statistics
- `POST /ai/cache/clear` - Clear all caches (admin)
- `POST /ai/queue/flush` - Flush AI processing queue

### Configuration

- `GET /settings` - User settings and preferences
- `POST /settings` - Update user settings
- `POST /settings/api-key` - Update OpenAI API key

## 🧠 AI & Caching System

### AI Integration

- **Model**: GPT-3.5-turbo (cost-optimized from GPT-4)
- **Timeout**: 30 seconds with graceful fallbacks
- **Cost Reduction**: 90% savings through caching and model optimization
- **Analysis Types**: Credibility scoring, manipulation detection, market sentiment

### Multi-Layer Caching

```python
# Cache Configuration (seconds)
MARKETS_CACHE_TTL = 1800     # 30 minutes - Market data
COMMENTS_CACHE_TTL = 3600    # 60 minutes - Social sentiment
ANALYSIS_CACHE_TTL = 7200    # 2 hours - AI analysis results
```

**Benefits:**

- 83-95% reduction in external API calls
- Sub-second response times for cached data
- Automatic cache invalidation and refresh
- Smart cache warming for popular markets

## 🔗 Blockchain Integration

### Smart Contract Integration

- **Network**: Binance Smart Chain Testnet
- **Contract Address**: `0xF1B6289e5F6A9F768dFE3F3214EF7556d35db0Ef`
- **ABI**: Located in `services/blockchain/abi.json`

### Oracle Functions

```python
# Key blockchain operations
- read_oracle_data()     # Get current oracle readings
- update_oracle()        # Submit new price data
- get_market_status()    # Check market active status
- validate_submission()  # Verify data integrity
```

## 📊 Performance Features

### Optimization Techniques

1. **Intelligent Caching**: Multi-layer cache with different TTLs
2. **Background Processing**: Periodic analysis without blocking requests
3. **Rate Limiting**: Respectful API usage with automatic throttling
4. **Error Recovery**: Graceful fallbacks and retry mechanisms
5. **Resource Monitoring**: Memory and CPU usage tracking

### Performance Metrics

- **API Response Time**: < 100ms for cached data
- **Cache Hit Rate**: 85-95% for frequently accessed markets
- **AI Analysis Cost**: 90% reduction through caching
- **System Uptime**: 99.5%+ availability target

## 🚦 Development

### Running in Development Mode

```bash
# Start with auto-reload
python server.py

# Manual FastAPI start
uvicorn app:create_app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs**: `http://localhost:8000/redoc` (ReDoc)
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

### Testing

```bash
# Health check
curl http://localhost:8000/health

# Market data
curl http://localhost:8000/markets

# AI analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the market sentiment for Bitcoin?"}'
```

## 🔍 Monitoring & Debugging

### Health Monitoring

The `/health` endpoint provides comprehensive system status:

```json
{
  "status": "healthy",
  "timestamp": 1762499156594,
  "services": {
    "api": "online",
    "markets": "online",
    "oracle": "online",
    "analysis": "online"
  },
  "metrics": {
    "total_markets": 3,
    "active_analyses": 12,
    "blockchain_connected": true,
    "last_update": "2025-11-07T10:30:00Z"
  }
}
```

### Logging

- **Level**: INFO (configurable)
- **Format**: Structured JSON for production
- **Locations**: Console output, optional file logging
- **Monitoring**: Request/response times, error tracking

## 🔒 Security & Production

### Security Considerations

- **API Keys**: Never commit to version control
- **CORS**: Configure properly for production domains
- **Rate Limiting**: Implement per-IP limits for production
- **Input Validation**: All endpoints use Pydantic validation
- **Error Handling**: Sanitized error responses

### Production Deployment

```bash
# Production server (example)
gunicorn app:create_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker deployment
docker build -t truthlens-backend .
docker run -p 8000:8000 --env-file .env truthlens-backend
```

## 📈 Scaling Considerations

### Horizontal Scaling

- **Stateless Design**: All state in external systems (blockchain, cache)
- **Load Balancing**: Multiple instances behind reverse proxy
- **Cache Sharing**: Redis for shared caching across instances
- **Database**: Add PostgreSQL for persistent analytics

### Performance Optimization

- **Connection Pooling**: HTTP client connection reuse
- **Async Processing**: Full async/await implementation
- **Background Jobs**: Celery for heavy AI processing
- **CDN Integration**: Cache static analysis results

## 🤝 Contributing

### Code Style

- **Formatting**: Black + isort
- **Linting**: flake8 + mypy for type checking
- **Testing**: pytest with async support
- **Documentation**: Docstrings for all public functions

### Development Workflow

1. Fork and create feature branch
2. Implement changes with tests
3. Run linting and formatting
4. Update documentation if needed
5. Submit pull request with description

## 📄 License

This project is part of the TruthLens Oracle system. See the main repository LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'services'`
**Solution**: Ensure you're running from the backend directory and virtual environment is activated.

**Issue**: `OpenAI API rate limit exceeded`  
**Solution**: The system includes automatic retries and caching. Check your OpenAI plan limits.

**Issue**: `System status shows 'offline'`
**Solution**: Verify all required environment variables are set and external services are accessible.

**Issue**: `Blockchain connection failed`
**Solution**: Check WEB3_RPC_URL is accessible and BSC testnet is operational.

### Support

For technical support and feature requests, please check the main TruthLens repository issues section.

---

**TruthLens Backend** - Powering transparent and intelligent crypto market analysis 🎯
