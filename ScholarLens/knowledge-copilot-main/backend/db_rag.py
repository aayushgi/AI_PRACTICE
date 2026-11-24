import torch
import psycopg2
import os
from uuid import uuid4
from dotenv import load_dotenv
from FlagEmbedding import BGEM3FlagModel
from transformers import AutoTokenizer

load_dotenv()

device = 'cuda' if torch.cuda.is_available() else 'cpu'

class EmbeddingModel():
  def __init__(self):
    self.model = BGEM3FlagModel('BAAI/bge-m3', devices=device, use_fp16=True)
    self.tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-m3")

  def encode(self, text, batch_size=4, max_length=5192):
    return self.model.encode(text, batch_size=batch_size, max_length=max_length)['dense_vecs'].tolist()

  def tokenize(self, text):
    return self.tokenizer.encode(text, return_tensors='pt').to(device)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("RAG_DB_NAME", "ragdb"),
        user=os.getenv("RAG_DB_USER", "postgres"),
        password=os.getenv("RAG_DB_PASSWORD"),
        host=os.getenv("RAG_DB_HOST", "localhost"),
        port=int(os.getenv("RAG_DB_PORT", 5432))
    )

emb_model = EmbeddingModel()

def add_chunks(chunks, batch_size=4, max_length=8192):
	conn = None
	try:
		conn = get_db_connection()
		all_chunk_emb = emb_model.encode(chunks, batch_size=batch_size)
		for chunk, chunk_emb in zip(chunks, all_chunk_emb):
			chunk_id = str(uuid4())
			with conn.cursor() as cursor:
				cursor.execute(
					"""
					INSERT INTO chunks (id, content, embedding)
					VALUES(%s, %s, %s)
					""",
					(chunk_id, chunk, chunk_emb)
			)
		conn.commit()
	except Exception as e:
		print(f"Error adding chunk to database: {e}")
	finally:
		if conn:
			conn.close()

def get_top_k_docs(query, k=7):
	conn=None
	try:
		conn = get_db_connection()
		query_emb = emb_model.encode(query)
		with conn.cursor() as cursor:
			cursor.execute("""
				SELECT content, embedding <=> %s::vector
				AS distance FROM chunks
				ORDER BY distance
				LIMIT %s
			""",
			(query_emb, k))
			result = cursor.fetchall()
			documents = []
			for i in range(len(result)):
				documents.append(result[i][0] + "\n")
			return "".join(documents)
	except Exception as e:
		print(f"Error fetching top k docs: {e}")
		return ""
	finally:
		if conn:
			conn.close()