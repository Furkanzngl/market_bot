from curl_cffi import requests
import json
import time
from datetime import datetime

# Dikkate alınmayacak, indirimi ifade etmeyen kuru tanıtım rozetleri
YOKSAYILAN_ROZETLER = {
    "GREAT_PRICE", "MIGROSKOP", "PESTICIDE_ANALYZED", "PESTICIDE_FREE",
    "GOOD_AGRICULTURE", "LOCAL_PRODUCT", "BEST_SELLER"
}

def avantaj_analizi_yap(product):
    """
    Ürünün gerçek bir avantajı olup olmadığını inceler.
    Avantaj yoksa (None, None, False) döner ve ürün elenir.
    """
    discount_rate = product.get("discountRate", 0)
    badges = product.get("badges", [])
    
    kampanya_tipi = None
    kampanya_metni = None

    # 1. Rozet bazlı çoklu ve sepet kampanyalarını tara
    for b in badges:
        b_name = b.get("name", "")
        b_val = b.get("value", "").strip()

        # Genel tanıtım rozetlerini atla
        if b_name in YOKSAYILAN_ROZETLER or b_val.lower() in ["iyi fiyat", "migroskop", "pestisit analizli"]:
            continue

        b_val_lower = b_val.lower()

        # Çoklu alım kampanyaları (2 Al 1 Öde, 3 Al 2 Öde vb.)
        if b_name == "CROSS_PROMOTED" or "al " in b_val_lower or "öde" in b_val_lower or "hediye" in b_val_lower:
            kampanya_tipi = "Çoklu Kampanya"
            kampanya_metni = b_val
            break
        # Sepet kampanyaları
        elif "sepette" in b_val_lower:
            kampanya_tipi = "Sepette İndirim"
            kampanya_metni = b_val
            break
        # Money Kart / Fiyat avantajı
        elif b_name == "PRICE_PROMOTED":
            kampanya_tipi = "Fiyat İndirimi"
            kampanya_metni = f"Eski Fiyat: {b_val}"
            break
        elif b_val:
            kampanya_tipi = "Özel Kampanya"
            kampanya_metni = b_val
            break

    # 2. Doğrudan fiyat indirimi varsa
    if discount_rate > 0:
        if not kampanya_tipi:
            kampanya_tipi = "Fiyat İndirimi"
            kampanya_metni = f"%{discount_rate} İndirim"
        return kampanya_tipi, kampanya_metni, True

    # 3. İndirim oranı %0 ama kampanya rozeti yakalandıysa (Örn: 2 Al 1 Öde)
    if kampanya_tipi:
        return kampanya_tipi, kampanya_metni, True

    # 4. Hiçbir avantaj yok -> DIŞLA
    return None, None, False

def migroskop_urunlerini_cek():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Referer": "https://www.migros.com.tr/migroskop-urunleri-dt-3",
        "x-forwarded-rest": "true"
    }

    session = requests.Session(impersonate="chrome120")
    pdf_url = "https://moneyclubkart.azureedge.net/mcstage/907-24-eylul-7-ekim-migroskop-639259551466403073.pdf"

    print("1. Migroskop kampanya verisi taranıyor...")
    ilk_url = "https://www.migros.com.tr/rest/search/screens/migroskop-urunleri-dt-3?sayfa=1"
    
    try:
        res = session.get(ilk_url, headers=headers)
        ana_veri = res.json()
    except Exception as e:
        print(f"[-] API Hatası: {e}")
        return {}

    search_info = ana_veri.get("data", {}).get("searchInfo", {})
    hedef_hit_count = search_info.get("hitCount", 0)
    print(f"[+] Taranacak Toplam Ham Ürün: {hedef_hit_count}")

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
    elenen_indirimsiz_idler = set()  # Tekil ID bazlı takip

    def urun_isle(urunler):
        for u in urunler:
            u_id = u.get("id")
            # Daha önce avantajlı olarak eklenmiş veya elenmiş tekil ürünleri tekrar işleme
            if not u_id or u_id in tum_avantajli_urunler or u_id in elenen_indirimsiz_idler:
                continue

            kampanya_tipi, kampanya_metni, gecerli_avantaj = avantaj_analizi_yap(u)
            
            # Gerçek avantajı olmayan tekil ürünü elenenler kümesine at
            if not gecerli_avantaj:
                elenen_indirimsiz_idler.add(u_id)
                continue

            ascendants = u.get("categoryAscendants", [])
            if ascendants:
                reyon_adi = ascendants[-1].get("name", "Diğer")
                alt_kategori = ascendants[0].get("name", reyon_adi)
            else:
                reyon_adi = u.get("category", {}).get("name", "Genel Fırsatlar")
                alt_kategori = reyon_adi

            gorseller = u.get("images", [])
            hd_resim = ""
            if gorseller and "urls" in gorseller[0]:
                hd_resim = gorseller[0]["urls"].get("PRODUCT_HD") or gorseller[0]["urls"].get("PRODUCT_DETAIL", "")

            tum_avantajli_urunler[u_id] = {
                "id": u_id,
                "urun_adi": u.get("name"),
                "marka": u.get("brand", {}).get("name", ""),
                "ana_kategori": reyon_adi,
                "alt_kategori": alt_kategori,
                "normal_fiyat": u.get("regularPrice", 0) / 100,
                "indirimli_fiyat": u.get("shownPrice", 0) / 100,
                "indirim_orani": f"%{u.get('discountRate', 0)}",
                "kampanya_tipi": kampanya_tipi,
                "kampanya_metni": kampanya_metni,
                "birim_fiyat": u.get("unitPrice", ""),
                "gorsel_hd": hd_resim
            }

    for kanal in dinamik_kanallar:
        ad = kanal["ad"]
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

    # Kategori gruplama (Sadece avantajı olan ürünlerle)
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
        "kampanya_adi": "Dijital Migroskop Fırsatları",
        "orijinal_pdf_katalog": pdf_url,
        "guncelleme_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "toplam_gecerli_avantaj": len(tum_avantajli_urunler),
        "elenen_indirimsiz_urun": len(elenen_indirimsiz_idler),
        "toplam_islenen_tekil_urun": len(tum_avantajli_urunler) + len(elenen_indirimsiz_idler),
        "kategori_sayisi": len(kategori_listesi),
        "kategoriler": kategori_listesi
    }

    return veri_paketi

if __name__ == "__main__":
    sonuc = migroskop_urunlerini_cek()

    with open("migros_data.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=4)

    print("\n" + "="*50)
    print("MİGROSKOP GERÇEK AVANTAJ LİSTESİ TAMAMLANDI")
    print(f"Toplam Geçerli Avantajlı Ürün : {sonuc.get('toplam_gecerli_avantaj', 0)}")
    print(f"Dışlanan İndirimsiz Tekil Ürün: {sonuc.get('elenen_indirimsiz_urun', 0)}")
    print(f"Toplam İşlenen Tekil Havuz    : {sonuc.get('toplam_islenen_tekil_urun', 0)}")
    print(f"Aktif Kategori Sayısı         : {sonuc.get('kategori_sayisi', 0)}")
    print("="*50)
    for k in sonuc.get("kategoriler", [])[:10]:
        print(f" • {k['kategori_adi']:30} : {k['urun_sayisi']} fırsat ürünü")
    print("="*50)