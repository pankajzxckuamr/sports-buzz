# 📊 PlayerBuzz - Sports Data Intelligence Platform

A full-stack application for aggregating, processing, and visualizing athlete-focused sports data with real-time social media integration and AI-powered insights.

## 🎯 Overview

PlayerBuzz is a three-tier system that crawls sports data from multiple sources, enriches it with AI/LLM capabilities, and presents it through an intuitive web interface. It combines web scraping, data processing, search indexing, and modern web technologies to deliver actionable sports intelligence.

## 🏗️ Architecture

### Backend (TypeScript/Node.js)
- RESTful API with Express.js
- PostgreSQL database with migrations
- Elasticsearch for full-text search
- Redis-based message queues (BullMQ)
- LLM integration for content enrichment
- Distributed workers for async processing (classification, deduplication, enrichment)
- Content caching with trending analytics

### Crawler (Python)
- Headless browser automation with Puppeteer integration
- Multi-source web scraping (sports news, player profiles)
- Social media data collection:
  - Twitter/X API integration
  - Instagram scraping
  - YouTube metadata extraction
- DNS resolution and network resilience
- Bulk data ingestion to backend API

### Frontend (React + Vite)
- Modern SPA with TypeScript
- Multi-page application:
  - Landing page
  - Main feed with trending content
  - Player profiles and selection
  - Content detail views
  - Explore/discovery pages
- Real-time API communication
- Responsive UI with Tailwind CSS

## ✨ Key Features

- **Data Aggregation** - Unified athlete and sports content from 10+ sources
- **Social Media Integration** - Real-time Twitter, Instagram, YouTube data
- **Content Enrichment** - LLM-powered text analysis and categorization
- **Search & Discovery** - Elasticsearch-powered full-text search
- **Performance** - Optimized with caching, indexing, and database pooling
- **Scalability** - Distributed worker architecture with message queues
- **Deduplication** - Intelligent duplicate content detection and removal

## 🛠️ Tech Stack

| Component | Technologies |
|-----------|--------------|
| **Backend API** | Node.js, Express.js, TypeScript, PostgreSQL |
| **Search** | Elasticsearch |
| **Message Queue** | Redis, BullMQ |
| **LLM** | OpenAI API integration |
| **Crawler** | Python, Selenium/Puppeteer, social media APIs |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS |
| **Infrastructure** | Docker, Docker Compose |

## 📦 Project Structure

```
playerBuzz/
├── sports-data-backend/      # Node.js REST API
│   ├── src/
│   │   ├── api/              # Routes & serializers
│   │   ├── workers/          # Async workers
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Data access
│   │   ├── db/               # Database & migrations
│   │   └── search/           # Elasticsearch integration
│   └── docker-compose.yml
│
├── sportsbuzz/               # Python data crawler
│   ├── crawler.py            # Web scraping engine
│   ├── social/               # Social media integrations
│   ├── parser.py             # Content parsing
│   └── config/               # Configuration files
│
└── stitch/                   # React web application
    └── web/
        ├── src/
        │   ├── pages/        # Page components
        │   ├── components/   # Reusable components
        │   ├── api/          # API client
        │   └── styles/       # Styling
        └── vite.config.ts
```

## 🚀 Quick Start

See individual README files in each directory for detailed setup instructions.

**Backend:** `sports-data-backend/README.md`  
**Crawler:** `sportsbuzz/README.md`  
**Frontend:** `stitch/web/index.html`

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Elasticsearch 7.x+
- Docker & Docker Compose (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/pankajzxckuamr/sports-buzz.git
cd sports-buzz
```

2. **Backend Setup**
```bash
cd sports-data-backend
npm install
# Configure .env with database credentials
npm run dev
```

3. **Crawler Setup**
```bash
cd sportsbuzz
pip install -r requirements.txt
# Configure config files
python start.py
```

4. **Frontend Setup**
```bash
cd stitch/web
npm install
npm run dev
```

5. **Docker Compose** (all services)
```bash
docker-compose up
```

## 📝 Features In Development

- Real-time sports notifications
- Advanced player analytics dashboard
- Predictive modeling for player performance
- Multi-language support
- Mobile application

## 📄 License

MIT License - feel free to use this project for your own purposes.

## 👤 Author

Pankaj - [@pankajzxckuamr](https://github.com/pankajzxckuamr)

---

**Status**: 🚀 Active Development
