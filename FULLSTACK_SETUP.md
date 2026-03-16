# Garden Full-Stack Platform Setup Guide

Complete MLflow-integrated model arena platform with drag-and-drop UI and ontology-based model matching.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                   │
│  • Drag-and-drop model selection                            │
│  • Ontology-based compatibility suggestions                 │
│  • Real-time experiment dashboard                           │
│  • MLflow UI integration                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                  Backend (FastAPI)                           │
│  • Model registry with ontology support                     │
│  • Arena management                                         │
│  • Match execution                                          │
│  • Compatibility matching algorithm                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
┌──────────▼─────────┐  ┌─────────▼──────────┐
│  Garden Core       │  │   MLflow Backend   │
│  • ELO ratings     │  │  • Experiment      │
│  • Tournaments     │  │    tracking        │
│  • Leaderboards    │  │  • Metrics logging │
│  • Ontologies      │  │  • Artifact storage│
└────────────────────┘  └────────────────────┘
```

## 📦 Components

### 1. **Model Ontology System** (`garden/ontology.py`)
- Defines input/output schemas for models
- Task type classification (text generation, QA, classification, etc.)
- Compatibility scoring algorithm
- Predefined templates for common model types

### 2. **REST API Backend** (`api/main.py`)
- FastAPI server on port 8000
- Endpoints for models, arenas, matches, tournaments
- MLflow integration endpoints
- Compatibility matching API

### 3. **React Frontend** (`frontend/`)
- Modern UI with Tailwind CSS
- Drag-and-drop arena builder (react-dnd)
- Real-time experiment dashboard (recharts)
- Compatible model suggestions based on ontology

### 4. **MLflow Integration**
- Real MLflow library (not custom implementation)
- Automatic experiment tracking
- Run metrics and parameters
- UI accessible at http://localhost:5000

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.10+
python3 --version

# Node.js 18+
node --version
npm --version
```

### 1. Install Python Dependencies
```bash
cd /Users/jg/mind
pip3 install -r requirements.txt
```

**Required packages:**
- `mlflow>=2.9.0` - Real MLflow tracking
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pandas` - Data manipulation
- `numpy` - Numerical operations

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 3. Start MLflow UI (Terminal 1)
```bash
cd /Users/jg/mind
mlflow ui --backend-store-uri ./mlruns --port 5000
```
Access at: **http://localhost:5000**

### 4. Start Backend API (Terminal 2)
```bash
cd /Users/jg/mind
python3 api/main.py
```
API will be available at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### 5. Start Frontend (Terminal 3)
```bash
cd /Users/jg/mind/frontend
npm run dev
```
UI will be available at: **http://localhost:3000**

## 🎯 Usage

### Register Models with Ontology

```python
from garden import Garden, ontology

garden = Garden(enable_mlflow_tracking=True)

# Register a text generation model
model_ont = ontology.text_generation_ontology(
    model_id="gpt-mini",
    max_length=2048
)

model = garden.register_model(
    name="GPT-Mini",
    version="1.0",
    ontology=model_ont
)
```

### Use the Web UI

1. **Model Library** (Left Sidebar)
   - View all registered models
   - See model stats (win rate, matches)
   - Models with ontologies show a sparkle icon

2. **Arena Builder** (Main Area)
   - Drag models from library into arena slots
   - System suggests compatible models based on ontology
   - Compatibility scores shown with visual indicators
   - Select arena and run matches

3. **Dashboard** (Top Nav)
   - View experiment statistics
   - Real-time match score charts
   - ELO rating evolution
   - Recent runs table

### API Examples

```bash
# List all models
curl http://localhost:8000/models

# Get compatible models for a specific model
curl -X POST http://localhost:8000/models/{model_id}/compatible \
  -H "Content-Type: application/json" \
  -d '{"min_score": 0.5}'

# Run a match
curl -X POST http://localhost:8000/matches \
  -H "Content-Type: application/json" \
  -d '{
    "model_a_id": "abc123",
    "model_b_id": "def456",
    "arena_id": "ghi789"
  }'
```

## 🧠 Ontology System

### Supported Task Types
- `TEXT_GENERATION` - LLMs, completion models
- `TEXT_CLASSIFICATION` - Sentiment, topic classification
- `QUESTION_ANSWERING` - QA systems, extractive QA
- `SUMMARIZATION` - Text summarization
- `TRANSLATION` - Machine translation
- `IMAGE_CLASSIFICATION` - Image classifiers
- `OBJECT_DETECTION` - Object detection models
- `CUSTOM` - Custom task types

### Compatibility Scoring

Models are scored on:
1. **Task Type Match** (40%) - Same task type
2. **Input Compatibility** (20%) - Compatible input data types
3. **Output Compatibility** (20%) - Compatible output data types
4. **Capability Overlap** (10%) - Shared capabilities
5. **Tag Similarity** (10%) - Common tags

Score range: 0.0 (incompatible) to 1.0 (perfect match)

### Example Ontology Definition

```python
from garden.ontology import ModelOntology, IOSchema, DataType, TaskType

