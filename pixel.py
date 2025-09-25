#!/usr/bin/env python3
import os
import httpx
import argparse
from tqdm import tqdm

class PixeldrainUploader:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
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

        def progress_wrapper(data):
            progress.update(len(data))
            return data

        try:
            with open(file_path, "rb") as f:
                files = {
                    "file": (file_name, progress_wrapper(f.read()), "application/octet-stream")
                }
                data = {
                    "name": file_name,
                    "anonymous": str(not bool(self.api_key)).lower()
                }

                response = self.client.post(
                    url,
                    headers=headers,
                    files=files,
                    data=data
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

    def __del__(self):
        self.client.close()

def main():
    parser = argparse.ArgumentParser(description='Pixeldrain File Uploader')
    parser.add_argument('file_path', help='Path file yang akan diupload')
    parser.add_argument('-k', '--api-key', help='Pixeldrain API Key (opsional)', default=None)
    
    args = parser.parse_args()
    
    try:
        uploader = PixeldrainUploader(api_key=args.api_key)
        result = uploader.upload(args.file_path)
        
        print("\n✅ Upload berhasil!")
        print(f"🔗 Link: https://pixeldrain.com/u/{result['id']}")
        print(f"📁 Nama: {result['name']}")
        print(f"📏 Ukuran: {result['size']} bytes")
        
        if args.api_key:
            print(f"👤 Owner: {result.get('owner', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()