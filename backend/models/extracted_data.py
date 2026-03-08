from pydantic import BaseModel, Field
from typing import List, Optional

class ProductItem(BaseModel):
    brand: Optional[str] = Field(None, description="Marka bilgisinin adı, örn: YİTAŞ, BOSCH vb. Yoksa null veya boş bırakılabilir.")
    model: Optional[str] = Field(None, description="Model adı veya kodu")
    product_type: Optional[str] = Field(None, description="Cinsi veya tipi, örn: Pürmüz, Vida, Matkap")
    size_or_spec: Optional[str] = Field(None, description="Ebat, ölçü veya spesifikasyon, örn: 1/2, 5x50")
    price: float = Field(..., description="Ürünün fiyatı (Sadece sayısal değer, virgül de olsa ondalık formatı yani float olmalı).")
    currency: Optional[str] = Field("TL", description="Para birimi, örn: TL, USD, EUR")

class ExtractedPageData(BaseModel):
    page_number: int
    items: List[ProductItem] = Field(..., description="Sayfada bulunan ürünlerin listesi")