ontology = ModelOntology(
    model_id="my-model",
    task_type=TaskType.TEXT_GENERATION,
    input_schema=IOSchema(
        data_type=DataType.TEXT,
        description="Input prompt",
        constraints={'max_length': 2048}
    ),
    output_schema=IOSchema(
        data_type=DataType.TEXT,
        description="Generated text"
    ),
    capabilities={'generation', 'completion', 'chat'},
    tags={'llm', 'transformer', 'gpt'}
)
```

## 📊 Features

### Frontend Features
✅ Drag-and-drop model selection  
✅ Ontology-based compatibility matching  
✅ Visual compatibility score indicators  
✅ Real-time experiment dashboard  
✅ Interactive charts (match scores, ELO evolution)  
✅ Recent runs table with status  
✅ Direct MLflow UI link  
✅ Responsive design with Tailwind CSS  

### Backend Features
✅ RESTful API with FastAPI  
✅ Real MLflow integration (not custom)  
✅ Automatic experiment tracking  
✅ Model ontology registry  
✅ Compatibility matching algorithm  
✅ Tournament support  
✅ Arena management  
✅ CORS enabled for frontend  

### MLflow Integration
✅ Experiments per arena/tournament  
✅ Runs per match  
✅ Automatic parameter logging  
✅ Automatic metric logging  
✅ Tag-based organization  
✅ Viewable in MLflow UI  

## 🔧 Development

### Project Structure
```
/Users/jg/mind/
├── garden/                  # Core library
│   ├── core.py             # Main Garden class
│   ├── ontology.py         # NEW: Ontology system
│   ├── tracking.py         # MLflow wrapper
│   ├── metrics.py          # Custom metrics
│   └── ...
├── api/                     # NEW: Backend API
│   └── main.py             # FastAPI application
├── frontend/                # NEW: React UI
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── lib/            # API client
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Main app
│   ├── package.json
│   └── vite.config.ts
├── test_mlflow_integration.py  # Tests
└── requirements.txt         # Python deps
```

### Adding New Model Types

1. **Define Ontology Template**:
```python
# In garden/ontology.py
def my_custom_ontology(model_id: str, **kwargs) -> ModelOntology:
    return ModelOntology(
        model_id=model_id,
        task_type=TaskType.CUSTOM,
        input_schema=IOSchema(...),
        output_schema=IOSchema(...),
        **kwargs
    )
```

2. **Register Model**:
```python
model = garden.register_model(
    name="My Model",
    ontology=my_custom_ontology("model-id")
)
```

3. **Models auto-appear in UI** with compatibility suggestions

## 🎨 UI Customization

Edit frontend theme in `frontend/src/index.css` and Tailwind config.

### Color Scheme
- Primary: Purple (`#a855f7`)
- Secondary: Pink (`#ec4899`)
- Background: Slate-900 (`#0f172a`)
- Accents: Blue, Green for stats

## 📈 Monitoring

### MLflow UI
- View all experiments: http://localhost:5000
- Compare runs side-by-side
- Download artifacts
- Search and filter runs

### API Metrics
- FastAPI auto-docs: http://localhost:8000/docs
- Stats endpoint: `GET /stats`
- Health check: `GET /`

## 🐛 Troubleshooting

**Frontend won't start:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

**Backend 404 errors:**
- Ensure API is running on port 8000
- Check CORS settings in `api/main.py`

**MLflow UI connection issues:**
- Verify MLflow is running: `mlflow ui --backend-store-uri ./mlruns`
- Check port 5000 is not in use

**Models not showing compatibility:**
- Ensure models have ontology defined
- Check compatibility score threshold (default 0.5)

## 🚢 Production Deployment

### Backend
```bash
# Use production ASGI server
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
cd frontend
npm run build
# Serve dist/ folder with nginx or similar
```

### MLflow
Consider using database backend instead of file store:
```python
mlflow.set_tracking_uri("postgresql://user:pass@host/db")
```

## 📝 Next Steps

- [ ] Add authentication/authorization
- [ ] Implement model versioning
- [ ] Add batch match execution
- [ ] Create tournament brackets UI
- [ ] Add model comparison view
- [ ] Implement real-time match streaming
- [ ] Add arena rental/scheduling
- [ ] Create admin dashboard

## 🌱 Summary

You now have a complete full-stack platform that:
1. Uses **real MLflow** for experiment tracking (viewable in UI)
2. Provides **drag-and-drop** model arena building
3. Suggests **compatible models** based on input/output ontologies
4. Tracks everything automatically with MLflow backend
5. Has a beautiful modern UI with real-time updates

**Three terminals, one platform - start experimenting!** 🚀
