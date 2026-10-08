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
            # The official CDN remains the image host. Re-encoding the source
            # as WebP costs a second lossy pass and makes every CI run download
            # and commit megabytes of identical image bytes.
            tum_gecerli_afisler.append({
                "sayfa_no": sayfa_no,
                "resim_url": src,
                # Kept for clients that already consume the previous schema.
                "afis_hd": src,
                "onizleme": src
            })

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
