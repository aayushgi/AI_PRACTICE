import re
from preprocessing_rag import get_all_text
from db_rag import emb_model, add_chunks

def split_into_sentences(text):
    """
    Text ko sentences mein split karo (.) ke basis pe.
    Handles abbreviations like Dr., Mr., etc. carefully.
    """
    # Simple sentence split - splits on period followed by space and capital letter
    # Or period at end of text
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def create_chunks(text, min_tokens=192, max_tokens=240, overlap_tokens=32):
    """
    Smart chunking with overlap
    """
    sentences = split_into_sentences(text)
    print(f"Total sentences found: {len(sentences)}")
    
    chunks = []
    current_chunk_sentences = []
    current_tokens = []
    overlap_text = ""  # Previous chunk ke last 32 tokens ka text
    
    for sentence in sentences:
        # Tokenize current sentence
        sentence_tokens = emb_model.tokenize(sentence).squeeze().tolist()
        
        # Handle case where tokenize returns single int
        if isinstance(sentence_tokens, int):
            sentence_tokens = [sentence_tokens]
        
        # Check if adding this sentence would exceed max_tokens
        if len(current_tokens) + len(sentence_tokens) > max_tokens:
            # Current chunk is already at good size (192-240)?
            if len(current_tokens) >= min_tokens:
                # Save current chunk - ends at complete sentence
                chunk_text = ' '.join(current_chunk_sentences)
                
                # Add overlap from previous chunk at the start
                if overlap_text:
                    chunk_text = overlap_text + " " + chunk_text
                
                chunks.append(chunk_text)
                
                # Get last 32 tokens for next chunk's overlap
                if len(current_tokens) >= overlap_tokens:
                    overlap_tokens_list = current_tokens[-overlap_tokens:]
                    overlap_text = emb_model.tokenizer.decode(overlap_tokens_list, skip_special_tokens=True)
                else:
                    overlap_text = ' '.join(current_chunk_sentences)
                
                current_chunk_sentences = []
                current_tokens = []
            else:
                # Not enough tokens yet, but adding more would exceed max
                # Force cut at max_tokens
                combined_tokens = current_tokens + sentence_tokens
                
                # Take only up to max_tokens
                truncated_tokens = combined_tokens[:max_tokens]
                chunk_text = emb_model.tokenizer.decode(truncated_tokens, skip_special_tokens=True)
                
                # Add overlap from previous chunk at the start
                if overlap_text:
                    chunk_text = overlap_text + " " + chunk_text
                
                chunks.append(chunk_text)
                
                # Get last 32 tokens for next chunk's overlap
                overlap_tokens_list = truncated_tokens[-overlap_tokens:]
                overlap_text = emb_model.tokenizer.decode(overlap_tokens_list, skip_special_tokens=True)
                
                # Remaining tokens start new chunk
                remaining_tokens = combined_tokens[max_tokens:]
                if remaining_tokens:
                    remaining_text = emb_model.tokenizer.decode(remaining_tokens, skip_special_tokens=True)
                    current_chunk_sentences = [remaining_text]
                    current_tokens = remaining_tokens
                else:
                    current_chunk_sentences = []
                    current_tokens = []
                continue
        
        # Add sentence to current chunk
        current_chunk_sentences.append(sentence)
        current_tokens.extend(sentence_tokens)
        
        # Check if we're in the sweet spot (192-240 tokens) and sentence just ended
        if min_tokens <= len(current_tokens) <= max_tokens:
            chunk_text = ' '.join(current_chunk_sentences)
            
            # Add overlap from previous chunk at the start
            if overlap_text:
                chunk_text = overlap_text + " " + chunk_text
            
            chunks.append(chunk_text)
            
            # Get last 32 tokens for next chunk's overlap
            if len(current_tokens) >= overlap_tokens:
                overlap_tokens_list = current_tokens[-overlap_tokens:]
                overlap_text = emb_model.tokenizer.decode(overlap_tokens_list, skip_special_tokens=True)
            else:
                overlap_text = ' '.join(current_chunk_sentences)
            
            current_chunk_sentences = []
            current_tokens = []
    
    # Don't forget remaining content
    if current_chunk_sentences:
        chunk_text = ' '.join(current_chunk_sentences)
        if overlap_text:
            chunk_text = overlap_text + " " + chunk_text
        chunks.append(chunk_text)
    
    return chunks

def populate_database():
    print("Extracting text from PDFs...")
    text = get_all_text()
    print(f"Extracted {len(text)} characters of text")
    
    print("Creating chunks...")
    chunks = create_chunks(text, min_tokens=192, max_tokens=240)
    print(f"Created {len(chunks)} chunks")
    
    # Add chunks to database in batches
    batch_size = 4
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        add_chunks(batch, batch_size=len(batch))
        print(f"Added batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
    
    print("Database population complete!")

if __name__ == "__main__":
    populate_database()
