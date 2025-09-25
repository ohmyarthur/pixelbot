#!/usr/bin/env python3
import os
import httpx
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
import re
from typing import Optional
import io

class PixeldrainUploader:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=30),
            transport=httpx.HTTPTransport(retries=3, http2=True),
        )

    def upload(self, file_path, chunk_size=1024*1024):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        url = "https://pixeldrain.com/api/file"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        progress = tqdm(
            total=file_size,
            unit='B',
            unit_scale=True,
            desc=f"Uploading {file_name}",
            ncols=100
        )

        class ProgressFileWrapper:
            def __init__(self, fp: io.BufferedReader, progress_bar: tqdm):
                self.fp = fp
                self.progress = progress_bar

            def read(self, amt: Optional[int] = None) -> bytes:
                data = self.fp.read(amt)
                if data:
                    self.progress.update(len(data))
                return data

            def __getattr__(self, name):
                return getattr(self.fp, name)

        try:
            with open(file_path, "rb") as f:
                wrapped_fp = ProgressFileWrapper(f, progress)
                files = {
                    "file": (file_name, wrapped_fp, "application/octet-stream")
                }
                data = {
                    "name": file_name,
                    "anonymous": str(not bool(self.api_key)).lower(),
                }
                response = self.client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            error_msg = f"Upload gagal: {e.response.status_code} - {e.response.text}"
            raise Exception(error_msg) from e
        except Exception as e:
            raise Exception(f"Upload error: {str(e)}") from e
        finally:
            progress.close()

    def _extract_id(self, file_id_or_url: str) -> str:
        text = file_id_or_url.strip()
        m = re.search(r"/u/([A-Za-z0-9_-]{8,})", text)
        if m:
            return m.group(1)
        m = re.search(r"/api/file/([A-Za-z0-9_-]{8,})", text)
        if m:
            return m.group(1)
        return text

    def download(self, file_id_or_url: str, output_path: Optional[str] = None, chunk_size: int = 1024*1024) -> str:
        file_id = self._extract_id(file_id_or_url)
        url = f"https://pixeldrain.com/u/{file_id}?download"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        with self.client.stream("GET", url, headers=headers) as r:
            r.raise_for_status()

            if output_path is None:
                cd = r.headers.get("content-disposition", "")
                m = re.search(r'filename\*=UTF-8\'\'([^\s;]+)', cd)
                if not m:
                    m = re.search(r'filename="?([^";]+)"?', cd)
                if m:
                    output_path = m.group(1)
                else:
                    output_path = f"{file_id}.bin"

            total = int(r.headers.get("content-length", 0)) or None
            progress = tqdm(total=total, unit='B', unit_scale=True, desc=f"Downloading {file_id}", ncols=100)
            try:
                with open(output_path, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress.update(len(chunk))
            finally:
                progress.close()

        return output_path

    def __del__(self):
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Pixeldrain Uploader/Downloader (cepat, streaming)')
    parser.add_argument('path', help='Upload: path file. Download: ID/URL Pixeldrain (gunakan --download)')
    parser.add_argument('-d', '--download', action='store_true', help='Mode download (path dianggap sebagai ID/URL)')
    parser.add_argument('-o', '--output', help='Path output file hasil download (opsional)')
    parser.add_argument('-k', '--api-key', help='Pixeldrain API Key (opsional, override .env)', default=None)
    parser.add_argument('--chunk-size', type=int, default=1024*1024, help='Ukuran chunk (byte) untuk streaming')
    parser.add_argument('--env-file', default=None, help='Path file .env khusus (opsional)')

    args = parser.parse_args()

    if args.env_file and os.path.exists(args.env_file):
        load_dotenv(args.env_file)
    else:
        load_dotenv()

    api_key = args.api_key or os.getenv('PIXELDRAIN_API_KEY')

    try:
        uploader = PixeldrainUploader(api_key=api_key)
        if args.download:
            saved_path = uploader.download(args.path, output_path=args.output, chunk_size=args.chunk_size)
            print("\n✅ Download berhasil!")
            print(f"📁 Tersimpan: {os.path.abspath(saved_path)}")
        else:
            result = uploader.upload(args.path, chunk_size=args.chunk_size)
            print("\n✅ Upload berhasil!")
            print(f"🔗 Link: https://pixeldrain.com/u/{result['id']}")
            print(f"📁 Nama: {result['name']}")
            print(f"📏 Ukuran: {result['size']} bytes")
            if api_key:
                owner = result.get('owner') or result.get('user') or 'N/A'
                print(f"👤 Owner: {owner}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()