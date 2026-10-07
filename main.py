import time
import os
import json
from datetime import datetime

# Modüllerimizi içe aktarıyoruz
try:
    from bim import bim_afislerini_cek
except ImportError:
    bim_afislerini_cek = None

try:
    from a101 import a101_afislerini_cek
except ImportError:
    a101_afislerini_cek = None

try:
    from sok import sok_afislerini_cek
except ImportError:
    sok_afislerini_cek = None

try:
    from migros import migroskop_urunlerini_cek
except ImportError:
    migroskop_urunlerini_cek = None


def tum_marketleri_guncelle():
    print("=" * 60)
    print(f"MARKET VERİLERİ GÜNCELLEME BAŞLATILDI: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    os.makedirs("data", exist_ok=True)

    # 1. BİM
    if bim_afislerini_cek:
        print("\n[1/4] BİM Aktüel Kataloğu Çekiliyor...")
        try:
            bim_data = bim_afislerini_cek()
            with open("data/bim.json", "w", encoding="utf-8") as f:
                json.dump(bim_data, f, ensure_ascii=False, indent=2)
            print(" -> BİM verisi hazır.")
        except Exception as e:
            print(f" -> BİM hatası: {e}")

    # 2. A101
    if a101_afislerini_cek:
        print("\n[2/4] A101 Afişleri Çekiliyor...")
        try:
            a101_data = a101_afislerini_cek()
            with open("data/a101.json", "w", encoding="utf-8") as f:
                json.dump(a101_data, f, ensure_ascii=False, indent=2)
            print(" -> A101 verisi hazır.")
        except Exception as e:
            print(f" -> A101 hatası: {e}")

    # 3. ŞOK
    if sok_afislerini_cek:
        print("\n[3/4] ŞOK Katalogları Çekiliyor...")
        try:
            sok_data = sok_afislerini_cek()
            with open("data/sok.json", "w", encoding="utf-8") as f:
                json.dump(sok_data, f, ensure_ascii=False, indent=2)
            print(" -> ŞOK verisi hazır.")
        except Exception as e:
            print(f" -> ŞOK hatası: {e}")

    # 4. MİGROS
    if migroskop_urunlerini_cek:
        print("\n[4/4] Migros Migroskop Avantajları Çekiliyor...")
        try:
            migros_data = migroskop_urunlerini_cek()
            with open("data/migros.json", "w", encoding="utf-8") as f:
                json.dump(migros_data, f, ensure_ascii=False, indent=2)
            print(" -> Migros verisi hazır.")
        except Exception as e:
            print(f" -> Migros hatası: {e}")

    print("\n" + "=" * 60)
    print("TÜM MARKET VERİLERİ BAŞARIYLA GÜNCELLENDİ VE 'data/' KLASÖRÜNE KAYDEDİLDİ")
    print("=" * 60)

if __name__ == "__main__":
    tum_marketleri_guncelle()