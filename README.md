<div align="center">

# Pixelbot • Pixeldrain Uploader/Downloader (CLI)

</div>

## Fitur
- **Upload cepat (streaming multipart)**: hemat memori, HTTP/2, keep-alive, pooling, retries.
- **Download cepat (streaming)**: progress bar berwarna, speed, ETA, ukuran.
- **Batch upload**: upload semua file dalam folder (opsional rekursif).
- **Notifikasi Telegram (Pyrogram)**: pesan HTML dengan tombol (Open/Download) untuk setiap file selesai diupload.
- **.env support**: API key Pixeldrain dan kredensial Telegram melalui environment file.

## Persiapan

1) (Opsional) Buat dan aktifkan virtualenv
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2) Install dependencies
```bash
pip install -r requirements.txt
```

3) Siapkan `.env`
- Salin `.env.example` menjadi `.env`
- Isi nilai minimal Pixeldrain API key jika ingin non-anonim:
```dotenv
PIXELDRAIN_API_KEY=api_key_anda
```

### (Opsional) Aktifkan Notifikasi Telegram
Bot Telegram berfungsi hanya sebagai notifier. Tidak menerima perintah apa pun.

Isi variabel berikut di `.env` agar notifikasi aktif:
```dotenv
TG_API_ID=123456        # dari https://my.telegram.org/apps
TG_API_HASH=xxxxxxxx    # dari https://my.telegram.org/apps
TG_BOT_TOKEN=123:ABC    # dari @BotFather
TG_OWNER_ID=123456789   # user id Telegram (integer), bukan username
```

## Penggunaan

Script utama: `pixel.py`

### Upload 1 file
```bash
python3 pixel.py path/ke/file
```

### Batch Upload (1 folder)
```bash
python3 pixel.py /path/ke/folder

python3 pixel.py /path/ke/folder --recursive
```

### Download (ID atau URL)
```bash
python3 pixel.py --download <ID_atau_URL> [-o output_path]

python3 pixel.py --download abcdef12 -o video.mp4
python3 pixel.py --download https://pixeldrain.com/u/abcdef12
```

### Opsi Lain
- `-k, --api-key`      : Override API key dari CLI.
- `--chunk-size`       : Ukuran chunk (byte) untuk streaming. Default 4 MiB.
- `--env-file`         : Gunakan .env khusus.
- `--no-telegram`      : Nonaktifkan notifikasi Telegram.

Lihat semua opsi:
```bash
python3 pixel.py -h
```

## Catatan Performa
- Upload & download memanfaatkan HTTP/2, connection pooling, dan streaming.
- Naikkan `--chunk-size` untuk throughput yang lebih tinggi pada jaringan cepat (contoh 8–16 MiB).
- Upload multipart streaming: memori tetap rendah meskipun file besar.

## Link & Kontak
- Repo: https://github.com/ohmyarthur/pixelbot
- Telegram: @durovpalsu

## Lisensi
[![AGPLv3](https://camo.githubusercontent.com/16f4518b01f149369b19f7aaf26d77515ddf3382a7868af8337f9ca00b89f25f/68747470733a2f2f7777772e676e752e6f72672f67726170686963732f6167706c76332d3135357835312e706e67)](./LICENSE)

***Pixelbot*** is licensed under **GNU Affero General Public License v3 or later**.

Lihat berkas [LICENSE](./LICENSE) untuk detail lengkap.
