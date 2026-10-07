from curl_cffi import requests
import json
import time
from datetime import datetime

YOKSAYILAN_ROZETLER = {
    "GREAT_PRICE", "MIGROSKOP", "PESTICIDE_ANALYZED", "PESTICIDE_FREE",
    "GOOD_AGRICULTURE", "LOCAL_PRODUCT", "BEST_SELLER"
}

def avantaj_analizi_yap(product):
    discount_rate = product.get("discountRate", 0)
    badges = product.get("badges", [])
    
    kampanya_tipi = None

    for b in badges:
        b_name = b.get("name", "")
        b_val = b.get("value", "").strip()

        if b_name in YOKSAYILAN_ROZETLER or b_val.lower() in ["iyi fiyat", "migroskop", "pestisit analizli"]:
            continue

        b_val_lower = b_val.lower()

        if b_name == "CROSS_PROMOTED" or "al " in b_val_lower or "öde" in b_val_lower or "hediye" in b_val_lower:
            kampanya_tipi = "Çoklu Kampanya"
            break
        elif "sepette" in b_val_lower:
            kampanya_tipi = "Sepette İndirim"
            break
        elif b_name == "PRICE_PROMOTED":
            kampanya_tipi = "Fiyat İndirimi"
            break
        elif b_val:
            kampanya_tipi = "Özel Kampanya"
            break

    if discount_rate > 0 or kampanya_tipi:
        return True

    return False

def migroskop_urunlerini_cek():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://www.migros.com.tr/migroskop-urunleri-dt-3",
        "x-forwarded-rest": "true"
    }

    session = requests.Session(impersonate="chrome120")
    print("Migroskop kampanya verisi taranıyor...")
    ilk_url = "https://www.migros.com.tr/rest/search/screens/migroskop-urunleri-dt-3?sayfa=1"
    
    try:
        res = session.get(ilk_url, headers=headers)
        ana_veri = res.json()
    except Exception as e:
        print(f"[-] API Hatası: {e}")
        return {}

    search_info = ana_veri.get("data", {}).get("searchInfo", {})
    dinamik_kanallar = [{"ad": "Ana Havuz", "param": ""}]
    
    for grup in search_info.get("aggregationGroups", []):
        if grup.get("type") in ["CATEGORY", "DISCOUNT"]:
            param_key = "kategori" if grup.get("type") == "CATEGORY" else "indirim"
            for info in grup.get("aggregationInfos", []):
                dinamik_kanallar.append({
                    "ad": info.get("label"),
                    "param": f"&{param_key}={info.get('id')}"
                })

    tum_avantajli_urunler = {}
    elenen_indirimsiz_idler = set()

    def urun_isle(urunler):
        for u in urunler:
            u_id = u.get("id")
            if not u_id or u_id in tum_avantajli_urunler or u_id in elenen_indirimsiz_idler:
                continue

            if not avantaj_analizi_yap(u):
                elenen_indirimsiz_idler.add(u_id)
                continue

            ascendants = u.get("categoryAscendants", [])
            reyon_adi = ascendants[-1].get("name", "Diğer") if ascendants else u.get("category", {}).get("name", "Genel Fırsatlar")

            gorseller = u.get("images", [])
            resim_url = ""
            if gorseller and "urls" in gorseller[0]:
                urls = gorseller[0]["urls"]
                # 1650x1650 yerine mobil veri tasarrufu için PRODUCT_DETAIL alıyoruz
                resim_url = urls.get("PRODUCT_DETAIL") or urls.get("PRODUCT_HD", "")

            rate = u.get("discountRate", 0)
            tum_avantajli_urunler[u_id] = {
                "urun_adi": u.get("name"),
                "ana_kategori": reyon_adi,
                "normal_fiyat": u.get("regularPrice", 0) / 100,
                "indirimli_fiyat": u.get("shownPrice", 0) / 100,
                "indirim_orani": f"%{rate}" if rate > 0 else None,
                "gorsel_hd": resim_url
            }

    for kanal in dinamik_kanallar:
        ek_param = kanal["param"]
        sayfa = 1

        while True:
            url = f"https://www.migros.com.tr/rest/search/screens/migroskop-urunleri-dt-3?sayfa={sayfa}{ek_param}"
            try:
                p_res = session.get(url, headers=headers)
                if p_res.status_code != 200:
                    break

                p_veri = p_res.json()
                p_search = p_veri.get("data", {}).get("searchInfo", {})
                urunler = p_search.get("storeProductInfos", [])
                max_sayfa = p_search.get("pageCount", 1)

                if not urunler:
                    break

                urun_isle(urunler)
                if sayfa >= max_sayfa:
                    break

                sayfa += 1
                time.sleep(0.08)
            except Exception:
                break

    kategori_gruplari = {}
    for urun in tum_avantajli_urunler.values():
        kat = urun["ana_kategori"]
        if kat not in kategori_gruplari:
            kategori_gruplari[kat] = []
        kategori_gruplari[kat].append(urun)

    kategori_listesi = [
        {
            "kategori_adi": kat_adi,
            "urun_sayisi": len(urunler),
            "urunler": urunler
        }
        for kat_adi, urunler in sorted(kategori_gruplari.items(), key=lambda x: len(x[1]), reverse=True)
    ]

    veri_paketi = {
        "market": "Migros",
        "guncelleme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_gecerli_avantaj": len(tum_avantajli_urunler),
        "kategori_sayisi": len(kategori_listesi),
        "kategoriler": kategori_listesi
    }

    return veri_paketi

if __name__ == "__main__":
    sonuc = migroskop_urunlerini_cek()

    with open("migros_data.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, separators=(',', ':'))

    print("\n" + "="*50)
    print("MİGROS AVANTAJ LİSTESİ SIKIŞTIRILDI")
    print(f"Toplam Fırsat Ürünü: {sonuc.get('toplam_gecerli_avantaj', 0)}")
    print("="*50)