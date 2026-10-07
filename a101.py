from curl_cffi import requests
from PIL import Image
from io import BytesIO
import json
import time
import os
from datetime import datetime

def a101_tum_kataloglari_cek():
    base_api = "https://rio.a101.com.tr/dbmk89vnr/CALL/poster"
    list_url = f"{base_api}/list/default?__culture=tr-TR&__platform=web"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Origin": "https://www.a101.com.tr",
        "Referer": "https://www.a101.com.tr/"
    }

    os.makedirs("a101_afisler", exist_ok=True)
    session = requests.Session(impersonate="chrome120")
    
    print("A101 kampanya listesi alınıyor...")
    res = session.get(list_url, headers=headers)
    if res.status_code != 200:
        return {}

    veri = res.json()
    items = veri.get("items") or veri.get("data") or []
    if isinstance(veri, list):
        items = veri

    kampanyalar = []
    toplam_sayfa_sayisi = 0
    genel_sayac = 1

    for item in items:
        kampanya_id = item.get("id")
        baslik = item.get("title", "").strip() or "A101 Aktüel"
        if not kampanya_id:
            continue

        detail_url = f"{base_api}/get/default/{kampanya_id}?__culture=tr-TR&__platform=web"
        detay_res = session.get(detail_url, headers=headers)
        
        sayfalar = []
        if detay_res.status_code == 200:
            detay_data = detay_res.json()
            pages_list = detay_data.get("pages", [])
            
            for p in pages_list:
                img_url = p.get("image") or p.get("url") if isinstance(p, dict) else (p if isinstance(p, str) else "")
                if not img_url and isinstance(p, dict) and isinstance(p.get("web"), dict):
                    img_url = p["web"].get("image", "")

                if img_url:
                    dosya_adi = f"a101_afisler/a101_sayfa_{genel_sayac}.webp"
                    try:
                        img_res = session.get(img_url, headers=headers)
                        if img_res.status_code == 200:
                            pil_img = Image.open(BytesIO(img_res.content)).convert("RGB")
                            pil_img.save(dosya_adi, "WEBP", quality=75, method=4)
                            
                            sayfalar.append({
                                "sayfa_no": len(sayfalar) + 1,
                                "resim_url": dosya_adi
                            })
                            genel_sayac += 1
                    except Exception as e:
                        print(f"[-] A101 görsel indirilemedi: {e}")

        kampanyalar.append({
            "kampanya_adi": baslik,
            "kampanya_id": kampanya_id,
            "sayfa_sayisi": len(sayfalar),
            "sayfalar": sayfalar
        })
        toplam_sayfa_sayisi += len(sayfalar)
        time.sleep(0.1)

    veri_paketi = {
        "market": "A101",
        "guncelleme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_kampanya": len(kampanyalar),
        "toplam_afis_sayisi": toplam_sayfa_sayisi,
        "kampanyalar": kampanyalar
    }

    return veri_paketi

if __name__ == "__main__":
    sonuc = a101_tum_kataloglari_cek()
    with open("data/a101.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, separators=(',', ':'))
    print(f"A101 WebP tamam: {sonuc.get('toplam_afis_sayisi', 0)} sayfa")