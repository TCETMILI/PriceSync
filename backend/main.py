import os
import asyncio
import json
import pandas as pd
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from services.pdf_service import convert_pdf_to_images
from services.vision_service import extract_data_from_image
from services.normalization import load_excel_database
from services.entity_resolution import resolve_entities
from services.excel_injector import ExcelInjector

app = FastAPI(title="PriceSync Backend API", description="AI-Driven Entity Resolution & Data Injection API")

# İleride Frontend'den gelecek istekler için CORS izni
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Progress durumu (Demo amaçlı basit bellek store)
processing_status = {"status": "idle", "message": "Sistem Hazır", "progress": 0}

class ResolveRequest(BaseModel):
    match_id: int
    excel_row_index: int
    new_price: float
    # İskontosuz Perakende sütunu ya da konfigürasyondan gelecek sütun (Varsayılan Q)
    price_column: str = "T" # Örnek kolon harfi

def process_pdf_background(pdf_path: str):
    global processing_status
    excel_path = os.getenv("EXCEL_PATH", "/app/data/SSTOK_LISTESI.xlsx")
    
    try:
        processing_status = {"status": "processing", "message": "PDF PNG'ye dönüştürüldü...", "progress": 10}
        image_paths = convert_pdf_to_images(pdf_path, dpi=300)
        
        if not image_paths:
            processing_status = {"status": "error", "message": "PDF'ten görüntü çıkarılamadı.", "progress": 0}
            return
            
        processing_status = {"status": "processing", "message": "Sayfalar Vision AI ile okunuyor...", "progress": 30}
        
        all_extracted_items = []
        for idx, img_path in enumerate(image_paths):
            processing_status = {"status": "processing", "message": f"Sayfa {idx+1}/{len(image_paths)} okunuyor...", "progress": 30 + int((idx/len(image_paths))*20)}
            extracted_data = extract_data_from_image(img_path, page_number=idx+1)
            all_extracted_items.extend(extracted_data.items)
        
        processing_status = {"status": "processing", "message": "Excel Veritabanı belleğe yükleniyor...", "progress": 50}
        df_excel = load_excel_database(excel_path)
        
        excel_mapping = {'brand': 'FİRMA\nMARKA', 'model': 'ÜRÜN\nADI', 'type': 'ÜRÜN CİNSİ', 'size': 'EBAT'}
        
        processing_status = {"status": "processing", "message": "Akıllı Eşleştirme Motoru ve AI Hakem devrede...", "progress": 70}
        match_results = resolve_entities(
            extracted_items=all_extracted_items,
            df_excel=df_excel,
            excel_columns_mapping=excel_mapping
        )
        
        processing_status = {"status": "processing", "message": "Otonom Enjeksiyon ve Analiz Raporu oluşturuluyor...", "progress": 90}
        
        updates = []
        audit_records = []
        
        def process_matches(match_list, method_name):
            for m in match_list:
                pdf = m['pdf_data']
                pdf_isim = f"{pdf.get('brand','')} {pdf.get('product_type','')} {pdf.get('model','')} {pdf.get('size_or_spec','')}".strip()
                fiyat = pdf.get('price', 0.0)
                
                excel = m.get('excel_match', {})
                excel_isim = excel.get('composite_key', '')
                excel_row = excel.get('index', -1)
                
                if excel_row != -1:
                    updates.append({
                        "excel_row_index": excel_row,
                        "new_price": float(fiyat),
                        "price_column": "T"
                    })
                
                audit_records.append({
                    "Orijinal PDF Ürünü": pdf_isim,
                    "Eşleşen Excel Adayı": excel_isim,
                    "Eşleşme Yöntemi": method_name,
                    "Güven Skoru (%)": m.get('confidence', 0.0),
                    "Uygulanan Yeni Fiyat": fiyat
                })

        process_matches(match_results.get("exact_matches", []), "Kesin Eşleşme")
        process_matches(match_results.get("fuzzy_matches", []), "Bulanık Mantık")
        process_matches(match_results.get("ai_matches", []), "AI Hakem")
        
        # Pending olanlar (Eşleşmeyenler tablosuna)
        for p in match_results.get("pending_matches", []):
            pdf = p['pdf_data']
            pdf_isim = f"{pdf.get('brand','')} {pdf.get('product_type','')} {pdf.get('model','')} {pdf.get('size_or_spec','')}".strip()
            fiyat = pdf.get('price', 0.0)
            
            audit_records.append({
                "Orijinal PDF Ürünü": pdf_isim,
                "Eşleşen Excel Adayı": "BOŞ",
                "Eşleşme Yöntemi": "BULUNAMADI",
                "Güven Skoru (%)": 0.0,
                "Uygulanan Yeni Fiyat": "Uygulanmadı"
            })
            
        # Otonom Excel Enjeksiyonu
        # Updates listesi boş olsa bile orijinal Excel SSTOK_LISTESI_GUNCEL olarak kaydedilmek ZORUNDA
        injector = ExcelInjector(excel_path=excel_path)
        injector.inject_prices(updates)
            
        # Rapor Oluşturma
        df_audit = pd.DataFrame(audit_records)
        report_path = "/app/data/PriceSync_Rapor.xlsx"
        df_audit.to_excel(report_path, index=False)
             
        processing_status = {"status": "completed", "message": f"{len(image_paths)} Sayfa Tamamlandı! Rapor ve Excel Hazır.", "progress": 100}


    except Exception as e:
        import traceback
        traceback.print_exc()
        processing_status = {"status": "error", "message": f"Kritik Hata: {str(e)}", "progress": 0}


