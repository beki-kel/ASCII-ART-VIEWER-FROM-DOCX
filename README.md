# 🎨 ASCII Art Viewer

A professional web application for extracting and displaying ASCII art from Google Docs with real-time processing feedback and multiple extraction strategies.

## 🚀 Tech Stack

**Backend:**
- FastAPI - Modern async web framework
- Pydantic - Data validation and type safety
- WebSockets - Real-time communication
- Python 3.11+

**Frontend:**
- Vanilla JavaScript (ES6+)
- Font Awesome - Icon library
- CSS3 with custom properties
- WebSocket API

## ✨ Clean Code Architecture

**One Class Per File**: Each service class is isolated in its own module for better maintainability and testability.

**Separation of Concerns:**
- `models/` - Pydantic schemas for data validation
- `services/` - Business logic (Parser, Processor)
- `templates/` - HTML presentation layer
- `static/` - Client-side assets (CSS, JS)

**Type Safety**: Full type hints throughout the codebase with Pydantic models ensuring data integrity.

**Service Layer Pattern**: Business logic abstracted into reusable service classes with clear responsibilities.

## � UI Features

- **4 Theme Options**: Dark, Cyberpunk, Matrix, Classic
- **8 Color Modes**: Auto, Rainbow, Highlight, Gradient, Matrix, Cyberpunk, Classic, None
- **Real-time Terminal**: Live processing feedback with status updates
- **Responsive Design**: Mobile-friendly layout with adaptive components
- **Smooth Animations**: Modern transitions and visual effects
- **Export Options**: Download as TXT, JSON, HTML, or SVG

## � Folder Architecture

```
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── run_webapp.sh          # Launch script
├── test_webapp.py         # Integration tests
├── app/
│   ├── models/
│   │   ├── schemas.py     # Pydantic data models
│   ├── services/
│   │   ├── ascii_art_parser.py    # HTML parsing logic
│   │   ├── parser_service.py      # Extraction strategies
│   │   ├── processor.py           # Main processing workflow
│   │   └── parser.py              # Re-export module
│   ├── static/
│   │   ├── style.css      # UI styling
│   │   └── app.js         # Client-side logic
│   └── templates/
│       └── index.html     # Main UI template
```

## 📋 Requirements

```bash
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
jinja2>=3.1.0
requests>=2.25.0
python-multipart>=0.0.6
```

## � Installation & Setup

### Option 1: Docker (Recommended)

```bash
# Quick start with Docker Compose
docker-compose up --build

# Access the application at: http://localhost:8000
```

### Option 2: Traditional Python Setup

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Run the application
./run_webapp.sh
# Or: uvicorn main:app --host 127.0.0.1 --port 8000

# 3. Open browser
# Navigate to: http://localhost:8000
```

### Docker Commands

```bash
# Development mode with hot reload
docker-compose --profile dev up ascii-art-viewer-dev --build

# Production mode
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

📋 **See [DOCKER.md](DOCKER.md) for detailed Docker setup and deployment instructions.**

## 🔗 API Endpoints

- `GET /` - Web interface
- `POST /api/process` - Start ASCII art extraction
- `GET /api/session/{id}` - Get session results
- `WS /ws/{id}` - Real-time updates
- `GET /api/health` - Health check
- `GET /docs` - API documentation

## 🧪 Testing

```bash
# Run integration tests
python test_webapp.py http://localhost:8000
```

## 🎯 Key Features

**Extraction Strategies:**
1. Coordinate-based rendering (tables with X,Y coordinates)
2. Table-based extraction (direct table content)
3. Pre-formatted blocks (`<pre>` tags)
4. Paragraph analysis (ASCII character density)

**Real-time Processing:**
- WebSocket updates for live feedback
- Step-by-step progress tracking
- Performance metrics and timing

**Export Options:**
- Text files (.txt)
- JSON data (.json)
- HTML pages (.html)
- SVG vectors (.svg)
