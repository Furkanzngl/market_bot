from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI(
    title="Market Aktüel & İndirim API",
    description="BİM, A101, ŞOK ve Migros Güncel Aktüel ve İndirim Verileri",
    version="1.0.0"
)

# Android veya Web erişimi için CORS izni
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eğer yerel afiş görselleri kaydettiysen onları dışarıya açar (örn: http://ip:8000/images/...)
if os.path.exists("sok_afisler"):
    app.mount("/images/sok", StaticFiles(directory="sok_afisler"), name="sok_afisler")
if os.path.exists("bim_afisler"):
    app.mount("/images/bim", StaticFiles(directory="bim_afisler"), name="bim_afisler")

def dosya_oku(dosya_adi):
    slug = dosya_adi.lower().strip()
    
    # BİM verisi klasörde doğrudan data.json olarak duruyor
    olasi_yollar = [
        f"{slug}_data.json",
        f"data/{slug}.json",
        f"{slug}.json"
    ]
    
    if slug == "bim":
        olasi_yollar.append("data.json")

    for yol in olasi_yollar:
        if os.path.exists(yol):
            try:
                with open(yol, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return None

@app.get("/")
def kok_dizin():
    return {
        "status": "online",
        "message": "Market Aktüel API Servisi Çalışıyor",
        "endpoints": [
            "/api/markets",
            "/api/market/{slug}",
            "/api/migros/categories",
            "/api/migros/products",
            "/api/search?q=..."
        ]
    }

@app.get("/api/markets")
def market_listesi():
    """Android ana ekranı için market logoları ve özet bilgiler."""
    return [
        {
            "id": 1,
            "name": "BİM",
            "slug": "bim",
            "type": "catalog",
            "badge": "Salı & Cuma"
        },
        {
            "id": 2,
            "name": "A101",
            "slug": "a101",
            "type": "catalog",
            "badge": "Perşembe & Hafta Sonu"
        },
        {
            "id": 3,
            "name": "ŞOK",
            "slug": "sok",
            "type": "catalog",
            "badge": "Çarşamba & Hafta Sonu"
        },
        {
            "id": 4,
            "name": "Migros",
            "slug": "migros",
            "type": "products_and_catalog",
            "badge": "Migroskop Fırsatları"
        }
    ]

@app.get("/api/market/{market_slug}")
def market_detayi(market_slug: str):
    """BİM, A101, ŞOK veya Migros'un tüm güncel katalog verisini döner."""
    data = dosya_oku(market_slug.lower())
    if not data:
        raise HTTPException(status_code=404, detail="Market verisi bulunamadı.")
    return data

@app.get("/api/status")
def toplama_durumu():
    """Son toplama çalıştırmasının kaynak bazındaki durumunu döner."""
    return dosya_oku("durum") or {"marketler": {}}

@app.get("/api/migros/categories")
def migros_kategorileri():
    """Migros'un reyon listesini ve ürün sayılarını döner."""
    data = dosya_oku("migros")
    if not data:
        raise HTTPException(status_code=404, detail="Migros verisi bulunamadı.")
    
    kategoriler = [
        {
            "kategori_adi": k["kategori_adi"],
            "urun_sayisi": k["urun_sayisi"]
        }
        for k in data.get("kategoriler", [])
    ]
    return kategoriler

@app.get("/api/migros/products")
def migros_urunleri(category: str = Query(None, description="Kategori adına göre filtrele")):
    """Migros ürünlerini listeler, kategori filtresi destekler."""
    data = dosya_oku("migros")
    if not data:
        raise HTTPException(status_code=404, detail="Migros verisi bulunamadı.")

    if category:
        for kat in data.get("kategoriler", []):
            if kat["kategori_adi"].lower() == category.lower():
                return kat
        raise HTTPException(status_code=404, detail="Belirtilen kategori bulunamadı.")

    # Kategori verilmediyse tüm avantajlı ürünleri tek liste olarak döner
    tum_urunler = [u for kat in data.get("kategoriler", []) for u in kat["urunler"]]
    return {
        "toplam_urun": len(tum_urunler),
        "urunler": tum_urunler
    }

@app.get("/api/search")
def urun_ara(q: str = Query(..., min_length=2, description="Aranacak kelime")):
    """Migros avantajlı ürünleri içinde arama yapar."""
    data = dosya_oku("migros")
    if not data:
        return {"sonuc_sayisi": 0, "sonuclar": []}

    kelime = q.lower().strip()
    bulunanlar = []

    for kat in data.get("kategoriler", []):
        for u in kat["urunler"]:
            if kelime in u["urun_adi"].lower() or kelime in u["marka"].lower():
                bulunanlar.append(u)

    return {
        "arama_kelimesi": q,
        "sonuc_sayisi": len(bulunanlar),
        "sonuclar": bulunanlar
    }
