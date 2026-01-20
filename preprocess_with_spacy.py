import spacy
from spacy.tokens import Doc
import os
import glob
from tqdm import tqdm


def preprocess_documents_with_spacy(input_dir, output_dir, model_name='en_core_web_sm'):
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model {model_name} not found. Downloading...")
        os.system(f"python -m spacy download {model_name}")
        nlp = spacy.load(model_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    file_paths = []
    for ext in ['*.txt', '*.md']:
        file_paths.extend(glob.glob(os.path.join(input_dir, ext)))
        file_paths.extend(glob.glob(os.path.join(input_dir, '**', ext), recursive=True))
    
    if not file_paths:
        print(f"No text files found in {input_dir}")
        return
    
    print(f"Found {len(file_paths)} files to process")
    
    for file_path in tqdm(file_paths, desc="Processing documents"):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        doc = nlp(text)
        
        sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        processed_text = '\n'.join(sentences)
        
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(processed_text)
    
    print(f"Processed {len(file_paths)} files. Output saved to {output_dir}")


def extract_entities_and_save(input_dir, output_file, model_name='en_core_web_sm'):
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model {model_name} not found. Downloading...")
        os.system(f"python -m spacy download {model_name}")
        nlp = spacy.load(model_name)
    
    file_paths = glob.glob(os.path.join(input_dir, '*.txt'))
    
    all_entities = []
    
    for file_path in tqdm(file_paths, desc="Extracting entities"):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        doc = nlp(text)
        
        for ent in doc.ents:
            all_entities.append(f"{ent.text}\t{ent.label_}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_entities))
    
    print(f"Extracted {len(all_entities)} entities. Saved to {output_file}")


def clean_and_normalize_text(input_dir, output_dir, model_name='en_core_web_sm'):
    try:
        nlp = spacy.load(model_name)
    except OSError:
        print(f"Model {model_name} not found. Downloading...")
        os.system(f"python -m spacy download {model_name}")
        nlp = spacy.load(model_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    file_paths = glob.glob(os.path.join(input_dir, '*.txt'))
    
    for file_path in tqdm(file_paths, desc="Cleaning text"):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        doc = nlp(text)
        
        tokens = []
        for token in doc:
            if not token.is_space and not token.is_punct:
                tokens.append(token.text.lower())
        
        cleaned_text = ' '.join(tokens)
        
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
    
    print(f"Cleaned {len(file_paths)} files. Output saved to {output_dir}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess documents with spaCy')
    parser.add_argument('--input_dir', type=str, default='raw_data',
                        help='Directory containing raw text files')
    parser.add_argument('--output_dir', type=str, default='data',
                        help='Directory to save processed files')
    parser.add_argument('--mode', type=str, default='sentence',
                        choices=['sentence', 'entities', 'clean'],
                        help='Processing mode: sentence splitting, entity extraction, or cleaning')
    parser.add_argument('--model', type=str, default='en_core_web_sm',
                        help='spaCy model to use')
    
    args = parser.parse_args()
    
    if args.mode == 'sentence':
        preprocess_documents_with_spacy(args.input_dir, args.output_dir, args.model)
    elif args.mode == 'entities':
        extract_entities_and_save(args.input_dir, 'entities.txt', args.model)
    elif args.mode == 'clean':
        clean_and_normalize_text(args.input_dir, args.output_dir, args.model)
