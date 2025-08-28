from sentence_transformers import SentenceTransformer
from PIL import Image
from io import BytesIO

model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_text(text):
    embedding = model.encode(text)
    return embedding

# print(type(embed_text('real')))
# print(embed_text('real'))