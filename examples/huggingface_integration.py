"""
HuggingFace Integration Examples

Demonstrates how to use the HuggingFace client for:
- Model discovery and search
- Loading models from HuggingFace Hub
- Running inference
- Model comparison
"""

import sys
sys.path.append('/Users/jg/mind/services/model_registry')

from huggingface_client import HuggingFaceClient, ModelLoadConfig
import asyncio

def example_1_search_models():
    """Example 1: Search for models on HuggingFace Hub."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Search for Models")
    print("="*80)
    
    client = HuggingFaceClient()
    
    # Search for GPT models
    print("\nSearching for GPT models...")
    models = client.search_models(
        query="gpt",
        task="text-generation",
        limit=5
    )
    
    for model in models:
        print(f"\n  Model: {model['model_id']}")
        print(f"  Author: {model['author']}")
        print(f"  Downloads: {model['downloads']:,}")
        print(f"  Tags: {', '.join(model['tags'][:5])}")


def example_2_get_model_info():
    """Example 2: Get detailed information about a specific model."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Get Model Information")
    print("="*80)
    
    client = HuggingFaceClient()
    
    model_id = "gpt2"
    print(f"\nGetting info for: {model_id}")
    
    info = client.get_model_info(model_id)
    
    print(f"\n  Model ID: {info['model_id']}")
    print(f"  Author: {info['author']}")
    print(f"  Downloads: {info['downloads']:,}")
    print(f"  Likes: {info['likes']}")
    print(f"  Pipeline: {info['pipeline_tag']}")
    print(f"  Library: {info['library_name']}")
    print(f"  Tags: {', '.join(info['tags'][:10])}")


def example_3_get_model_config():
    """Example 3: Get model architecture configuration."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Get Model Configuration")
    print("="*80)
    
    client = HuggingFaceClient()
    
    model_id = "gpt2"
    print(f"\nGetting config for: {model_id}")
    
    config = client.get_model_config(model_id)
    
    print(f"\n  Architecture: {config['architectures']}")
    print(f"  Model Type: {config['model_type']}")
    print(f"  Hidden Size: {config['hidden_size']}")
    print(f"  Num Layers: {config['num_hidden_layers']}")
    print(f"  Attention Heads: {config['num_attention_heads']}")
    print(f"  Vocab Size: {config['vocab_size']:,}")
    print(f"  Max Position: {config['max_position_embeddings']}")


def example_4_load_and_generate():
    """Example 4: Load a model and generate text."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Load Model and Generate Text")
    print("="*80)
    
    client = HuggingFaceClient(cache_dir="/tmp/hf_cache")
    
    model_id = "gpt2"
    print(f"\nLoading model: {model_id}")
    
    # Configure model loading
    config = ModelLoadConfig(
        model_id=model_id,
        device="cpu",  # Use "auto" for GPU
        torch_dtype="float32",  # Use "float16" for GPU
        trust_remote_code=False
    )
    
    # Load model and tokenizer
    print("  Loading model...")
    model = client.load_model(config)
    print("  ✓ Model loaded")
    
    print("  Loading tokenizer...")
    tokenizer = client.load_tokenizer(model_id)
    print("  ✓ Tokenizer loaded")
    
    # Generate text
    prompts = [
        "The future of artificial intelligence is",
        "In a world where robots and humans coexist,",
        "The most important breakthrough in science will be"
    ]
    
    print("\nGenerating text for prompts...")
    for prompt in prompts:
        print(f"\n  Prompt: '{prompt}'")
        
        outputs = client.generate_text(
            model_id=model_id,
            prompt=prompt,
            max_length=50,
            temperature=0.8,
            top_k=50,
            top_p=0.9,
            num_return_sequences=1
        )
        
        print(f"  Generated: '{outputs[0]}'")
    
    # Clean up
    client.unload_model(model_id)
    print("\n  ✓ Model unloaded")


def example_5_compare_models():
    """Example 5: Compare multiple models side-by-side."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Compare Multiple Models")
    print("="*80)
    
    client = HuggingFaceClient()
    
    model_ids = ["gpt2", "distilgpt2", "gpt2-medium"]
    
    print("\nComparing models:")
    print(f"{'Model':<20} {'Layers':<10} {'Hidden':<10} {'Params (est.)':<15}")
    print("-" * 80)
    
    for model_id in model_ids:
        config = client.get_model_config(model_id)
        
        # Estimate parameters (rough calculation)
        hidden = config['hidden_size'] or 0
        layers = config['num_hidden_layers'] or 0
        vocab = config['vocab_size'] or 0
        
        # Very rough estimation
        params_est = (hidden * hidden * 12 * layers + vocab * hidden) / 1_000_000
        
        print(f"{model_id:<20} {layers:<10} {hidden:<10} {params_est:.1f}M")


def example_6_pipeline_usage():
    """Example 6: Use HuggingFace pipelines for inference."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Using HuggingFace Pipelines")
    print("="*80)
    
    client = HuggingFaceClient()
    
    model_id = "distilgpt2"
    print(f"\nLoading model: {model_id}")
    
    # Load model
    config = ModelLoadConfig(
        model_id=model_id,
        device="cpu",
        torch_dtype="float32"
    )
    
    model = client.load_model(config)
    tokenizer = client.load_tokenizer(model_id)
    
    # Create pipeline
    print("Creating text generation pipeline...")
    pipe = client.create_pipeline(model_id, task="text-generation")
    
    # Use pipeline
    prompt = "Once upon a time in a land far away,"
    print(f"\nPrompt: '{prompt}'")
    
    result = pipe(
        prompt,
        max_length=60,
        num_return_sequences=2,
        temperature=0.9
    )
    
    print("\nGenerated sequences:")
    for i, seq in enumerate(result, 1):
        print(f"\n  {i}. {seq['generated_text']}")
    
    # Clean up
    client.unload_model(model_id)


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("HUGGINGFACE INTEGRATION EXAMPLES")
    print("="*80)
    
    try:
        # Example 1: Search models
        example_1_search_models()
        
        # Example 2: Get model info
        example_2_get_model_info()
        
        # Example 3: Get model config
        example_3_get_model_config()
        
        # Example 4: Load and generate (commented out by default - requires download)
        # example_4_load_and_generate()
        
        # Example 5: Compare models
        example_5_compare_models()
        
        # Example 6: Pipeline usage (commented out by default - requires download)
        # example_6_pipeline_usage()
        
        print("\n" + "="*80)
        print("ALL EXAMPLES COMPLETED!")
        print("="*80)
        print("\nNote: Examples 4 and 6 are commented out by default")
        print("      Uncomment them to test model loading and generation")
        print("      (requires downloading models from HuggingFace Hub)")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
