from curl_cffi import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def bim_temiz_veri_cek():
    base_url = "https://www.bim.com.tr"
    url = f"{base_url}/Categories/680/afisler.aspx"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("BİM sunucusuna bağlanılıyor...")
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print(f"Bağlantı kurulamadı: {res.status_code}")
        return {}

    soup = BeautifulSoup(res.content, "html.parser")

    tum_gecerli_afisler = []
    eklenen_afisler = set()

    # Kırık resimlerin bağlı olduğu başlıkları tespit et
    kirik_basliklar = set()
    for img in soup.select("img[src*='uploads/afisler/']"):
        src = img.get("src", "")
        if src.split("/")[-1].strip() in ["k_", "k_.jpg", ""]:
            parent = img.find_parent("div", class_="subarea") or img.find_parent("div", class_="rightArea") or img.find_parent("div")
            if parent:
                kirik_basliklar.add(parent.get_text(strip=True))

    for img in soup.select("img[src*='uploads/afisler/']"):
        src = img.get("src") or img.get("data-src") or ""
        dosya = src.split("/")[-1].strip()

        # Boş ve kırık görselleri atla
        if dosya in ["k_", "k_.jpg", "", "k"]:
            continue

        if not src.startswith("http"):
            src = base_url + src

        # Mobil kota için optimize edilmiş src boyutunu kullanıyoruz
        if src not in eklenen_afisler:
            eklenen_afisler.add(src)
            tum_gecerli_afisler.append({
                "sayfa_no": len(tum_gecerli_afisler) + 1,
                "afis_hd": src,
                "onizleme": src
            })

    gecerli_kategoriler = []
    butonlar = soup.select("a[href*='Bim_AfisKey']")

    for a in butonlar:
        metin = a.get_text(strip=True)
        href = a.get("href", "")
        
        if not metin or not href:
            continue

        if any(kb in metin or metin in kb for kb in kirik_basliklar if kb):
            continue

        if "14 Ekim" in metin:
            continue

        tam_link = href if href.startswith("http") else base_url + href
        gecerli_kategoriler.append({
            "kategori_adi": metin,
            "url": tam_link
        })

    veri = {
        "market": "BİM",
        "guncellenme_zamani": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_aktif_afis": len(tum_gecerli_afisler),
        "kategori_sayisi": len(gecerli_kategoriler),
        "kategoriler": gecerli_kategoriler,
        "afisler": tum_gecerli_afisler
    }

    return veri

if __name__ == "__main__":
    sonuc = bim_temiz_veri_cek()

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, separators=(',', ':'))

    print("\n" + "="*45)
    print("BİM VERİLERİ SIKIŞTIRILARAK ALINDI")
    print(f"Kullanıma Hazır Afiş: {sonuc.get('toplam_aktif_afis', 0)}")
    print("="*45)