from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import insert_image, compress_image_bytes, init_db, SessionLocal, ImageRecord
import captioner, uvicorn, base64
import numpy as np
from embedder import embed_text


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5500", "*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get('/')
async def root():
    return {'message': 'API is running!'}

@app.on_event('startup')
def on_start_up():
    init_db()

@app.post('/caption-image')
async def caption_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        image_bytes = await file.read()
        caption = captioner.caption_image(image_bytes)
        embedding = embed_text(caption).tobytes()
        embedding_dim = embedding.size
        image_bytes, width, height = compress_image_bytes(image_bytes)
        
        insert_image(db, image_bytes, file.filename, width, height, caption, embedding, embedding_dim)
        return JSONResponse({'caption': caption})
    
    except Exception as e:
        raise HTTPException(400, f'Failed to process image: {e}')
    
@app.post('/search-by-image')
async def search_by_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        image_bytes = await file.read()
        caption = captioner.caption_image(image_bytes)
        embedding = embed_text(caption)
        data = db.query(ImageRecord.embedding, ImageRecord.caption, ImageRecord.image_bytes).all()

        index = None
        max_cos_sim = -1

        for i, row in enumerate(data):
            row_emb = np.frombuffer(row.embedding, dtype=np.float32)
            cos_sim = float(row_emb @ embedding)
            if cos_sim > max_cos_sim:
                max_cos_sim = cos_sim
                index = i

        # print(data[index].caption)
        image_bytes = base64.b64encode(data[index].image_bytes).decode("utf-8")
        
        return JSONResponse({'image_bytes': image_bytes, 'caption': data[index].caption})

    except Exception as e:
        raise HTTPException(400, f'Failed to process image: {e}')
    
@app.post('/search-by-description')
async def search_by_image(description: str = Body(..., embed=True), db: Session = Depends(get_db)):
    try:
        # print('========================')
        # print(description)
        # print(type(description))
        embedding = embed_text(description)
        data = db.query(ImageRecord.embedding, ImageRecord.caption, ImageRecord.image_bytes).all()

        index = None
        max_cos_sim = -1

        for i, row in enumerate(data):
            row_emb = np.frombuffer(row.embedding, dtype=np.float32)
            cos_sim = float(row_emb @ embedding)
            if cos_sim > max_cos_sim:
                max_cos_sim = cos_sim
                index = i

        # print(data[index].caption)
        image_bytes = base64.b64encode(data[index].image_bytes).decode("utf-8")

        return JSONResponse({'image_bytes': image_bytes, 'caption': data[index].caption})

    except Exception as e:
        raise HTTPException(400, f'Failed to process image: {e}')
    

if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )