from __future__ import annotations

from pathlib import Path

from io import BytesIO
from PIL import Image
from sqlalchemy import create_engine, Column, Integer, String, Text, LargeBinary
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_PATH = Path('images.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False, future=True, connect_args={"check_same_thread": False})

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class ImageRecord(Base):
    __tablename__ = 'Image'

    id = Column(Integer, nullable=False, autoincrement=True, primary_key=True)
    image_name = Column(String(255), nullable=False)

    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)

    caption = Column(Text, nullable=False)

    image_bytes = Column(LargeBinary, nullable=False)

    embedding = Column(LargeBinary, nullable=False)
    embedding_dim = Column(Integer, nullable=False)

def init_db():
    Base.metadata.create_all(engine)

def insert_image(session, image_bytes, image_name, width, height, caption, embedding, embedding_dim):
    row = ImageRecord(
        image_name=image_name,
        width=width,
        height=height,
        caption=caption,
        image_bytes=image_bytes,
        embedding=embedding,
        embedding_dim=embedding_dim
    )

    session.add(row)
    try:
        session.commit()
    except:
        session.rollback()
        raise ValueError(f"image_name '{image_name}' already exists")
    
    session.refresh(row)
    return row

def compress_image_bytes(
    img_bytes: bytes,
    max_side: int = 1024,
    fmt: str = "WEBP",
    quality: int = 80,
) -> tuple[bytes, int, int]:
    """
    Take raw image bytes -> compress -> return (compressed_bytes, width, height)
    """
    img = Image.open(BytesIO(img_bytes))

    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = BytesIO()
    save_kwargs = {"quality": quality}
    if fmt.upper() in {"JPEG", "JPG"}:
        save_kwargs.update({"optimize": True, "progressive": True})
    elif fmt.upper() == "WEBP":
        save_kwargs.update({"method": 6})

    img.save(buf, format=fmt.upper(), **save_kwargs)
    data = buf.getvalue()
    buf.close()

    return data, img.width, img.height