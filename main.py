import os
from datetime import datetime
from fetch_utils import atomic_write_json, has_usable_payload, utc_now

# 1. BİM
try:
    from bim import bim_temiz_veri_cek as bim_cek
except Exception as e:
    print(f"BİM İçe Aktarma Hatası: {e}")
    bim_cek = None

# 2. A101
try:
    from a101 import a101_tum_kataloglari_cek as a101_cek
except ImportError:
    a101_cek = None

# 3. ŞOK
try:
    from sok import sok_afislerini_cek as sok_cek
except ImportError:
    sok_cek = None

# 4. MİGROS
try:
    from migros import migroskop_urunlerini_cek as migros_cek
except ImportError:
    migros_cek = None


def _kaydet_ve_durum_yaz(market, veri, durumlar):
    """Never let an empty upstream result overwrite usable saved data."""
    if has_usable_payload(veri):
        atomic_write_json(f"data/{market}.json", veri)
        durumlar[market] = {"durum": "ok", "guncelleme_zamani_utc": utc_now()}
        print(f" -> {market.upper()} verisi hazır.")
        return
    durumlar[market] = {"durum": "korundu", "neden": "Kaynak boş/geçersiz veri döndürdü; son çalışan veri korunuyor.", "guncelleme_zamani_utc": utc_now()}
    print(f" -> {market.upper()} boş veri döndürdü; mevcut dosya korundu.")


def tum_marketleri_guncelle():
    print("=" * 60)
    print(f"MARKET VERİLERİ GÜNCELLEME BAŞLATILDI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)
    durumlar = {}

    # 1. BİM
    if bim_cek:
        print("\n[1/4] BİM Aktüel Kataloğu Çekiliyor...")
        try:
            bim_data = bim_cek()
            _kaydet_ve_durum_yaz("bim", bim_data, durumlar)
        except Exception as e:
            print(f" -> BİM hatası: {e}")
            durumlar["bim"] = {"durum": "korundu", "neden": str(e), "guncelleme_zamani_utc": utc_now()}
    else:
        print("\n[1/4] BİM modülü bulunamadı, atlandı.")

    # 2. A101
    if a101_cek:
        print("\n[2/4] A101 Afişleri Çekiliyor...")
        try:
            a101_data = a101_cek()
            _kaydet_ve_durum_yaz("a101", a101_data, durumlar)
        except Exception as e:
            print(f" -> A101 hatası: {e}")
            durumlar["a101"] = {"durum": "korundu", "neden": str(e), "guncelleme_zamani_utc": utc_now()}
    else:
        print("\n[2/4] A101 modülü bulunamadı, atlandı.")

    # 3. ŞOK
    if sok_cek:
        print("\n[3/4] ŞOK Katalogları Çekiliyor...")
        try:
            sok_data = sok_cek()
            _kaydet_ve_durum_yaz("sok", sok_data, durumlar)
        except Exception as e:
            print(f" -> ŞOK hatası: {e}")
            durumlar["sok"] = {"durum": "korundu", "neden": str(e), "guncelleme_zamani_utc": utc_now()}
    else:
        print("\n[3/4] ŞOK modülü bulunamadı, atlandı.")

    # 4. MİGROS
    if migros_cek:
        print("\n[4/4] Migros Migroskop Avantajları Çekiliyor...")
        try:
            migros_data = migros_cek()
            _kaydet_ve_durum_yaz("migros", migros_data, durumlar)
        except Exception as e:
            print(f" -> Migros hatası: {e}")
            durumlar["migros"] = {"durum": "korundu", "neden": str(e), "guncelleme_zamani_utc": utc_now()}

    else:
        print("\n[4/4] Migros modülü bulunamadı, atlandı.")

    atomic_write_json("data/durum.json", {"guncelleme_zamani_utc": utc_now(), "marketler": durumlar})

    print("\n" + "=" * 60)
    print("TÜM MARKET VERİLERİ SIKIŞTIRILARAK 'data/' KLASÖRÜNE KAYDEDİLDİ")
    print("=" * 60)

if __name__ == "__main__":
    tum_marketleri_guncelle()
