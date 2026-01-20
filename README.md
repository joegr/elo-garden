# Large Language Model from Scratch

A complete implementation of a transformer-based language model built from scratch using Python and PyTorch.

## Features

- **Custom Transformer Architecture**: Multi-head attention, feedforward layers, positional encoding
- **BPE Tokenizer**: Byte-pair encoding tokenizer trained on your documents
- **Training Pipeline**: Complete training loop with validation, checkpointing, and TensorBoard logging
- **Text Generation**: Support for temperature, top-k, and top-p sampling
- **Configurable**: Easy-to-modify model and training configurations

## Architecture

- **Model**: Transformer decoder with causal masking
- **Attention**: Multi-head scaled dot-product attention
- **Layers**: 6 transformer blocks (configurable)
- **Hidden Size**: 512 dimensions (configurable)
- **Attention Heads**: 8 heads (configurable)
- **Feedforward**: 2048 dimensions (configurable)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Prepare Your Data

Create a `data/` directory and add your text documents:

```bash
mkdir data
# Add your .txt files to the data/ directory
```

### 2. Train the Model

```bash
python train.py
```

This will:
- Train a BPE tokenizer on your documents
- Create train/validation splits
- Train the transformer model
- Save checkpoints to `checkpoints/`
- Log metrics to `logs/` (view with TensorBoard)

### 3. Generate Text

**Single prompt:**
```bash
python generate.py --prompt "Once upon a time" --max_length 100
```

**Interactive mode:**
```bash
python generate.py --interactive
```

**Custom parameters:**
```bash
python generate.py \
    --prompt "The future of AI" \
    --max_length 200 \
    --temperature 0.8 \
    --top_k 50 \
    --top_p 0.9
```

## Configuration

### Model Configuration (`config.py`)

```python
ModelConfig(
    vocab_size=10000,      # Vocabulary size
    d_model=512,           # Model dimension
    n_heads=8,             # Number of attention heads
    n_layers=6,            # Number of transformer layers
    d_ff=2048,             # Feedforward dimension
    max_seq_len=512,       # Maximum sequence length
    dropout=0.1            # Dropout rate
)
```

### Training Configuration (`config.py`)

```python
TrainingConfig(
    batch_size=32,         # Batch size
    learning_rate=3e-4,    # Learning rate
    num_epochs=10,         # Number of epochs
    warmup_steps=4000,     # Warmup steps for learning rate
    gradient_clip=1.0,     # Gradient clipping threshold
    save_every=1000,       # Save checkpoint every N steps
    eval_every=500         # Evaluate every N steps
)
```

## Project Structure

```
mind/
├── config.py           # Model and training configurations
├── tokenizer.py        # BPE tokenizer implementation
├── model.py            # Transformer model architecture
├── dataset.py          # Data loading and preprocessing
├── train.py            # Training script
├── generate.py         # Text generation script
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── data/              # Training documents (create this)
├── checkpoints/       # Model checkpoints (auto-created)
└── logs/              # TensorBoard logs (auto-created)
```

## Monitoring Training

View training metrics with TensorBoard:

```bash
tensorboard --logdir logs/
```

Then open http://localhost:6006 in your browser.

## Advanced Usage

### Custom Tokenizer Training

```python
from tokenizer import BPETokenizer

tokenizer = BPETokenizer(vocab_size=10000)
tokenizer.train(texts)
tokenizer.save('custom_tokenizer.pkl')
```

### Load and Use Trained Model

```python
import torch
from model import TransformerLM
from tokenizer import BPETokenizer

# Load tokenizer
tokenizer = BPETokenizer()
tokenizer.load('tokenizer.pkl')

# Load model
checkpoint = torch.load('checkpoints/best_model.pt')
model = TransformerLM(checkpoint['config'])
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# Generate
prompt = "Your prompt here"
input_ids = tokenizer.encode(prompt)
input_tensor = torch.tensor([input_ids])
output = model.generate(input_tensor, max_length=100)
text = tokenizer.decode(output[0].tolist())
print(text)
```

## Technical Details

### Tokenization
- Uses Byte-Pair Encoding (BPE) algorithm
- Trained on your custom documents
- Special tokens: `<PAD>`, `<UNK>`, `<BOS>`, `<EOS>`

### Model Architecture
- Transformer decoder with causal (autoregressive) masking
- Sinusoidal positional encodings
- Layer normalization and residual connections
- Xavier uniform weight initialization

### Training
- AdamW optimizer with learning rate warmup
- Cross-entropy loss with label smoothing capability
- Gradient clipping for stability
- Automatic checkpointing and validation

### Generation
- Temperature-based sampling
- Top-k filtering
- Top-p (nucleus) sampling
- Automatic stopping at `<EOS>` token

## Performance Tips

1. **GPU Training**: The model automatically uses CUDA if available
2. **Batch Size**: Adjust based on your GPU memory
3. **Sequence Length**: Shorter sequences train faster
4. **Model Size**: Reduce `d_model`, `n_layers`, or `d_ff` for faster training

## Requirements

- Python 3.8+
- PyTorch 2.1.0+
- NumPy
- tqdm
- spaCy (optional, for advanced preprocessing)
- TensorBoard (for monitoring)

## License

MIT License - feel free to use and modify as needed.

## Contributing

This is a educational implementation. Feel free to extend it with:
- Different attention mechanisms
- More sophisticated tokenization
- Pre-training objectives (MLM, NSP, etc.)
- Fine-tuning capabilities
- Model quantization
- Distributed training