@app.post("/upload-pdf")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """PDF dosyasını alır ve arka planda Vision + Eşleştirme sürecini başlatır."""
    upload_dir = "/app/data"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, "temp_upload.pdf")
    
    # 🚨 SELF-DESTRUCT (ÖN TEMİZLİK) MEKANİZMASI 🚨
    # Yeni dosya yüklenir yüklenmez eski raporları acımasızca sil!
    try:
        # data klasöründeki eski Excel ve tüm CACHE (.db, .bin, .json, vb.) dosyalarını temizle
        import glob
        for ext in ["*.xlsx", "*.db", "*.bin", "*.json", "*.index", "*.pkl"]:
            for f_path in glob.glob(os.path.join(upload_dir, ext)):
                # SSTOK_LISTESI.xlsx veritabanının silinmesini engelle
                if os.path.basename(f_path) != "SSTOK_LISTESI.xlsx":
                    try:
                        os.remove(f_path)
                        print(f"🗑️ Önbellek silindi: {f_path}")
                    except OSError:
                        pass
    except Exception as e:
        print(f"Eski dosya silinemedi: {e}")

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    # İşlemi arkaplana at
    background_tasks.add_task(process_pdf_background, file_path)
    return {"message": "Dosya başarıyla alındı, eski veriler imha edildi, analiz başlatıldı."}



@app.get("/download-excel")
def download_excel():
    """Güncellenmiş Excel dosyasını Frontend'e indirilebilir formatta sunar."""
    file_path = "/app/data/SSTOK_LISTESI_GUNCEL.xlsx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Güncel dosya henüz hazır değil veya işlem devam ediyor!")
    return FileResponse(
        file_path, 
        filename="SSTOK_LISTESI_GUNCEL.xlsx", 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )

@app.get("/download-report")
def download_report():
    """Oluşturulan PriceSync Audit Log raporunu indirir."""
    file_path = "/app/data/PriceSync_Rapor.xlsx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Rapor henüz oluşturulmadı, lütfen işlemin bitmesini bekleyin!")
    return FileResponse(
        file_path, 
        filename="PriceSync_Rapor.xlsx", 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    )

@app.get("/stream-status")
async def stream_status(request: Request):
    """
    Server-Sent Events (SSE) ile Frontend'e canlı ilerleme yüzdesi (progress bar) gönderir.
    """
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            # Status dict'ini JSON olarak yayınla (sse-starlette standart dict beklentisi)
            yield {"data": json.dumps(processing_status)}
            await asyncio.sleep(1)  # Saniyede bir güncelle

    return EventSourceResponse(event_generator())
