# 🧬 Drug Discovery AI System

A comprehensive multi-agent AI system for pharmaceutical research and drug discovery analysis. This system integrates traditional data analysis with cutting-edge machine learning and generative AI to provide insights across market intelligence, clinical trials, patents, literature, and more.

## ✨ Features

### 🤖 Multi-Agent Architecture
- **10 Specialized AI Agents** working together
- **Market Intelligence Agent** - IQVIA and market data analysis
- **EXIM Agent** - Trade and import/export data
- **Patent Agent** - Intellectual property landscape
- **Clinical Trials Agent** - Clinical research data
- **Internal Documents Agent** - Proprietary knowledge base
- **Web Intelligence Agent** - Real-time web research
- **Literature Review Agent** - Scientific publications
- **ML Prediction Agent** - Drug property predictions
- **Generative AI Agent** - Novel drug candidate generation
- **NLP Analysis Agent** - Advanced text analysis

### 🎨 Modern Web Interface
- **Responsive Bootstrap UI** with dark mode
- **Real-time progress tracking** and status updates
- **Interactive data visualizations** (charts, graphs)
- **Search history** and query management
- **PDF report generation** with comprehensive analysis

### 🛡️ Robust & Reliable
- **Automatic fallback systems** for API failures
- **Comprehensive error handling** and recovery
- **Memory management** and resource monitoring
- **Health checks** and system diagnostics
- **Graceful degradation** when components fail

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended for ML features)
- Internet connection for API calls

### One-Command Setup
```bash
# Clone and setup everything automatically
git clone <repository-url>
cd drug_discovery
python start.py
```

The robust startup script will:
- ✅ Check system requirements
- ✅ Install missing dependencies
- ✅ Find available ports
- ✅ Initialize all components
- ✅ Start the web application
- 🌐 Open browser automatically

### Manual Setup (Alternative)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment** (Optional)
   ```bash
   # Create .env file for API keys
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Open http://localhost:5000 in your browser
   - Or use the automatic launcher: `python start.py`

## ⚙️ Configuration

### Environment Variables
Create a `.env` file or set environment variables:

```bash
# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true
SECRET_KEY=your-secret-key

# API Keys (optional - system works without them)
PUBMED_API_KEY=your-pubmed-key
MARKET_API_URL=https://api.example.com
MARKET_API_KEY=your-key
# ... other API keys

# ML Configuration
ENABLE_ML_PREDICTION=true
ENABLE_GENERATIVE_AI=true
ENABLE_NLP_ANALYSIS=true
MAX_MEMORY_GB=4.0
```

### Configuration File
The system creates a `config.json` file automatically. You can edit it directly:

```json
{
  "app": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": true
  },
  "ml": {
    "enable_ml_prediction": true,
    "enable_generative_ai": true,
    "enable_nlp_analysis": true,
    "max_memory_gb": 4.0
  }
}
```

## 🔧 Troubleshooting

### Common Issues & Solutions

#### 1. **Port Already in Use**
```
Port 5000 is in use by another program
```
**Solution:**
- The startup script automatically finds an available port
- Or manually specify a different port: `FLASK_PORT=5001 python start.py`

#### 2. **Memory Issues**
```
High memory usage detected
```
**Solutions:**
- Reduce ML features: Set `ENABLE_ML_*=false` in environment
- Increase memory limit: `MAX_MEMORY_GB=8.0`
- Close other applications

#### 3. **ML Models Not Loading**
```
Failed to load model
```
**Solutions:**
- Check internet connection for model downloads
- Disable ML features: `ENABLE_ML_PREDICTION=false`
- Free up disk space (models need ~2GB)

#### 4. **Import Errors**
```
ImportError: No module named 'xyz'
```
**Solution:**
```bash
pip install -r requirements.txt
# Or install specific package: pip install xyz
```

#### 5. **API Failures**
```
API call failed
```
**Solutions:**
- System automatically uses fallback data
- Check internet connection
- Add API keys to `.env` file for better results
- Check API service status

### Health Check Endpoint
Monitor system health:
```
GET http://localhost:5000/health
```

### Logs
Check logs in:
- Console output (when running)
- `logs/drug_discovery.log` file
- Browser developer tools (Network tab for API calls)

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐
│   Web Interface │    │   Flask Backend  │
│   (Bootstrap)   │◄──►│   (Python)       │
└─────────────────┘    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────┐
│           Master Agent Coordinator          │
└─────────────────────────────────────────────┘
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Market Agent │ │ EXIM Agent  │ │Patent Agent │
└─────────────┘ └─────────────┘ └─────────────┘
        ▼       ▼       ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Clinical     │ │Internal     │ │Web Agent    │
│Agent        │ │Agent        │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
        ▼       ▼       ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Literature   │ │ML Prediction│ │Generative   │
│Agent        │ │Agent        │ │AI Agent     │
└─────────────┘ └─────────────┘ └─────────────┘
                                      ▼
                           ┌─────────────┐
                           │NLP Analysis │
                           │Agent        │
                           └─────────────┘
```

## 🔍 API Endpoints

- `GET /` - Main web interface
- `POST /analyze` - Start analysis job
- `GET /status/<job_id>` - Check analysis progress
- `GET /results/<job_id>` - Get analysis results
- `GET /download/<job_id>` - Download PDF report
- `GET /health` - System health check
- `GET /config` - Current configuration

## 📈 Performance Optimization

### Memory Management
- Automatic memory monitoring
- Model caching and reuse
- Garbage collection triggers
- Configurable memory limits

### Speed Optimizations
- Asynchronous processing where possible
- Model warm-up on startup
- Result caching for repeated queries
- Parallel agent execution (future enhancement)

### Reliability Features
- Automatic retries for failed operations
- Circuit breaker pattern for APIs
- Graceful degradation
- Comprehensive error logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python start.py` (includes health checks)
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Health Check**: Visit `/health` endpoint
- **Logs**: Check `logs/drug_discovery.log`
- **Configuration**: Edit `config.json` or set environment variables
- **Automatic Setup**: Use `python start.py` for hands-free setup

---

**Built with ❤️ for the pharmaceutical research community**

*This system is designed to be robust and work in all circumstances, from development laptops to production servers, with or without internet access, and with varying hardware capabilities.*