from curl_cffi import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import json
import os
from datetime import datetime

def bim_temiz_veri_cek():
    base_url = "https://www.bim.com.tr"
    url = f"{base_url}/Categories/680/afisler.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    os.makedirs("bim_afisler", exist_ok=True)
    session = requests.Session(impersonate="chrome120")

    print("BİM sunucusuna bağlanılıyor...")
    res = session.get(url, headers=headers)
    if res.status_code != 200:
        return {}

    soup = BeautifulSoup(res.content, "html.parser")
    tum_gecerli_afisler = []
    eklenen_afisler = set()

    for img in soup.select("img[src*='uploads/afisler/']"):
        src = img.get("src") or img.get("data-src") or ""
        dosya = src.split("/")[-1].strip()

        if dosya in ["k_", "k_.jpg", "", "k"]:
            continue

        if not src.startswith("http"):
            src = base_url + src

        if src not in eklenen_afisler:
            eklenen_afisler.add(src)
            sayfa_no = len(tum_gecerli_afisler) + 1
            dosya_adi = f"bim_afisler/bim_sayfa_{sayfa_no}.webp"

            # Görseli indirip doğrudan WebP formatına sıkıştırıyoruz (~80 KB)
            try:
                img_res = session.get(src, headers=headers)
                if img_res.status_code == 200:
                    pil_img = Image.open(BytesIO(img_res.content)).convert("RGB")
                    pil_img.save(dosya_adi, "WEBP", quality=75, method=4)
                    
                    tum_gecerli_afisler.append({
                        "sayfa_no": sayfa_no,
                        "afis_hd": dosya_adi,
                        "onizleme": dosya_adi
                    })
            except Exception as e:
                print(f"[-] BİM görsel indirilemedi ({src}): {e}")

    veri = {
        "market": "BİM",
        "guncellenme_zamani": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_aktif_afis": len(tum_gecerli_afisler),
        "afisler": tum_gecerli_afisler
    }

    return veri

if __name__ == "__main__":
    sonuc = bim_temiz_veri_cek()
    with open("data/bim.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, separators=(',', ':'))
    print(f"BİM WebP tamam: {len(sonuc.get('afisler', []))} sayfa")