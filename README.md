<div align="center">

# Pixelbot • Pixeldrain Uploader/Downloader (CLI)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-AGPLv3-green)](./LICENSE)

</div>

---

## Fitur

* **Upload cepat (streaming multipart)**: hemat memori, HTTP/2, keep-alive, connection pooling, retries otomatis.
* **Download cepat (streaming)**: progress bar berwarna, speed, ETA, ukuran file.
* **Batch upload**: upload semua file dalam folder, opsional rekursif.
* **Notifikasi Telegram (Pyrogram)**: pesan HTML dengan tombol (Open/Download) setiap file selesai diupload.
* **.env support**: API key Pixeldrain & kredensial Telegram melalui environment file.

---

## Persiapan

1. (Opsional) Buat dan aktifkan virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Siapkan `.env`

* Salin `.env.example` menjadi `.env`
* Isi minimal Pixeldrain API key (untuk non-anonim):

```dotenv
PIXELDRAIN_API_KEY=api_key_anda
```

### (Opsional) Aktifkan Notifikasi Telegram

Bot Telegram hanya berfungsi sebagai notifier. Tidak menerima perintah.

Isi variabel di `.env` agar notifikasi aktif:

```dotenv
TG_API_ID=123456        # dari https://my.telegram.org/apps
TG_API_HASH=xxxxxxxx    # dari https://my.telegram.org/apps
TG_BOT_TOKEN=123:ABC    # dari @BotFather
TG_OWNER_ID=123456789   # user id Telegram (integer), bukan username
TG_NOTIFY=True          # Aktifkan notifikasi
```

---

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

| Opsi            | Deskripsi                                          |
| --------------- | -------------------------------------------------- |
| `-k, --api-key` | Override API key dari CLI                          |
| `--chunk-size`  | Ukuran chunk (byte) untuk streaming. Default 4 MiB |
| `--env-file`    | Gunakan file `.env` khusus                         |
| `--no-telegram` | Nonaktifkan notifikasi Telegram                    |

Lihat semua opsi:

```bash
python3 pixel.py -h
```

---

## Catatan Performa

* Upload & download memanfaatkan HTTP/2, connection pooling, dan streaming.
* Naikkan `--chunk-size` untuk throughput lebih tinggi pada jaringan cepat (misal 8–16 MiB).
* Upload multipart streaming menjaga memori tetap rendah meskipun file besar.

---

## Link & Kontak

* Repo: [https://github.com/ohmyarthur/pixelbot](https://github.com/ohmyarthur/pixelbot)
* Telegram: [@durovpalsu](https://t.me/durovpalsu)

---

## Lisensi

[![AGPLv3](https://img.shields.io/badge/license-AGPLv3-blue)](./LICENSE)

***Pixelbot*** is licensed under **GNU Affero General Public License v3 or later**.
Lihat berkas [LICENSE](./LICENSE) untuk detail lengkap.
