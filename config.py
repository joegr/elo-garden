import torch

class ModelConfig:
    def __init__(
        self,
        vocab_size=10000,
        d_model=512,
        n_heads=8,
        n_layers=6,
        d_ff=2048,
        max_seq_len=512,
        dropout=0.1,
        device=None
    ):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.d_ff = d_ff
        self.max_seq_len = max_seq_len
        self.dropout = dropout
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        assert d_model % n_heads == 0, "d_model must be divisible by n_heads"
        self.d_k = d_model // n_heads


class TrainingConfig:
    def __init__(
        self,
        batch_size=32,
        learning_rate=3e-4,
        num_epochs=10,
        warmup_steps=4000,
        gradient_clip=1.0,
        save_every=1000,
        eval_every=500,
        checkpoint_dir='checkpoints',
        log_dir='logs'
    ):
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        self.warmup_steps = warmup_steps
        self.gradient_clip = gradient_clip
        self.save_every = save_every
        self.eval_every = eval_every
        self.checkpoint_dir = checkpoint_dir
        self.log_dir = log_dir
