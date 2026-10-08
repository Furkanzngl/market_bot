# Market İndirim Veri Servisi

Bu proje BİM, A101, ŞOK ve Migros kampanya verilerini `data/` altında yayımlar.

## Dayanıklılık

- Kaynak geçici olarak hata verir veya A101 bir GitHub Actions IP'sine `403` dönerse son doğrulanmış JSON korunur; boş cevap asla yayımlanmaz.
- `data/durum.json` her market için son çalıştırmanın sonucunu taşır.
- JSON atomik yazılır; yarım kalan işlem bozuk dosya bırakamaz.
- Workflow yalnızca `data/` dosyalarını commit eder ve açık yazma izni ister.

## Görsel stratejisi

Katalogları indirip JPEG → WebP dönüştürmek iki kez kayıplı sıkıştırma, büyüyen Git geçmişi ve gereksiz trafik üretir. BİM, A101 ve Migros için JSON'da resmi CDN görsel URL'leri verilir; uygulamada `loading="lazy"`, uygun görüntü ölçüsü ve disk/bellek önbelleği kullanılmalıdır. Böylece kaynak kendi optimize boyutunu verir ve kalite ikinci kez kayba uğramaz.

ŞOK PDF'leri yerel arşivlenmek istenirse mevcut WebP üretimi uygundur. Mobil afişler için 75–82 kalite aralığı boyut/netlik açısından iyi dengedir.

## GitHub Actions ve A101 403

GitHub'ın paylaşımlı IP'leri zaman zaman A101 WAF/CDN katmanında engellenir; bunu başlık değiştirerek güvenilir şekilde aşmak doğru ya da kalıcı değildir. Bu akış diğer marketleri günceller, A101'in son çalışan verisini korur ve `durum.json` içine uyarı yazar. Kesintisiz tazelik gerekiyorsa cron'u sabit IP'li kendi sunucunuzda çalıştırıp depoya yetkili anahtarla göndermek gerekir.
