from curl_cffi import requests
import json
import time
import os
from datetime import datetime

def a101_tum_kataloglari_cek():
    base_api = "https://rio.a101.com.tr/dbmk89vnr/CALL/poster"
    list_url = f"{base_api}/list/default?__culture=tr-TR&__platform=web"
    
    # Doğrudan tarayıcından yakalanan orijinal ve yetkili başlıklar:
    headers = {
        "a101-user-agent": "web-3.0.3",
        "accept": "application/json, text/plain, */*",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJwcm9qZWN0SWQiOiJkYm1rODl2bnIiLCJpZGVudGl0eSI6ImVuZHVzZXIiLCJhbm9ueW1vdXMiOmZhbHNlLCJ1c2VySWQiOiJub25tZW0yNjEwMDZneDZHR1lraThrZ1UiLCJjbGFpbXMiOnsiY2RoSWQiOiIxMDAwIiwiZGV2aWNlSWQiOiJwN3h2dC15aGg3cC0xaDRtbi0zZXVlbyIsIm1wVXNlcklkIjoibm9ubWVtMjYxMDA2Z3g2R0dZa2k4a2dVIn0sInNlc3Npb25JZCI6IjE0OTk0MzEyZGRkMjQyM2ZhZjg3OTEzYmIyMGU3OTg4IiwiaWF0IjoxNzkxNDY2NDY4LCJleHAiOjE3OTE0NzAwNjh9.x1VA_l5UmixRJJZzEChsLEaD5e0Ku2Lx0gnxOTNH512KUdKxfhIl9a9qiD9tIlPFlaSwVgbUl-XOzKv_eXSNASMNUsf7QCa7COgfFulfy5FhRBYza-gbTxQjNyXCnDB25kbLYC1SiXKXygpmAl_bX79_EWymQKWFmnRCQ6auoYW1i578EeOxEhKmvtuakN9OHMu0hlvqX_GtbHb01qBRsneXBt_uS2jueV1TdxH9XDIeSsvRiGHw113ICTFPhyXA0MSfMKG_A98fOv6i-f3CCoPcNQB9lDDYMmonGtZ7WWoIHwpG-v-cSUZC60KXHQOW6er3j3RxJBPJDzPuRDRXJA",
        "installationid": "cac717477285155399a774bd92980d25",
        "content-type": "application/json",
        "origin": "https://www.a101.com.tr",
        "referer": "https://www.a101.com.tr/",
        "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not A(Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    session = requests.Session(impersonate="chrome120")
    
    print("A101 kampanya listesi alınıyor...")
    try:
        res = session.get(list_url, headers=headers, timeout=20)
    except Exception as e:
        print(f"[-] A101 Bağlantı hatası: {e}")
        return {}

    if res.status_code != 200:
        print(f"[-] Liste alınamadı! Hata kodu: {res.status_code}")
        return {}

    veri = res.json()
    items = veri.get("items") or veri.get("data") or []
    if isinstance(veri, list):
        items = veri

    print(f"[+] Toplam {len(items)} aktif kampanya grubu tespit edildi.\n")

    kampanyalar = []
    toplam_sayfa_sayisi = 0

    for item in items:
        kampanya_id = item.get("id")
        baslik = item.get("title", "").strip() or "A101 Aktüel"
        
        if not kampanya_id:
            continue

        print(f" -> Çekiliyor: {baslik}...")
        
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
                    # 1.5 MB'lık PNG yerine hafif JPG/WebP versiyonunu al
                    opt_url = img_url.replace(".png", ".jpg").replace("_1024x1024", "_800x800")
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
                opt_kapak = kapak.replace(".png", ".jpg").replace("_1024x1024", "_800x800")
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
        print(f"\n[OK] A101 başarıyla güncellendi: {sonuc.get('toplam_afis_sayisi', 0)} sayfa")