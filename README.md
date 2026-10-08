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

## Mobil uygulama: hızlı veri akışı

ViewPager sekmesi açıldığında eski `/api/market/{slug}` ucu yerine önce
`/api/v2/market/{slug}` çağrılmalıdır. Bu uç yalnızca kampanya kartlarını ve
480 px kapak önizlemesini verir. Kullanıcı kampanyayı açtığında
`/api/v2/market/{slug}/campaign/{id}` çağrılır; liste görünümünde
`onizleme_url`, yakınlaştırılmış görünümde `hd_url` kullanılır.

`/api/image/{id}?w=480` ilk istekte resmi 82 kalite WebP olarak sunucuda
önbelleğe alır. Sonraki kullanıcılar ve uygulama disk önbelleği aynı küçük
dosyayı alır; HTTP önbellek ömrü 7 gündür. Görüntü yükleyicide disk cache açık,
liste için 480 px, tam ekran için 1080 px istenmelidir. Migros ürünleri için
`/api/migros/products?offset=0&limit=30` kullanın; bütün ürün listesini tek
istekte indirmeyin.
