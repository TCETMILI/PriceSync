import os
import json
import numpy as np
import faiss
from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072 # text-embedding-3-large için varsayılan boyut

def get_embedding(text: str) -> list[float]:
    """Tek bir metni OpenAI üzerinden vektöre çevirir."""
    response = client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
    return response.data[0].embedding

def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Metin listesini batch halinde OpenAI üzerinden vektöre çevirir."""
    # OpenAI tek seferde geniş array'leri alabilir (ancak limitlere dikkat)
    # Şimdilik 1000'erli gruplarla (batch) gönderelim ki hata vermesin
    all_embeddings = []
    chunk_size = 500
    for i in range(0, len(texts), chunk_size):
        chunk = texts[i:i + chunk_size]
        response = client.embeddings.create(input=chunk, model=EMBEDDING_MODEL)
        chunk_embeddings = [data.embedding for data in response.data]
        all_embeddings.extend(chunk_embeddings)
    return all_embeddings

class VectorDatabase:
    def __init__(self, cache_path: str = "/app/data/embeddings_cache.json"):
        self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
        self.texts = []   # id'si, metne denk gelen
        self.items = []   # Asıl obje bilgisi (excel record)
        self.cache_path = cache_path
        
    def _save_cache(self, embeddings: np.ndarray):
        with open(self.cache_path, "w", encoding="utf-8") as f:
            data_to_save = {
                "texts": self.texts,
                "items": self.items,
                "embeddings": embeddings.tolist()
            }
            json.dump(data_to_save, f, ensure_ascii=False)

    def _load_cache(self) -> np.ndarray:
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.texts = data["texts"]
                self.items = data["items"]
                return np.array(data["embeddings"], dtype=np.float32)
        return None

    def initialize(self, text_item_pairs: list):
        """
        [(text, item_data), (text, item_data)...] şeklinde liste alır.
        Performans için önce CACHE'den kontrol eder, yoksa OpenAI api call yapar.
        """
        # CACHE İPTALİ: Uygulamanın yeni sözlük ve algoritmalarına uyum sağlaması için
        # eski cache her zaman bypass edilecek ve Excel verisi sıfırdan embed edilecektir.
        cached_embeddings = None # self._load_cache() devredışı bırakıldı
        
        input_texts = [pair[0] for pair in text_item_pairs]
        input_items = [pair[1] for pair in text_item_pairs]
        
        # Eğer cache'deki metinler güncel gelen verilerle uyuşuyorsa doğrudan kullan
        # if cached_embeddings is not None and len(self.texts) == len(input_texts) and self.texts == input_texts:
        #     print("🚀 [FAISS] Embeddings önbellekten (cache) yüklendi!")
        #     self.index.add(cached_embeddings)
        #     return

        print("⏳ [FAISS] Yeni veriler için OpenAI üzerinden embedding oluşturuluyor... Lütfen bekleyin.")
        self.texts = input_texts
        self.items = input_items
        
        # API'den embedding al
        raw_embeddings = get_embeddings_batch(self.texts)
        np_embeddings = np.array(raw_embeddings, dtype=np.float32)
        
        print(f"Debug: texts len={len(self.texts)}, raw_embeddings len={len(raw_embeddings)}, np_embeddings.shape={np_embeddings.shape}")
        
        if len(np_embeddings.shape) == 1:
            print("Hata: np_embeddings 1 boyutlu (1D) olarak geldi. FAISS 2D bekliyor.")
            if len(np_embeddings) == 0:
                print("Sebebi: Embedding listesi boş!")
            raise ValueError("Embedding array shape is 1D")
            
        # FAISS index'e ekle
        self.index.add(np_embeddings)
        
        # Cache'e kaydet
        self._save_cache(np_embeddings)
        print("✅ [FAISS] Embeddingler başarıyla indekslendi ve cache'e kaydedildi.")

    def search(self, target_text: str, top_k: int = 3) -> list:
        """Hedef metne en çok benzeyen Top-K adayı döndürür."""
        if self.index.ntotal == 0:
            return []
            
        target_emb = np.array([get_embedding(target_text)], dtype=np.float32)
        distances, indices = self.index.search(target_emb, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # -1 found in faiss if nothing found
                results.append({
                    "text": self.texts[idx],
                    "item": self.items[idx],
                    "distance": float(distances[0][i])
                })
        return results
