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

    # 1. Kırık ve boş olmayan tüm HD afişleri topla
    tum_gecerli_afisler = []
    eklenen_afisler = set()

    for img in soup.select("img[src*='uploads/afisler/']"):
        src = img.get("src") or img.get("data-src") or ""
        dosya = src.split("/")[-1].strip()

        # Boş / kırık linkleri doğrudan atla (14 Ekim gibi görseli yüklenmemiş olanlar)
        if dosya in ["k_", "k_.jpg", "", "k"]:
            continue

        if not src.startswith("http"):
            src = base_url + src

        hd_url = src.replace("/k_", "/")

        if hd_url not in eklenen_afisler:
            eklenen_afisler.add(hd_url)
            tum_gecerli_afisler.append({
                "sayfa_no": len(tum_gecerli_afisler) + 1,
                "afis_hd": hd_url,
                "onizleme": src
            })

    # 2. Menü butonlarını topla, sadece görseli olmayan (kırık) kategoriyi ele
    gecerli_kategoriler = []
    butonlar = soup.select("a[href*='Bim_AfisKey']")

    # Sayfadaki kırık resimlerin bağlı olduğu başlıkları tespit et
    kirik_basliklar = set()
    for img in soup.select("img[src*='uploads/afisler/']"):
        src = img.get("src", "")
        if src.split("/")[-1].strip() in ["k_", "k_.jpg", ""]:
            # Kırık resmin üst kapsayıcısındaki başlığı bul
            parent = img.find_parent("div", class_="subarea") or img.find_parent("div", class_="rightArea") or img.find_parent("div")
            if parent:
                kirik_basliklar.add(parent.get_text(strip=True))

    for a in butonlar:
        metin = a.get_text(strip=True)
        href = a.get("href", "")
        
        if not metin or not href:
            continue

        # Görseli sitede boş olan başlığı ele
        if any(kb in metin or metin in kb for kb in kirik_basliklar if kb):
            print(f"[-] Görseli bulunmadığı için elendi: {metin}")
            continue

        # Manuel güvenlik filtresi (14 Ekim'in resmi sitede kırık olduğu için)
        if "14 Ekim" in metin:
            print(f"[-] Görseli yüklenmediği için elendi: {metin}")
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
        json.dump(sonuc, f, ensure_ascii=False, indent=4)

    print("\n" + "="*45)
    print("FİLTRELEME TAMAMLANDI")
    print(f"Yayındaki Kategori Sayısı : {sonuc['kategori_sayisi']}")
    print(f"Kullanıma Hazır HD Afiş   : {sonuc['toplam_aktif_afis']}")
    print("="*45)
    print("Yayındaki Onaylı Kampanyalar:")
    for kat in sonuc["kategoriler"]:
        print(f" • {kat['kategori_adi']}")
    print("="*45)