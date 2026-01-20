import torch
import argparse

from model import TransformerLM
from tokenizer import BPETokenizer


def load_model(checkpoint_path, tokenizer):
    checkpoint = torch.load(checkpoint_path, map_location='cpu')
    config = checkpoint['config']
    
    model = TransformerLM(config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(config.device)
    model.eval()
    
    return model


def generate_text(model, tokenizer, prompt, max_length=100, temperature=1.0, top_k=50, top_p=0.9):
    input_ids = tokenizer.encode(prompt, add_special_tokens=True)
    input_tensor = torch.tensor([input_ids], dtype=torch.long).to(model.config.device)
    
    output_ids = model.generate(
        input_tensor,
        max_length=max_length,
        temperature=temperature,
        top_k=top_k,
        top_p=top_p
    )
    
    generated_text = tokenizer.decode(output_ids[0].tolist())
    return generated_text


def interactive_mode(model, tokenizer):
    print("\n=== Interactive Generation Mode ===")
    print("Type your prompt and press Enter. Type 'quit' to exit.\n")
    
    while True:
        prompt = input("Prompt: ")
        if prompt.lower() in ['quit', 'exit', 'q']:
            break
        
        if not prompt.strip():
            continue
        
        print("\nGenerating...")
        generated = generate_text(
            model,
            tokenizer,
            prompt,
            max_length=100,
            temperature=0.8,
            top_k=50,
            top_p=0.9
        )
        
        print(f"\nGenerated text:\n{generated}\n")
        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description='Generate text using trained LLM')
    parser.add_argument('--checkpoint', type=str, default='checkpoints/best_model.pt',
                        help='Path to model checkpoint')
    parser.add_argument('--tokenizer', type=str, default='tokenizer.pkl',
                        help='Path to tokenizer file')
    parser.add_argument('--prompt', type=str, default=None,
                        help='Text prompt for generation')
    parser.add_argument('--max_length', type=int, default=100,
                        help='Maximum length of generated text')
    parser.add_argument('--temperature', type=float, default=0.8,
                        help='Sampling temperature')
    parser.add_argument('--top_k', type=int, default=50,
                        help='Top-k sampling parameter')
    parser.add_argument('--top_p', type=float, default=0.9,
                        help='Top-p (nucleus) sampling parameter')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode')
    
    args = parser.parse_args()
    
    print("Loading tokenizer...")
    tokenizer = BPETokenizer()
    tokenizer.load(args.tokenizer)
    
    print("Loading model...")
    model = load_model(args.checkpoint, tokenizer)
    print(f"Model loaded on device: {model.config.device}")
    
    if args.interactive:
        interactive_mode(model, tokenizer)
    elif args.prompt:
        generated = generate_text(
            model,
            tokenizer,
            args.prompt,
            max_length=args.max_length,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p
        )
        print(f"\nPrompt: {args.prompt}")
        print(f"\nGenerated text:\n{generated}")
    else:
        print("Please provide --prompt or use --interactive mode")


if __name__ == '__main__':
    main()
