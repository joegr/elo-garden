import torch
from torch.utils.data import Dataset, DataLoader
import os
from typing import List
import glob


class TextDataset(Dataset):
    def __init__(self, file_paths: List[str], tokenizer, max_seq_len=512):
        self.tokenizer = tokenizer
        self.max_seq_len = max_seq_len
        self.examples = []
        
        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                self._process_text(text)
    
    def _process_text(self, text: str):
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        
        for i in range(0, len(tokens) - self.max_seq_len, self.max_seq_len // 2):
            chunk = tokens[i:i + self.max_seq_len]
            if len(chunk) == self.max_seq_len:
                self.examples.append(chunk)
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        tokens = self.examples[idx]
        input_ids = torch.tensor(tokens[:-1], dtype=torch.long)
        target_ids = torch.tensor(tokens[1:], dtype=torch.long)
        return input_ids, target_ids


def collate_fn(batch):
    input_ids = torch.stack([item[0] for item in batch])
    target_ids = torch.stack([item[1] for item in batch])
    return input_ids, target_ids


def create_dataloaders(data_dir: str, tokenizer, batch_size=32, max_seq_len=512, train_split=0.9):
    file_paths = []
    
    for ext in ['*.txt', '*.md', '*.text']:
        file_paths.extend(glob.glob(os.path.join(data_dir, ext)))
        file_paths.extend(glob.glob(os.path.join(data_dir, '**', ext), recursive=True))
    
    if not file_paths:
        raise ValueError(f"No text files found in {data_dir}")
    
    split_idx = int(len(file_paths) * train_split)
    train_files = file_paths[:split_idx] if split_idx > 0 else file_paths
    val_files = file_paths[split_idx:] if split_idx < len(file_paths) else file_paths[:1]
    
    train_dataset = TextDataset(train_files, tokenizer, max_seq_len)
    val_dataset = TextDataset(val_files, tokenizer, max_seq_len)
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0
    )
    
    return train_loader, val_loader
