# Shopee Live Assistant Pro

Aplikasi otomatisasi untuk Shopee Live dengan fitur multi-session dan antarmuka grafis.

## Fitur

- Multi-session support
- Antarmuka grafis dengan PyQt5
- Rate limiting untuk mencegah pemblokiran
- Mendukung aksi:
  - Pengiriman pesan
  - Aksi beli
  - Aksi follow
  - Aksi like
- Manajemen cookies otomatis
- Statistik real-time
- Penyimpanan konfigurasi

## Persyaratan

```bash
pip install -r requirements.txt
```

## Penggunaan

1. Clone repository:
```bash
git clone https://github.com/username/shopee-live-assistant.git
cd shopee-live-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Jalankan aplikasi:
```bash
python shopee_live_gui.py
```

## Konfigurasi

- Cookies disimpan di file `cookies.txt`
- Konfigurasi sesi disimpan di `config.json`
- Rate limiting: 5 request per detik

## Kontribusi

Silakan berkontribusi dengan membuat pull request atau melaporkan issues.

## Lisensi

MIT License 