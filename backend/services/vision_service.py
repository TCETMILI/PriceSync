import os
import base64
import json
from openai import OpenAI
from pydantic import ValidationError

from core.config import settings
from models.extracted_data import ExtractedPageData

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_data_from_image(image_path: str, page_number: int) -> ExtractedPageData:
    """
    Sends the PNG image to GPT-4o and strictly expects JSON matching ExtractedPageData schema.
    This version uses ULTRA-STRICT GRID REASONING / MATRIX INTERSECTION logic to extract every single price dynamically without hallucinating new items.
    """
    base64_image = encode_image(image_path)
    
    system_prompt = f'''Sen bir Katalog Veri Çıkarım Uzmanısın ve kusursuz bir "Matris (Tablo) Zekasına" sahipsin. Görevin, sağlanan katalog veya fiyat listesindeki ürünleri okuyup SADECE JSON formatında dönmektir.

ÇOK KATI MATRİS (KESİŞİM) VE HİZALAMA KURALLARI:

1. TABLOYU KAVRAMA VE ŞAŞILIK ENGELİ: 
   Görseldeki listeler birer FİYAT MATRİSİDİR (Tablo). Gördüğün her bir fiyat (örn: 20.920,00 ₺) bir satır ile bir sütunun KESİŞİMİNDEDİR.
   Gözlerini satır çizgilerinden ASLA ayırma! Kaydırma (şaşılık) yapman YASAKTIR. Fiyatı gördüğünde:
   - TAM SOLUNDAKİ hizadaki Model/Cins satırına bak ve onu seç. 
   - TAM ÜSTÜNDEKİ hizadaki Ebat sütununa bak ve onu seç.

2. DİNAMİK SINIR VE GERÇEKÇİ KAPSAMA:
   Sayfada kaç tane fiyat etiketi (₺ veya rakam) varsa, dinamik olarak sayısını kendin bul ve HİÇBİRİNİ ATLAMADAN hepsini çıkar. İster 10 tane olsun ister 300 tane, sadece gördüğün GERÇEK fiyatları çıkar. Olmayan bir ürünü uydurmak KESİNLİKLE YASAK! Sadece ve sadece sayfada gerçekten gördüğün fiyat etiketlerinin kesişimlerini listele.

3. İLAVE ÜRÜNLER İSTİSNASI: SADECE en sağdaki "İLAVE ÜRÜNLER" (Komidin, Markiz, Kasa vb.) listesinin ebat sütunu YOKTUR. SADECE onlar için ebat (size_or_spec) kısmına "Standart" yaz.

4. TEMBELLİK YASAK (PARÇALI JSON FORMATI):
   Verileri bulduğunda tek bir string cümle olarak tıkıştırmak YASAKTIR. 
   Sayfada ne görüyorsan, tam ve akıcı bir Türkçe ile birleştir ("mi moza" yerine "mimoza" yaz).
   Verileri titizlikle şu alanlara PARÇALAYARAK yerleştirmelisin:
   - brand: "YİTAŞ" (Eğer marka belli değilse standart marka neyse o veya boş)
   - model: "MİMOZA" (Sadece model adı, ekler kelimeleri birleştir)
   - product_type: "BAZA" (Veya SET / KOMİDİN vb.)
   - size_or_spec: "150x200" (SADECE İlave Ürünler gibi ebadı olmayanlarda "Standart" yazılacak, SET'lerde dahil diğer hepsinde yukarıdaki tablodan boyut okunacak)

5. UZUN LİSTE VE TOKEN KESİNTİSİ UYARISI (HAYATİ ÖNEMDE): Sayfada 150'den fazla fiyat etiketi olabilir. Bu, çıktının çok uzun olacağı anlamına gelir. Asla ve ASLA tembellik yapıp 'benzerleri atla' veya 'kısalt' mantığına girme. Çıktıyı yarıda kesme. Tüm satırları SONUNA KADAR (gerekirse 15.000 token sürse bile) tek tek yaz. Atladığın her bir ürün KRİTİK SİSTEM HATASI kabul edilecektir!

6. HARİÇ TUTULACAK ÜRÜNLER (KARA LİSTE - KESİN EMİR): Katalogda "SET" veya "TAKIM" isminde satırlar göreceksin. Bu satırları ve onlara ait hiçbir fiyatı KESİNLİKLE ÇIKARMA! Sayfada "SET" veya "TAKIM" yazısını gördüğün an o satırı TAMAMEN KÖR GİBİ ATLA ve JSON listesine ASLA ekleme. Sadece tekil ürünlerin (Baza, Başlık, Yatak, İlave ürünler vb.) fiyatlarını al.

Çıktın KESİNLİKLE markdown kod blokları içinde veya dışında sadece saf JSON objesi içermelidir. Başka hiçbir açıklama yazma.
İstediğimiz JSON modeli tam olarak şudur:
{{
  "page_number": {page_number},
  "items": [
    {{
      "brand": "MARKA",
      "model": "MODEL",
      "product_type": "ÜRÜN CİNSİ",
      "size_or_spec": "EBAT VEYA Standart",
      "price": 20920.00,
      "currency": "TL"
    }}
  ]
}}
'''

    response = client.chat.completions.create(
        model="gpt-4o-2024-08-06",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Lütfen görseldeki güncel ürünlerin verilerini belirlenen JSON formatına göre listele. Tek bir fiyatı bile atlama!"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.0,
        max_tokens=16384
    )
    
    response_content = response.choices[0].message.content
    try:
        # Pydantic ile gelen JSON'ı validate ve deserialize ediyoruz.
        extracted_data = ExtractedPageData.model_validate_json(response_content)
        return extracted_data
    except ValidationError as e:
        # Eğer hatalı bir tip dönerse hata verecek (Örn float yerine metin fiyatsa)
        print(f"Veri doğrulaması başarısız oldu (Sayfa {page_number}):\n{e}")
        raise e
