from typing import Dict, Any, Optional, List
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    AutoConfig,
    pipeline
)
from huggingface_hub import HfApi, list_models, model_info
import torch
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelLoadConfig:
    model_id: str
    device: str = "auto"
    torch_dtype: str = "float16"
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    trust_remote_code: bool = False
    use_auth_token: Optional[str] = None

class HuggingFaceClient:
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir
        self.hf_api = HfApi()
        self.loaded_models: Dict[str, Any] = {}
        self.loaded_tokenizers: Dict[str, Any] = {}
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        try:
            info = model_info(model_id)
            
            return {
                "model_id": model_id,
                "author": info.author,
                "downloads": info.downloads,
                "likes": info.likes,
                "tags": info.tags,
                "pipeline_tag": info.pipeline_tag,
                "library_name": info.library_name,
                "created_at": info.created_at.isoformat() if info.created_at else None,
                "last_modified": info.last_modified.isoformat() if info.last_modified else None
            }
        except Exception as e:
            logger.error(f"Failed to get model info for {model_id}: {str(e)}")
            raise
    
    def search_models(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        library: str = "transformers",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        try:
            models = list_models(
                search=query,
                task=task,
                library=library,
                limit=limit
            )
            
            return [
                {
                    "model_id": model.modelId,
                    "author": getattr(model, 'author', None),
                    "downloads": getattr(model, 'downloads', 0),
                    "tags": getattr(model, 'tags', [])
                }
                for model in models
            ]
        except Exception as e:
            logger.error(f"Failed to search models: {str(e)}")
            return []
    
    def load_model(self, config: ModelLoadConfig):
        if config.model_id in self.loaded_models:
            logger.info(f"Model {config.model_id} already loaded")
            return self.loaded_models[config.model_id]
        
        try:
            dtype_map = {
                "float16": torch.float16,
                "float32": torch.float32,
                "bfloat16": torch.bfloat16
            }
            torch_dtype = dtype_map.get(config.torch_dtype, torch.float16)
            
            load_kwargs = {
                "pretrained_model_name_or_path": config.model_id,
                "torch_dtype": torch_dtype,
                "device_map": config.device,
                "trust_remote_code": config.trust_remote_code,
                "cache_dir": self.cache_dir
            }
            
            if config.use_auth_token:
                load_kwargs["use_auth_token"] = config.use_auth_token
            
            if config.load_in_8bit:
                load_kwargs["load_in_8bit"] = True
            elif config.load_in_4bit:
                load_kwargs["load_in_4bit"] = True
            
            model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
            self.loaded_models[config.model_id] = model
            
            logger.info(f"Successfully loaded model {config.model_id}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model {config.model_id}: {str(e)}")
            raise
    
    def load_tokenizer(self, model_id: str, use_auth_token: Optional[str] = None):
        if model_id in self.loaded_tokenizers:
            return self.loaded_tokenizers[model_id]
        
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                use_auth_token=use_auth_token,
                cache_dir=self.cache_dir
            )
            self.loaded_tokenizers[model_id] = tokenizer
            
            logger.info(f"Successfully loaded tokenizer for {model_id}")
            return tokenizer
            
        except Exception as e:
            logger.error(f"Failed to load tokenizer for {model_id}: {str(e)}")
            raise
    
    def generate_text(
        self,
        model_id: str,
        prompt: str,
        max_length: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.9,
        num_return_sequences: int = 1
    ) -> List[str]:
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        if model_id not in self.loaded_tokenizers:
            raise ValueError(f"Tokenizer for {model_id} not loaded")
        
        model = self.loaded_models[model_id]
        tokenizer = self.loaded_tokenizers[model_id]
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                num_return_sequences=num_return_sequences,
                do_sample=True
            )
        
        generated_texts = [
            tokenizer.decode(output, skip_special_tokens=True)
            for output in outputs
        ]
        
        return generated_texts
    
    def create_pipeline(self, model_id: str, task: str = "text-generation"):
        if model_id not in self.loaded_models:
            raise ValueError(f"Model {model_id} not loaded")
        
        model = self.loaded_models[model_id]
        tokenizer = self.loaded_tokenizers.get(model_id)
        
        pipe = pipeline(
            task,
            model=model,
            tokenizer=tokenizer,
            device=model.device
        )
        
        return pipe
    
    def unload_model(self, model_id: str):
        if model_id in self.loaded_models:
            del self.loaded_models[model_id]
            logger.info(f"Unloaded model {model_id}")
        
        if model_id in self.loaded_tokenizers:
            del self.loaded_tokenizers[model_id]
            logger.info(f"Unloaded tokenizer for {model_id}")
        
        torch.cuda.empty_cache()
    
    def get_model_config(self, model_id: str) -> Dict[str, Any]:
        try:
            config = AutoConfig.from_pretrained(model_id, cache_dir=self.cache_dir)
            
            return {
                "architectures": getattr(config, "architectures", []),
                "hidden_size": getattr(config, "hidden_size", None),
                "num_hidden_layers": getattr(config, "num_hidden_layers", None),
                "num_attention_heads": getattr(config, "num_attention_heads", None),
                "vocab_size": getattr(config, "vocab_size", None),
                "max_position_embeddings": getattr(config, "max_position_embeddings", None),
                "model_type": getattr(config, "model_type", None)
            }
        except Exception as e:
            logger.error(f"Failed to get config for {model_id}: {str(e)}")
            raise
