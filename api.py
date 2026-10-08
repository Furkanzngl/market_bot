from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from media import cached_webp, image_key
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


def _cache(response: Response, seconds: int = 300):
    response.headers["Cache-Control"] = f"public, max-age={seconds}, stale-while-revalidate=86400"


def _poster_url(page):
    return page.get("resim_url") or page.get("afis_hd") or page.get("dosya_yolu")


def _public_poster_url(source):
    """Turn stored local paths into API paths consumable by Android clients."""
    if not source:
        return source
    normalized = source.replace("\\", "/")
    if normalized.startswith("sok_afisler/"):
        return f"/images/sok/{normalized.rsplit('/', 1)[-1]}"
    if normalized.startswith("bim_afisler/"):
        return f"/images/bim/{normalized.rsplit('/', 1)[-1]}"
    return source


def _campaign_summary(campaign):
    pages = campaign.get("sayfalar", [])
    source = _poster_url(pages[0]) if pages else None
    cover = _public_poster_url(source)
    return {
        "kampanya_adi": campaign.get("kampanya_adi"),
        "kampanya_id": campaign.get("kampanya_id") or campaign.get("kampanya_adi"),
        "baslangic_tarihi": campaign.get("baslangic_tarihi"),
        "bitis_tarihi": campaign.get("bitis_tarihi"),
        "sayfa_sayisi": campaign.get("sayfa_sayisi") or campaign.get("toplam_sayfa") or len(pages),
        "kapak_url": cover,
        "kapak_onizleme_url": f"/api/image/{image_key(source)}?w=480" if source and source.startswith("http") else cover,
    }

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
def market_detayi(market_slug: str, response: Response):
    """BİM, A101, ŞOK veya Migros'un tüm güncel katalog verisini döner."""
    data = dosya_oku(market_slug.lower())
    if not data:
        raise HTTPException(status_code=404, detail="Market verisi bulunamadı.")
    _cache(response, 300)
    return data

@app.get("/api/v2/market/{market_slug}")
def market_manifest(market_slug: str, response: Response):
    """Tiny ViewPager payload: campaign cards only, no unseen poster pages."""
    data = dosya_oku(market_slug.lower())
    if not data:
        raise HTTPException(status_code=404, detail="Market verisi bulunamadı.")
    campaigns = data.get("kampanyalar")
    if campaigns is None:
        campaigns = [{"kampanya_adi": data.get("market"), "sayfalar": data.get("afisler", [])}]
    _cache(response, 3600)
    return {
        "market": data.get("market"),
        "guncelleme_tarihi": data.get("guncelleme_tarihi") or data.get("guncellenme_zamani"),
        "kampanyalar": [_campaign_summary(campaign) for campaign in campaigns],
    }

@app.get("/api/v2/market/{market_slug}/campaign/{campaign_id}")
def campaign_pages(market_slug: str, campaign_id: str, response: Response):
    """Poster pages are requested only after the user opens a campaign."""
    data = dosya_oku(market_slug.lower())
    if not data:
        raise HTTPException(status_code=404, detail="Market verisi bulunamadı.")
    for campaign in data.get("kampanyalar", []):
        current_id = str(campaign.get("kampanya_id") or campaign.get("kampanya_adi"))
        if current_id == campaign_id:
            pages = []
            for index, page in enumerate(campaign.get("sayfalar", []), 1):
                source = _poster_url(page)
                public_source = _public_poster_url(source)
                pages.append({
                    "sayfa_no": page.get("sayfa_no", index),
                    "orijinal_url": public_source,
                    "onizleme_url": f"/api/image/{image_key(source)}?w=480" if source and source.startswith("http") else public_source,
                    "hd_url": f"/api/image/{image_key(source)}?w=1080" if source and source.startswith("http") else public_source,
                })
            _cache(response, 3600)
            return {"kampanya_adi": campaign.get("kampanya_adi"), "sayfalar": pages}
    raise HTTPException(status_code=404, detail="Kampanya bulunamadı.")

@app.get("/api/image/{key}")
def poster_image(key: str, w: int = Query(480, ge=160, le=1440)):
    """Serve cached WebP derivatives; URL lookup prevents open-proxy abuse."""
    for market in ("a101", "bim", "migros"):
        data = dosya_oku(market) or {}
        campaigns = data.get("kampanyalar", []) or [{"sayfalar": data.get("afisler", [])}]
        for campaign in campaigns:
            for page in campaign.get("sayfalar", []):
                source = _poster_url(page)
                if source and source.startswith("http") and image_key(source) == key:
                    try:
                        file_path = cached_webp(source, w)
                        return FileResponse(file_path, media_type="image/webp", headers={"Cache-Control": "public, max-age=604800, immutable"})
                    except Exception as exc:
                        raise HTTPException(status_code=502, detail=f"Görsel hazırlanamadı: {exc}") from exc
    raise HTTPException(status_code=404, detail="Görsel bulunamadı.")

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
def migros_urunleri(category: str = Query(None, description="Kategori adına göre filtrele"), offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100), response: Response = None):
    """Migros ürünlerini listeler, kategori filtresi destekler."""
    data = dosya_oku("migros")
    if not data:
        raise HTTPException(status_code=404, detail="Migros verisi bulunamadı.")

    if category:
        for kat in data.get("kategoriler", []):
            if kat["kategori_adi"].lower() == category.lower():
                urunler = kat["urunler"]
                if response:
                    _cache(response, 300)
                return {**kat, "toplam_urun": len(urunler), "offset": offset, "limit": limit, "urunler": urunler[offset:offset + limit]}
        raise HTTPException(status_code=404, detail="Belirtilen kategori bulunamadı.")

    # Kategori verilmediyse tüm avantajlı ürünleri tek liste olarak döner
    tum_urunler = [u for kat in data.get("kategoriler", []) for u in kat["urunler"]]
    if response:
        _cache(response, 300)
    return {"toplam_urun": len(tum_urunler), "offset": offset, "limit": limit, "urunler": tum_urunler[offset:offset + limit]}

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
