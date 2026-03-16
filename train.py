import torch
import torch.nn as nn
import torch.optim as optim
import os
from tqdm import tqdm
import math
import mlflow

from model import TransformerLM
from config import ModelConfig, TrainingConfig
from tokenizer import BPETokenizer
from dataset import create_dataloaders


class Trainer:
    def __init__(self, model, train_loader, val_loader, config, tokenizer, model_config=None):
        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config
        self.tokenizer = tokenizer
        self.model_config = model_config
        
        self.optimizer = optim.AdamW(
            model.parameters(),
            lr=config.learning_rate,
            betas=(0.9, 0.98),
            eps=1e-9
        )
        
        self.criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.token_to_id['<PAD>'])
        
        os.makedirs(config.checkpoint_dir, exist_ok=True)
        
        self.global_step = 0
        self.best_val_loss = float('inf')
        self.mlflow_run_id = None
    
    def get_lr(self, step):
        d_model = self.model.config.d_model
        step = max(step, 1)
        lr = (d_model ** -0.5) * min(step ** -0.5, step * (self.config.warmup_steps ** -1.5))
        return lr * self.config.learning_rate
    
    def train_epoch(self, epoch):
        self.model.train()
        total_loss = 0
        progress_bar = tqdm(self.train_loader, desc=f'Epoch {epoch}')
        
        for batch_idx, (input_ids, target_ids) in enumerate(progress_bar):
            input_ids = input_ids.to(self.model.config.device)
            target_ids = target_ids.to(self.model.config.device)
            
            lr = self.get_lr(self.global_step)
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = lr
            
            self.optimizer.zero_grad()
            
            logits = self.model(input_ids)
            loss = self.criterion(logits.view(-1, logits.size(-1)), target_ids.view(-1))
            
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.gradient_clip)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            self.global_step += 1
            
            progress_bar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'lr': f'{lr:.2e}',
                'ppl': f'{math.exp(loss.item()):.2f}'
            })
            
            if self.mlflow_run_id:
                mlflow.log_metrics({
                    'train_loss': loss.item(),
                    'learning_rate': lr,
                    'train_perplexity': math.exp(loss.item()),
                }, step=self.global_step)
            
            if self.global_step % self.config.eval_every == 0:
                val_loss = self.validate()
                self.model.train()
            
            if self.global_step % self.config.save_every == 0:
                self.save_checkpoint(f'checkpoint_step_{self.global_step}.pt')
        
        return total_loss / len(self.train_loader)
    
    def validate(self):
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for input_ids, target_ids in tqdm(self.val_loader, desc='Validation'):
                input_ids = input_ids.to(self.model.config.device)
                target_ids = target_ids.to(self.model.config.device)
                
                logits = self.model(input_ids)
                loss = self.criterion(logits.view(-1, logits.size(-1)), target_ids.view(-1))
                
                total_loss += loss.item()
        
        avg_loss = total_loss / len(self.val_loader)
        perplexity = math.exp(avg_loss)
        
        if self.mlflow_run_id:
            mlflow.log_metrics({
                'val_loss': avg_loss,
                'val_perplexity': perplexity,
            }, step=self.global_step)
        
        print(f'\nValidation Loss: {avg_loss:.4f}, Perplexity: {perplexity:.2f}')
        
        if avg_loss < self.best_val_loss:
            self.best_val_loss = avg_loss
            self.save_checkpoint('best_model.pt')
        
        return avg_loss
    
    def save_checkpoint(self, filename):
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'global_step': self.global_step,
            'best_val_loss': self.best_val_loss,
            'config': self.model.config
        }
        path = os.path.join(self.config.checkpoint_dir, filename)
        torch.save(checkpoint, path)
        print(f'Checkpoint saved to {path}')
    
    def load_checkpoint(self, filepath):
        checkpoint = torch.load(filepath, map_location=self.model.config.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.global_step = checkpoint['global_step']
        self.best_val_loss = checkpoint['best_val_loss']
        print(f'Checkpoint loaded from {filepath}')
    
    def train(self):
        total_params = sum(p.numel() for p in self.model.parameters())
        print(f'Training on device: {self.model.config.device}')
        print(f'Total parameters: {total_params:,}')
        
        mlflow.set_tracking_uri('./mlruns')
        mlflow.set_experiment('training')
        
        with mlflow.start_run(run_name=f'transformer_{self.model.config.d_model}d_{self.model.config.n_layers}L') as run:
            self.mlflow_run_id = run.info.run_id
            
            # Log all hyperparameters once at the start
            mlflow.log_params({
                'vocab_size': self.model.config.vocab_size,
                'd_model': self.model.config.d_model,
                'n_heads': self.model.config.n_heads,
                'n_layers': self.model.config.n_layers,
                'd_ff': self.model.config.d_ff,
                'max_seq_len': self.model.config.max_seq_len,
                'dropout': self.model.config.dropout,
                'batch_size': self.config.batch_size,
                'learning_rate': self.config.learning_rate,
                'num_epochs': self.config.num_epochs,
                'warmup_steps': self.config.warmup_steps,
                'gradient_clip': self.config.gradient_clip,
                'total_parameters': total_params,
            })
            
            for epoch in range(self.config.num_epochs):
                train_loss = self.train_epoch(epoch)
                val_loss = self.validate()
                
                mlflow.log_metrics({
                    'epoch_train_loss': train_loss,
                    'epoch_val_loss': val_loss,
                    'epoch_val_perplexity': math.exp(val_loss),
                }, step=epoch)
                
                print(f'Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}')
            
            # Log best checkpoint as artifact
            best_path = os.path.join(self.config.checkpoint_dir, 'best_model.pt')
            if os.path.exists(best_path):
                mlflow.log_artifact(best_path)
            
            mlflow.log_metric('best_val_loss', self.best_val_loss)
            mlflow.set_tag('model_type', 'TransformerLM')
        
        print(f'Training complete! MLflow run ID: {self.mlflow_run_id}')


def main():
    model_config = ModelConfig(
        vocab_size=10000,
        d_model=512,
        n_heads=8,
        n_layers=6,
        d_ff=2048,
        max_seq_len=512,
        dropout=0.1
    )
    
    training_config = TrainingConfig(
        batch_size=32,
        learning_rate=3e-4,
        num_epochs=10,
        warmup_steps=4000,
        gradient_clip=1.0,
        save_every=1000,
        eval_every=500
    )
    
    print("Training tokenizer...")
    tokenizer = BPETokenizer(vocab_size=model_config.vocab_size)
    
    data_dir = 'data'
    if not os.path.exists(data_dir):
        print(f"Creating {data_dir} directory. Please add your training documents there.")
        os.makedirs(data_dir)
        return
    
    import glob
    text_files = glob.glob(os.path.join(data_dir, '*.txt'))
    if not text_files:
        print(f"No .txt files found in {data_dir}. Please add training documents.")
        return
    
    all_texts = []
    for file_path in text_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_texts.append(f.read())
    
    tokenizer.train(all_texts)
    tokenizer.save('tokenizer.pkl')
    print(f"Tokenizer trained with vocabulary size: {len(tokenizer.token_to_id)}")
    
    print("Creating dataloaders...")
    train_loader, val_loader = create_dataloaders(
        data_dir,
        tokenizer,
        batch_size=training_config.batch_size,
        max_seq_len=model_config.max_seq_len
    )
    
    print(f"Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    
    print("Initializing model...")
    model = TransformerLM(model_config).to(model_config.device)
    
    trainer = Trainer(model, train_loader, val_loader, training_config, tokenizer, model_config)
    trainer.train()


if __name__ == '__main__':
    main()
