import pandas as pd
import unicodedata
import re

def normalize_text(text: str) -> str:
    """
    Metinleri normalize eder:
    - Küçük harfe çevirir.
    - Türkçe karakterleri ingilizce karakterlere çevirir (İ->i, ş->s vb.).
    - Noktalama işaretlerini, fazlalık boşlukları vb. siler.
    """
    if not isinstance(text, str):
        return ""
    
    # Python lower() Türkçe İ hatasını önlemek için ön küçültme
    text = text.replace('İ', 'i').replace('I', 'ı')
    
    # Küçük harfe çevir
    text = text.lower()
    
    # Görünmez nokta hatasını ( \u0307 ) temizle
    text = text.replace('\u0307', '')
    
    # Türkçe karakter dönüştürme (unicodedata.normalize NFKD tam mükemmel değildir, manuel replace daha sağlıklıdır)
    tr_map = str.maketrans("çğıöşü", "cgiosu")
    text = text.translate(tr_map)
    
    # Alfasayısal olmayan her şeyi (nokta, virgül, tire vb.) boşlukla değiştir
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # Çoklu boşlukları tek boşluğa indirge ve kenarlardaki boşlukları sil
    text = re.sub(r'\s+', ' ', text).strip()
    
    return apply_domain_dictionary(text)

EXCEL_DICTIONARY = {
    "baza": "bz",
    "baslik": "plk",
    "yatak": "karyola",
    "yitas": "yts",
    "yt": "yts",
    "set": "takim",
    "tk": "takim",
    "aura": "ayak ucu",
    "auc": "ayak ucu",          # Manuel olarak eklendi
    "komidin": "komodin",       # Manuel olarak eklendi
    "sifonyer": "sifonyer",     # Manuel olarak eklendi
    "şifonyer": "sifonyer",
    "kasa": "para kasasi",
    "kucuk": "kucuk",
    "buyuk": "buyuk",
    "tv": "tv",
    "unite": "unitesi"
}

def apply_domain_dictionary(text: str) -> str:
    """Belirlenmiş sözlük kısıtlamalarını (ERP Kısaltmaları) doğal dil üzerinden çevirir."""
    words = text.split()
    mapped_words = [EXCEL_DICTIONARY.get(w, w) for w in words]
    return " ".join(mapped_words)

def create_composite_key(*args) -> str:
    """
    Verilen alanları normalize edip birleştirerek eşleştirme anahtarı oluşturur.
    Örn: create_composite_key("Yitaş", "101-A", "Matkap", "10mm") -> "yitas 101 a matkap 10mm"
    """
    parts = [normalize_text(str(arg)) for arg in args if arg is not None and str(arg).strip() != ""]
    return " ".join(parts)

def load_excel_database(excel_path: str) -> pd.DataFrame:
    """
    Hedef Excel veritabanını Pandas ile okur.
    Gerçek uygulamada Sütun isimleri Excel'in yapısına göre dinamik ayarlanmalıdır.
    """
    df = pd.read_excel(excel_path)
    
    # NaN değerleri boş string yapalım
    df = df.fillna("")
    
    return df

def get_valid_excel_keys(df_excel: pd.DataFrame, excel_columns_mapping: dict) -> list[str]:
    """
    Excel veritabanını tarayarak kullanılabilecek geçerli ürün isimlerinin benzersiz listesini oluşturur.
    """
    valid_keys = set()
    for index, row in df_excel.iterrows():
        excel_brand = row.get(excel_columns_mapping.get('brand', 'FİRMA\nMARKA'), "")
        excel_type = row.get(excel_columns_mapping.get('type', 'ÜRÜN CİNSİ'), "")
        excel_model = row.get(excel_columns_mapping.get('model', 'ÜRÜN \nKODU'), "")
        excel_size = row.get(excel_columns_mapping.get('size', 'EBAT'), "")

        composite_key = create_composite_key(excel_brand, excel_model, excel_type, excel_size)
        if composite_key.strip():
            valid_keys.add(composite_key.strip())
            
    return sorted(list(valid_keys))

