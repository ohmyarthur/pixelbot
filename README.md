# PixelUploader (Pixeldrain Uploader/Downloader)

1) (Opsional) Buat  dan aktifkan virtualenv
```
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) Siapkan `.env`
- Salin `.env.example` menjadi `.env`
- Isi nilai:
```
PIXELDRAIN_API_KEY=api_key_anda
```

> Jika tidak mengisi API key, upload berjalan sebagai anonymous.

### Upload
```
python3 pixel.py path/ke/file
```
Output akan menampilkan link file dan metadata. Jika `.env` berisi API key maka file akan terasosiasi dengan akun Anda.

### Download (berdasarkan ID atau URL)
```
python3 pixel.py --download <ID_atau_URL> [-o output_path]
```
Contoh:
```
python3 pixel.py --download abcdef12 -o video.mp4
python3 pixel.py --download https://pixeldrain.com/u/abcdef12
```

### Opsi Lain
- `-k, --api-key`: Override API key dari CLI.
- `--chunk-size`: Ukuran chunk (byte) saat download streaming. Default 1048576 (1 MiB).
- `--env-file`: Tentukan file `.env` khusus.

Lihat semua opsi:
```
python3 pixel.py -h
```

## Catatan
- Upload dan download menggunakan HTTP/2, connection pooling, dan streaming.
- Untuk jaringan cepat (LAN/fiber), Anda bisa coba menaikkan `--chunk-size` saat download.
- Upload menggunakan multipart streaming, sehingga penggunaan memori tetap rendah meskipun file besar.
