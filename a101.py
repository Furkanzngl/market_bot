from curl_cffi import requests
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

    session = requests.Session(impersonate="chrome120")
    
    print("A101 kampanya listesi alınıyor...")
    try:
        res = session.get(list_url, headers=headers, timeout=20)
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return {}

    if res.status_code != 200:
        print(f"Liste alınamadı! Hata kodu: {res.status_code}")
        return {}

    veri = res.json()
    items = veri.get("items") or veri.get("data") or []
    if isinstance(veri, list):
        items = veri

    print(f"Toplam {len(items)} aktif kampanya grubu tespit edildi.\n")

    kampanyalar = []
    toplam_sayfa_sayisi = 0

    for item in items:
        kampanya_id = item.get("id")
        baslik = item.get("title", "").strip() or "A101 Aktüel"
        
        if not kampanya_id:
            continue

        detail_url = f"{base_api}/get/default/{kampanya_id}?__culture=tr-TR&__platform=web"
        try:
            detay_res = session.get(detail_url, headers=headers, timeout=20)
        except Exception:
            continue
        
        sayfalar = []
        baslangic = item.get("start", "")
        bitis = item.get("end", "")

        if detay_res.status_code == 200:
            detay_data = detay_res.json()
            pages_list = detay_data.get("pages", [])
            
            for p in pages_list:
                img_url = ""
                if isinstance(p, dict):
                    img_url = p.get("image") or p.get("url") or ""
                    if not img_url and isinstance(p.get("web"), dict):
                        img_url = p["web"].get("image", "")
                elif isinstance(p, str):
                    img_url = p

                if img_url:
                    # PNG'yi kaldırıp A101 CDN'inden hafif WebP/JPG talep ediyoruz:
                    opt_url = img_url.replace(".png", ".webp").replace(".jpg", ".webp").replace("_1024x1024", "_800x800")
                    sayfalar.append({
                        "sayfa_no": len(sayfalar) + 1,
                        "resim_url": opt_url
                    })

            if not baslangic:
                baslangic = detay_data.get("start", "")
            if not bitis:
                bitis = detay_data.get("end", "")

        if not sayfalar:
            kapak = item.get("web", {}).get("image") or item.get("image")
            if kapak:
                opt_kapak = kapak.replace(".png", ".webp").replace(".jpg", ".webp").replace("_1024x1024", "_800x800")
                sayfalar.append({"sayfa_no": 1, "resim_url": opt_kapak})

        kampanyalar.append({
            "kampanya_adi": baslik,
            "kampanya_id": kampanya_id,
            "baslangic_tarihi": baslangic,
            "bitis_tarihi": bitis,
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
    if sonuc and sonuc.get("kampanyalar"):
        os.makedirs("data", exist_ok=True)
        with open("data/a101.json", "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, separators=(',', ':'))
        print(f"\nA101 güncellendi: {sonuc.get('toplam_afis_sayisi', 0)} sayfa")