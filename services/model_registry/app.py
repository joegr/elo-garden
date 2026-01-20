from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
from huggingface_hub import HfApi, hf_hub_download
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
import os
import json

app = FastAPI(title="Model Registry Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ModelMetadata(BaseModel):
    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str = "1.0.0"
    team_id: str
    huggingface_model_id: Optional[str] = None
    model_type: str = "causal_lm"
    framework: str = "pytorch"
    description: Optional[str] = None
    tags: List[str] = []
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    status: str = "active"
    performance_metrics: Dict[str, float] = {}

class ModelUploadRequest(BaseModel):
    name: str
    team_id: str
    huggingface_model_id: Optional[str] = None
    version: str = "1.0.0"
    description: Optional[str] = None
    tags: List[str] = []

class ModelUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

models_db: Dict[str, ModelMetadata] = {}
hf_api = HfApi()

@app.get("/")
async def root():
    return {
        "service": "Model Registry Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/models/register", response_model=ModelMetadata)
async def register_model(request: ModelUploadRequest):
    model_id = str(uuid.uuid4())
    
    model_params = None
    if request.huggingface_model_id:
        try:
            config = AutoConfig.from_pretrained(request.huggingface_model_id)
            model_params = {
                "num_parameters": getattr(config, "num_parameters", None),
                "hidden_size": getattr(config, "hidden_size", None),
                "num_layers": getattr(config, "num_hidden_layers", None),
                "vocab_size": getattr(config, "vocab_size", None),
                "model_architecture": config.architectures[0] if hasattr(config, "architectures") else None
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load HuggingFace model config: {str(e)}")
    
    metadata = ModelMetadata(
        model_id=model_id,
        name=request.name,
        version=request.version,
        team_id=request.team_id,
        huggingface_model_id=request.huggingface_model_id,
        description=request.description,
        tags=request.tags,
        parameters=model_params
    )
    
    models_db[model_id] = metadata
    return metadata

@app.get("/models", response_model=List[ModelMetadata])
async def list_models(
    team_id: Optional[str] = None,
    status: Optional[str] = None,
    tags: Optional[str] = None
):
    filtered_models = list(models_db.values())
    
    if team_id:
        filtered_models = [m for m in filtered_models if m.team_id == team_id]
    if status:
        filtered_models = [m for m in filtered_models if m.status == status]
    if tags:
        tag_list = tags.split(",")
        filtered_models = [m for m in filtered_models if any(tag in m.tags for tag in tag_list)]
    
    return filtered_models

@app.get("/models/{model_id}", response_model=ModelMetadata)
async def get_model(model_id: str):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    return models_db[model_id]

@app.put("/models/{model_id}", response_model=ModelMetadata)
async def update_model(model_id: str, request: ModelUpdateRequest):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = models_db[model_id]
    
    if request.name:
        model.name = request.name
    if request.description:
        model.description = request.description
    if request.tags:
        model.tags = request.tags
    if request.status:
        model.status = request.status
    
    model.updated_at = datetime.now()
    return model

@app.delete("/models/{model_id}")
async def delete_model(model_id: str):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    del models_db[model_id]
    return {"message": "Model deleted successfully"}

@app.post("/models/{model_id}/load")
async def load_model_for_inference(model_id: str):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_metadata = models_db[model_id]
    
    if not model_metadata.huggingface_model_id:
        raise HTTPException(status_code=400, detail="No HuggingFace model ID specified")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_metadata.huggingface_model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_metadata.huggingface_model_id,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        
        return {
            "model_id": model_id,
            "status": "loaded",
            "device": str(model.device),
            "message": "Model loaded successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

@app.post("/models/{model_id}/metrics")
async def update_model_metrics(model_id: str, metrics: Dict[str, float]):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = models_db[model_id]
    model.performance_metrics.update(metrics)
    model.updated_at = datetime.now()
    
    return {"message": "Metrics updated successfully", "metrics": model.performance_metrics}

@app.get("/models/{model_id}/metrics")
async def get_model_metrics(model_id: str):
    if model_id not in models_db:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return models_db[model_id].performance_metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
