from curl_cffi import requests

session = requests.Session(impersonate="chrome120")
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "accept-language": "tr-TR,tr;q=0.9"
}

# Doğrudan web sitesi (API değil!)
res = session.get("https://www.a101.com.tr/afisler", headers=headers, timeout=15)
print("A101 Web Sitesi Yanıt Kodu:", res.status_code)
print("İçerik Uzunluğu:", len(res.text))
if "Mh6LZTkQmmuWjukh" in res.text or "afis" in res.text.lower():
    print("[+] Harika! Web sitesi içeriği GitHub'da engelsiz açılıyor!")
else:
    print("[-] Sayfa açıldı ama afiş içeriği farklı formatta.")