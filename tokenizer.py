import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple
import pickle


class BPETokenizer:
    def __init__(self, vocab_size=10000):
        self.vocab_size = vocab_size
        self.vocab = {}
        self.merges = []
        self.special_tokens = {
            '<PAD>': 0,
            '<UNK>': 1,
            '<BOS>': 2,
            '<EOS>': 3,
        }
        self.token_to_id = self.special_tokens.copy()
        self.id_to_token = {v: k for k, v in self.special_tokens.items()}
        
    def get_stats(self, word_freqs: Dict[Tuple[str, ...], int]) -> Counter:
        pairs = Counter()
        for word, freq in word_freqs.items():
            for i in range(len(word) - 1):
                pairs[(word[i], word[i + 1])] += freq
        return pairs
    
    def merge_vocab(self, pair: Tuple[str, str], word_freqs: Dict[Tuple[str, ...], int]) -> Dict[Tuple[str, ...], int]:
        new_word_freqs = {}
        bigram = ' '.join(pair)
        replacement = ''.join(pair)
        
        for word, freq in word_freqs.items():
            new_word = []
            i = 0
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                    new_word.append(replacement)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_word_freqs[tuple(new_word)] = freq
        
        return new_word_freqs
    
    def train(self, texts: List[str]):
        word_freqs = Counter()
        for text in texts:
            words = text.lower().split()
            for word in words:
                word_freqs[tuple(word + '</w>')] += 1
        
        current_vocab_size = len(self.special_tokens)
        
        for char_tuple in word_freqs.keys():
            for char in char_tuple:
                if char not in self.token_to_id:
                    self.token_to_id[char] = current_vocab_size
                    self.id_to_token[current_vocab_size] = char
                    current_vocab_size += 1
        
        while current_vocab_size < self.vocab_size:
            pairs = self.get_stats(word_freqs)
            if not pairs:
                break
            
            best_pair = max(pairs, key=pairs.get)
            word_freqs = self.merge_vocab(best_pair, word_freqs)
            self.merges.append(best_pair)
            
            merged_token = ''.join(best_pair)
            if merged_token not in self.token_to_id:
                self.token_to_id[merged_token] = current_vocab_size
                self.id_to_token[current_vocab_size] = merged_token
                current_vocab_size += 1
    
    def tokenize_word(self, word: str) -> List[str]:
        word = word + '</w>'
        word = tuple(word)
        
        for pair in self.merges:
            i = 0
            new_word = []
            while i < len(word):
                if i < len(word) - 1 and word[i] == pair[0] and word[i + 1] == pair[1]:
                    new_word.append(''.join(pair))
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            word = tuple(new_word)
        
        return list(word)
    
    def encode(self, text: str, add_special_tokens=True) -> List[int]:
        words = text.lower().split()
        tokens = []
        
        if add_special_tokens:
            tokens.append(self.token_to_id['<BOS>'])
        
        for word in words:
            word_tokens = self.tokenize_word(word)
            for token in word_tokens:
                tokens.append(self.token_to_id.get(token, self.token_to_id['<UNK>']))
        
        if add_special_tokens:
            tokens.append(self.token_to_id['<EOS>'])
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        tokens = [self.id_to_token.get(tid, '<UNK>') for tid in token_ids]
        tokens = [t for t in tokens if t not in ['<PAD>', '<BOS>', '<EOS>']]
        text = ''.join(tokens)
        text = text.replace('</w>', ' ')
        return text.strip()
    
    def save(self, filepath: str):
        with open(filepath, 'wb') as f:
            pickle.dump({
                'vocab_size': self.vocab_size,
                'token_to_id': self.token_to_id,
                'id_to_token': self.id_to_token,
                'merges': self.merges,
                'special_tokens': self.special_tokens
            }, f)
    
    def load(self, filepath: str):
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.vocab_size = data['vocab_size']
            self.token_to_id = data['token_to_id']
            self.id_to_token = data['id_to_token']
            self.merges = data['merges']
            self.special_tokens = data['special_tokens']
