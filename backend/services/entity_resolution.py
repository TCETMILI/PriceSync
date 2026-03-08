import pandas as pd
import re
from rapidfuzz import fuzz, process
from rank_bm25 import BM25Okapi
from services.normalization import create_composite_key
from services.vector_search import VectorDatabase
from services.ai_judge import judge_match

def resolve_entities(extracted_items: list, df_excel: pd.DataFrame, excel_columns_mapping: dict):
    """
    Huni Mimarisi uygulanır:
    1. Kesin Eşleşme (Exact Match)
    2. Bulanık Eşleşme (RapidFuzz - Levenshtein)
    3. Vektörel Arama (FAISS - Semantic Search) Top-K=3
    4. Yapay Zeka Hakemi (GPT-4o-mini) -> Kesin Onay -> Eşleşme
    
    Tüm aşamalardan geçemeyenler pending_matches havuzunda (insan onayı) bekler.
    """
    exact_matches = []
    fuzzy_matches = []
    ai_matches = []
    pending_matches = []

    # Excel veritabanı belleğe alımı ve anahtar hazırlama
    excel_keys = {}
    text_item_pairs_for_faiss = [] # Vektör DB için (metin, data) tuple listesi
    
    for index, row in df_excel.iterrows():
        brand = row.get(excel_columns_mapping.get('brand', ''), '')
        model = row.get(excel_columns_mapping.get('model', ''), '')
        ptype = row.get(excel_columns_mapping.get('type', ''), '')
        size = str(row.get(excel_columns_mapping.get('size', ''), '')).strip()
        
        # EBAT kolonu boşsa, GENİŞLİK ve DERİNLİK kolonlarından ebat üret (Örn: 150x200)
        if not size or size.lower() == 'nan':
            genislik = str(row.get('GENİŞLİK', '')).strip()
            derinlik = str(row.get('DERİNLİK', '')).strip()
            if genislik and derinlik and genislik.lower() != 'nan' and derinlik.lower() != 'nan':
                try:
                    g = int(float(genislik))
                    d = int(float(derinlik))
                    size = f"{g}x{d}"
                except ValueError:
                    size = f"{genislik}x{derinlik}"
                    
        key = create_composite_key(brand, model, ptype, size)
        
        if key:
            item_data = {
                'index': index,
                'original_row': row.to_dict(),
                'composite_key': key
            }
            excel_keys[key] = item_data
            text_item_pairs_for_faiss.append((key, item_data))
            
    excel_key_list = list(excel_keys.keys())
    
    # 3. Aşama İçin Vektör Veritabanını Başlat (Cache veya API kullanarak indexler)
    vdb = VectorDatabase()
    vdb.initialize(text_item_pairs_for_faiss)
    
    # BM25 Lexical Arama İndeksi Hazırlığı
    tokenized_corpus = [doc.split() for doc in excel_key_list]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # 2. Huni: Çıkartılan veriler üzerinde işlem
    for pdf_item in extracted_items:
        brand = getattr(pdf_item, 'brand', '').strip()
        if not brand:
            brand = 'YİTAŞ'  # Marka boş gelirse ZORLA Yitaş ekle
            
        model = getattr(pdf_item, 'model', '').strip()
        # PDF fontu kaynaklı kelime ayrılmalarını temizle (mi moza -> mimoza)
        model = model.replace(" ", "")
        
        ptype = getattr(pdf_item, 'product_type', '').strip()
        size = getattr(pdf_item, 'size_or_spec', '').strip()
        
        target_key = create_composite_key(brand, model, ptype, size)
        if not target_key:
            continue
            
        result_item = {
            'pdf_data': pdf_item.model_dump() if hasattr(pdf_item, 'model_dump') else pdf_item,
            'target_key': target_key
        }
        
        # AŞAMA 1: Kesin Eşleşme (Exact Match)
        if target_key in excel_keys:
            result_item['match_type'] = 'exact'
            result_item['excel_match'] = excel_keys[target_key]
            result_item['confidence'] = 100.0
            exact_matches.append(result_item)
            continue
            
        # AŞAMA 2: Bulanık Eşleşme (RapidFuzz)
        best_match = process.extractOne(
            target_key, 
            excel_key_list, 
            scorer=fuzz.token_sort_ratio,
            score_cutoff=85.0 
        )
        
        if best_match:
            matched_key, score, match_index = best_match
            if score >= 90.0:  # Eğer RapidFuzz çok eminse
                 result_item['match_type'] = 'fuzzy'
                 result_item['excel_match'] = excel_keys[matched_key]
                 result_item['confidence'] = float(score)
                 fuzzy_matches.append(result_item)
                 continue
                 
        # AŞAMA 3: Hibrit Arama (Semantic FAISS + Keyword BM25) & Strict Size Regex
        # Vektör aramadan en iyi 10 adayı al, BM25 ile kelime odaklı birleştir, Regex Filtresinden geçir
        faiss_candidates = vdb.search(target_key, top_k=10)
        
        # Hedefteki Ebat tespit (Örn: 150x200)
        target_size_match = re.search(r'\b\d{2,3}x\d{2,3}\b', target_key)
        target_size = target_size_match.group() if target_size_match else None
        
        hybrid_candidates = []
        tokenized_query = target_key.split()
        
        for cand in faiss_candidates:
            cand_text = cand.get('text', '')
            
            # Ebat (Size) Zorunlu Filtresi (Strict Regex Check)
            cand_size_match = re.search(r'\b\d{2,3}x\d{2,3}\b', cand_text)
            cand_size = cand_size_match.group() if cand_size_match else None
            
            # Eğer ikisinde de ebat var ve uyuşmuyorsa, bu adayı direk ÇÖPE AT (Skor = 0)
            if target_size and cand_size and target_size != cand_size:
                 continue
            
            # BM25 Skorunu hesapla (Lexical Search)
            # Bu indeks Excel keys içindeki gerçek indeksini bulmalı ama basitleştirmek için:
            bm25_score = bm25.get_scores(tokenized_query)[excel_key_list.index(cand_text)] if cand_text in excel_key_list else 0
            
            # FAISS Skorunu Normalize et: FAISS distance döndürür, L2 küçüldükçe benzerlik artar
            distance = float(cand.get('distance', 0.0))
            semantic_score = 1.0 / (1.0 + distance)
            
            # Ensemble: 0.6 FAISS + 0.4 BM25
            combined_score = (0.6 * semantic_score) + (0.4 * bm25_score)
            
            hybrid_candidates.append({
                'text': cand_text,
                'item': cand.get('item', {}),
                'score': combined_score
            })
            
        # Skorlara göre hibrit listeyi büyükten küçüğe sırala ve top 3 al
        hybrid_candidates = sorted(hybrid_candidates, key=lambda x: x.get('score', 0.0), reverse=True)[:3]
        candidate_texts = [c.get('text', '') for c in hybrid_candidates]
        
        if candidate_texts:
            # Yapay Zeka Hakemine Danış
            ai_decision = judge_match(target_key, candidate_texts)
            print(f"🧐 [AI Gözlemi] Hedef: '{target_key}' | Karar Indeksi: {ai_decision.match_index} | Güven: {ai_decision.confidence}%")
            
            # %85 üstü güven varsa ve geçerli bir indeks döndüyse
            if ai_decision.match_index != -1 and ai_decision.confidence >= 85.0:
                 chosen_candidate = hybrid_candidates[ai_decision.match_index]
                 result_item['match_type'] = 'ai_judge_hybrid'
                 result_item['excel_match'] = chosen_candidate['item']
                 result_item['confidence'] = ai_decision.confidence
                 ai_matches.append(result_item)
                 continue
        
        # SONA KALANLAR: İnsan Onayı Bekleyenler (Pending)
        # Frontend'deki "Çözüm Merkezi"ne (Resolution Center) listelenecek havuz.
        result_item['match_type'] = 'pending'
        result_item['candidates'] = faiss_candidates  # Frontend gösterimi için adayları ekleyelim
        result_item['confidence'] = 0.0
        pending_matches.append(result_item)

    return {
        "exact_matches": exact_matches,
        "fuzzy_matches": fuzzy_matches,
        "ai_matches": ai_matches,
        "pending_matches": pending_matches,
        "stats": {
            "total_extracted": len(extracted_items),
            "exact_count": len(exact_matches),
            "fuzzy_count": len(fuzzy_matches),
            "ai_judge_count": len(ai_matches),
            "pending_count": len(pending_matches)
        }
    }
