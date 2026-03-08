import json
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

class AIJudgeDecision(BaseModel):
    match_index: int = Field(..., description="Eşleşen seçeneğin indeksi (0, 1 veya 2). Hiçbiri eşleşmiyorsa -1 dön.")
    confidence: float = Field(..., description="Bu seçeneğe olan tam güven yüzdeniz. (Örn: 98.5)")

def judge_match(pdf_item_text: str, candidates: list[str]) -> AIJudgeDecision:
    """
    Kritik Adım: Yapay Zeka Hakemi. Eşleşemeyen bir ürün ile FAISS üzerinden bulunan en yakın 3 adayı 
    gpt-4o-mini modeline sunar ve kesin karar ister.
    """
    candidates_text = "\n".join([f"{idx}- {cand}" for idx, cand in enumerate(candidates)])
    
    system_prompt = f"""Sen çok katı ve %100 doğrulukla çalışan bir stok kodu/ürün adı eşleştirme hakemisin.
PDF'ten (Katalogdan) gelen bir ürün ismi ile, veritabanımızdan bulduğumuz en olası 3 adayı karşılaştıracaksın.

PDF'ten gelen ürün: "{pdf_item_text}"

Veritabanındaki Adaylar:
{candidates_text}

Sence PDF'ten gelen ürün bu 3 adaydan hangisi ile aynıdır?
- Sadece anlamsal olarak gerçekten aynı ürün olduklarına inanıyorsan eşleştir.
- Kategori uyuşmazlıklarına karşı ACIMASIZ OL. Bir Çarşaf/Nevresim Seti (veya Yatak Örtüsü, Fitted Set vb.) ile Baza/Yatak Seti ASLA aynı şey değildir. Eğer ürünlerin ana kategorisi uyuşmuyorsa skoru direkt 0 ver ve KESİNLİKLE EŞLEŞTİRME (-1 dön).
- Farklı ebat, farklı paket veya farklı özellik varsa KESİNLİKLE EŞLEŞTİRME (-1 dön).
- SADECE JSON formatında şu yapıyı dön:
{{
  "match_index": 0, // 0, 1, 2 veya eşleşme yoksa -1
  "confidence": 99.5 // 0 ile 100 arasında güven skoru
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Kararını belirtilen JSON formatında ver."}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    content = response.choices[0].message.content
    try:
        decision = AIJudgeDecision.model_validate_json(content)
        return decision
    except ValidationError as e:
        print(f"AI Judge JSON Parse Hatası: {e}")
        # Hata durumunda eşleşmedi kabul et
        return AIJudgeDecision(match_index=-1, confidence=0.0)
