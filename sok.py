from curl_cffi import requests
import pypdfium2 as pdfium
import json
import os
from datetime import datetime

def sok_afislerini_cek():
    kampanyalar_kaynak = [
        {
            "kampanya_adi": "ŞOK'ta Haftanın Fırsatları (Çarşamba)",
            "url": "https://kurumsal.sokmarket.com.tr/firsatlar/carsamba/"
        },
        {
            "kampanya_adi": "ŞOK'ta Hafta Sonu Fırsatları",
            "url": "https://kurumsal.sokmarket.com.tr/firsatlar/hafta-sonu/"
        }
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,*/*",
        "Referer": "https://kurumsal.sokmarket.com.tr/haftanin-firsatlari/firsatlar"
    }

    session = requests.Session(impersonate="chrome120")
    os.makedirs("sok_afisler", exist_ok=True)

    kampanyalar = []
    toplam_sayfa = 0

    print("ŞOK resmi PDF katalogları indiriliyor...\n")

    for idx, k in enumerate(kampanyalar_kaynak, 1):
        adi = k["kampanya_adi"]
        url = k["url"]

        print(f"[{idx}/{len(kampanyalar_kaynak)}] İndiriliyor: {adi}...")
        try:
            res = session.get(url, headers=headers)
            if res.status_code != 200:
                print(f"   [-] Hata kodu: {res.status_code}")
                continue

            # PDF doğrulaması (PDF dosyaları %PDF- ile başlar)
            if not res.content.startswith(b"%PDF"):
                print("   [-] Dönen veri PDF formatında değil.")
                continue

            pdf = pdfium.PdfDocument(res.content)
            sayfa_sayisi = len(pdf)
            print(f"   [+] Başarılı! {sayfa_sayisi} sayfa tespit edildi. Görsellere dönüştürülüyor...")

            sayfalar = []
            prefix = "carsamba" if idx == 1 else "haftasonu"

            for s_no, page in enumerate(pdf, 1):
                # scale=2 ile net matbaa çözünürlüğü
                image = page.render(scale=2).to_pil()
                dosya_adi = f"sok_afisler/{prefix}_sayfa_{s_no}.jpg"
                image.save(dosya_adi, "JPEG", quality=92)
                
                sayfalar.append({
                    "sayfa_no": s_no,
                    "dosya_yolu": dosya_adi
                })

            kampanyalar.append({
                "kampanya_adi": adi,
                "kaynak_url": url,
                "toplam_sayfa": sayfa_sayisi,
                "sayfalar": sayfalar
            })
            toplam_sayfa += sayfa_sayisi

        except Exception as e:
            print(f"   [-] İşlem sırasında hata oluştu: {e}")

    veri_paketi = {
        "market": "ŞOK",
        "guncelleme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_kampanya": len(kampanyalar),
        "toplam_afis_sayisi": toplam_sayfa,
        "kampanyalar": kampanyalar
    }

    return veri_paketi

if __name__ == "__main__":
    sonuc = sok_afislerini_cek()

    with open("sok_data.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=4)

    print("\n" + "="*50)
    print("ŞOK TÜM AFİŞLER BAŞARIYLA DÖNÜŞTÜRÜLDÜ")
    print(f"Toplam Kampanya : {sonuc.get('toplam_kampanya', 0)}")
    print(f"Toplam Sayfa    : {sonuc.get('toplam_afis_sayisi', 0)}")
    print("Görseller 'sok_afisler/' klasörüne kaydedildi.")
    print("="*50)
    for k in sonuc.get("kampanyalar", []):
        print(f" • {k['kampanya_adi']:35} -> {k['toplam_sayfa']} Sayfa")
    print("="*50)