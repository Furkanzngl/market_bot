from curl_cffi import requests
import json
import re
import os
from datetime import datetime

def a101_tum_kataloglari_cek():
    url = "https://www.a101.com.tr/afisler"
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache"
    }

    session = requests.Session(impersonate="chrome120")
    print("A101 web sitesinden afişler taranıyor...")

    try:
        res = session.get(url, headers=headers, timeout=25)
    except Exception as e:
        print(f"[-] A101 Bağlantı hatası: {e}")
        return {}

    if res.status_code != 200:
        print(f"[-] A101 web sayfası açılamadı! HTTP Kodu: {res.status_code}")
        return {}

    html = res.text
    kampanyalar = []
    toplam_sayfa = 0

    # 1. YÖNTEM: Next.js script blokları veya JSON nesnelerini yakalama
    # Sayfa içindeki poster/afiş nesnelerini regex ile ayıkla
    poster_bloklari = re.findall(r'\{[^{}]*?"id"\s*:\s*"([a-zA-Z0-9_-]{10,30})"[^{}]*?"title"\s*:\s*"([^"]+)"[^{}]*?\}', html)
    
    # Tüm görsel CDN linklerini ayıkla
    cdn_resimler = re.findall(r'https://cdn2\.a101\.com\.tr/dbmk89vnr/CALL/Image/get/[a-zA-Z0-9_-]+_(?:1024x1024|800x800)\.(?:png|jpg)', html)
    cdn_resimler = list(dict.fromkeys(cdn_resimler))  # Tekrarları temizle

    # Afiş sayfalarını yakalama (detay linkleri veya poster id'leri)
    afis_linkleri = re.findall(r'/afisler/([a-zA-Z0-9_-]+)', html)
    afis_linkleri = list(dict.fromkeys(afis_linkleri))

    # Eğer regex ile bloklar bulunduysa yapılandır
    if poster_bloklari:
        for p_id, baslik in poster_bloklari:
            # İlgili afişe ait görselleri eşle
            sayfalar = []
            for img in cdn_resimler:
                opt_img = img.replace(".png", ".jpg").replace("_1024x1024", "_800x800")
                sayfalar.append({
                    "sayfa_no": len(sayfalar) + 1,
                    "resim_url": opt_img
                })
            
            if sayfalar:
                kampanyalar.append({
                    "kampanya_adi": baslik.encode().decode('unicode-escape', 'ignore') if '\\u' in baslik else baslik,
                    "kampanya_id": p_id,
                    "sayfa_sayisi": len(sayfalar),
                    "sayfalar": sayfalar[:10]  # Kampanya başına dengeli dağılım
                })
                toplam_sayfa += len(sayfalar[:10])

    # 2. YÖNTEM: Genel CDN Görsel Havuzu (Doğrudan ve kesin sonuç)
    if not kampanyalar and cdn_resimler:
        print(f"[+] Web sayfasından {len(cdn_resimler)} adet afiş görseli doğrudan ayıklandı.")
        sayfalar = []
        for img in cdn_resimler:
            opt_img = img.replace(".png", ".jpg").replace("_1024x1024", "_800x800")
            sayfalar.append({
                "sayfa_no": len(sayfalar) + 1,
                "resim_url": opt_img
            })

        kampanyalar.append({
            "kampanya_adi": "A101 Güncel Kampanyalar",
            "kampanya_id": "a101_guncel",
            "sayfa_sayisi": len(sayfalar),
            "sayfalar": sayfalar
        })
        toplam_sayfa = len(sayfalar)

    if not kampanyalar:
        print("[-] Sayfa içinden afiş verisi çözümlenemedi.")
        return {}

    print(f"[+] Başarılı: {len(kampanyalar)} kampanya grubu ve {toplam_sayfa} afiş sayfası kaydedildi.")

    return {
        "market": "A101",
        "guncelleme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_kampanya": len(kampanyalar),
        "toplam_afis_sayisi": toplam_sayfa,
        "kampanyalar": kampanyalar
    }

if __name__ == "__main__":
    veri = a101_tum_kataloglari_cek()
    if veri and veri.get("kampanyalar"):
        os.makedirs("data", exist_ok=True)
        with open("data/a101.json", "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, separators=(',', ':'))
        print(f"[OK] data/a101.json yazıldı ({veri['toplam_afis_sayisi']} sayfa).")