#!/usr/bin/env python3
# Pixelbot 
# Copyright (C) 2025 Moeamore
#
# This file is a part of < https://github.com/ohmyarthur/pixelbot
#>
# Please read the GNU Affero General Public License in order to use this project.
# <https://www.github.com/ohmyarthur/pixelbot/blob/main/LICENSE/>.


import os
import httpx
import argparse
from dotenv import load_dotenv
import re
from typing import Optional
import io
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
    DownloadColumn,
)
import html
from pyrogram import Client, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

console = Console()


def parse_bool_env(value: Optional[str], default: bool = True) -> bool:
    if value is None or value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


class PixeldrainUploader:
    def __init__(self, api_key=None):
        self.api_key = api_key
        default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
            )
        }
        auth = httpx.BasicAuth("", self.api_key) if self.api_key else None

        self.client = httpx.Client(
            http2=True,
            timeout=httpx.Timeout(60.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=30),
            transport=httpx.HTTPTransport(retries=3, http2=True),
            headers=default_headers,
            auth=auth,
        )

    def upload(self, file_path, chunk_size=1024*1024):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        url = "https://pixeldrain.com/api/file"

        columns = [
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=None),
            DownloadColumn(binary_units=True),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ]

        class ProgressFileWrapper:
            def __init__(self, fp: io.BufferedReader, progress_obj: Progress, task_id, chunk_size: int):
                self.fp = fp
                self.progress = progress_obj
                self.task_id = task_id
                self.chunk_size = chunk_size
            def read(self, amt: Optional[int] = None) -> bytes:
                if amt is None or amt <= 0:
                    amt = self.chunk_size
                data = self.fp.read(amt)
                if data:
                    self.progress.update(self.task_id, advance=len(data))
                return data
            def readinto(self, b) -> int:
                n = self.fp.readinto(b)
                if n and n > 0:
                    self.progress.update(self.task_id, advance=n)
                return n
            def __getattr__(self, name):
                return getattr(self.fp, name)

        try:
            with Progress(*columns, console=console, transient=True) as progress:
                task = progress.add_task(f"Uploading {file_name}", total=file_size)
                with open(file_path, "rb", buffering=chunk_size) as f:
                    wrapped_fp = ProgressFileWrapper(f, progress, task, chunk_size)
                    files = {
                        "file": (file_name, wrapped_fp, "application/octet-stream")
                    }
                    data = {
                        "name": file_name,
                        "anonymous": str(not bool(self.api_key)).lower(),
                    }
                    response = self.client.post(
                        url,
                        headers={"Expect": "100-continue"},
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

        with self.client.stream("GET", url) as r:
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

            columns = [
                SpinnerColumn(spinner_name="dots"),
                TextColumn("[bold green]Downloading {task.fields[file_id]}"),
                BarColumn(bar_width=None),
                DownloadColumn(binary_units=True),
                TransferSpeedColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
            ]

            with Progress(*columns, console=console, transient=True) as progress:
                task = progress.add_task("download", total=total, file_id=file_id)
                with open(output_path, "wb") as f:
                    for chunk in r.iter_bytes(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

        return output_path

    def __del__(self):
        self.client.close()


def format_size(num: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024.0


class TelegramNotifier:
    """Notifier Telegram menggunakan Pyrogram.
    Hanya mengirim pesan ke OWNER_ID dan tidak menerima perintah (notifier only).
    """

    def __init__(self, api_id: Optional[int], api_hash: Optional[str], bot_token: Optional[str], owner_id: Optional[int]):
        self.api_id = api_id
        self.api_hash = api_hash
        self.bot_token = bot_token
        self.owner_id = owner_id
        self.app: Optional[Client] = None
        self.enabled = bool(self.api_id and self.api_hash and self.bot_token and self.owner_id)

    @classmethod
    def from_env(cls, disable: bool = False) -> "TelegramNotifier":
        if disable:
            return cls(None, None, None, None)
        enabled_flag = parse_bool_env(os.getenv("TG_NOTIFY"), default=True)
        if not enabled_flag:
            return cls(None, None, None, None)
        api_id = os.getenv("TG_API_ID")
        api_hash = os.getenv("TG_API_HASH")
        bot_token = os.getenv("TG_BOT_TOKEN")
        owner_id = os.getenv("TG_OWNER_ID")
        try:
            api_id_i = int(api_id) if api_id else None
            owner_id_i = int(owner_id) if owner_id else None
        except ValueError:
            api_id_i, owner_id_i = None, None
        return cls(api_id_i, api_hash, bot_token, owner_id_i)

    def start(self):
        if not self.enabled or self.app is not None:
            return
        self.app = Client(
            name="pixelbot_notifier",
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.bot_token,
            in_memory=True,
        )
        self.app.start()

    def stop(self):
        if self.app is not None:
            self.app.stop()
            self.app = None

    def notify_upload(self, file_name: str, size_bytes: int, file_id: str):
        if not self.enabled or self.app is None or not self.owner_id:
            return
        safe_name = html.escape(file_name)
        size_h = format_size(size_bytes)
        link_view = f"https://pixeldrain.com/u/{file_id}"
        link_dl = f"https://pixeldrain.com/u/{file_id}?download"

        message = (
            f"<blockquote><b>PixelUploader</b> <i>Upload Selesai</i></blockquote>\n"
            f"<b>Judul:</b> <code>{safe_name}</code>\n"
            f"<b>Ukuran:</b> {size_h}\n"
            f"<b>Link:</b> {link_view}"
        )

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 Open", url=link_view),
                InlineKeyboardButton("⬇️ Download", url=link_dl),
            ]
        ])

        try:
            self.app.send_message(
                chat_id=self.owner_id,
                text=message,
                parse_mode=enums.ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=buttons,
            )
        except Exception as e:
            console.print(f"[yellow]Gagal mengirim notifikasi Telegram:[/] {e}")

def main():
    parser = argparse.ArgumentParser(description='Pixeldrain Uploader/Downloader (cepat, streaming)')
    parser.add_argument('path', help='Upload: path file/Folder. Download: ID/URL Pixeldrain (gunakan --download)')
    parser.add_argument('-d', '--download', action='store_true', help='Mode download (path dianggap sebagai ID/URL)')
    parser.add_argument('-o', '--output', help='Path output file hasil download (opsional)')
    parser.add_argument('-k', '--api-key', help='Pixeldrain API Key (opsional, override .env)', default=None)
    parser.add_argument('--chunk-size', type=int, default=4*1024*1024, help='Ukuran chunk (byte) untuk streaming')
    parser.add_argument('--env-file', default=None, help='Path file .env khusus (opsional)')
    parser.add_argument('--recursive', action='store_true', help='Batch upload folder secara rekursif')
    parser.add_argument('--no-telegram', action='store_true', help='Nonaktifkan notifikasi Telegram (jika .env di-set)')

    args = parser.parse_args()

    if args.env_file and os.path.exists(args.env_file):
        load_dotenv(args.env_file)
    else:
        load_dotenv()

    api_key = args.api_key or os.getenv('PIXELDRAIN_API_KEY')

    try:
        uploader = PixeldrainUploader(api_key=api_key)
        notifier = TelegramNotifier.from_env(disable=args.no_telegram)
        if notifier.enabled:
            notifier.start()
        if args.download:
            saved_path = uploader.download(args.path, output_path=args.output, chunk_size=args.chunk_size)
            console.print("\n✅ [bold green]Download berhasil![/]", highlight=False)
            console.print(f"📁 Tersimpan: [bold]{os.path.abspath(saved_path)}[/]", highlight=False)
        else:
            if os.path.isdir(args.path):
                files = []
                if args.recursive:
                    for root, _, names in os.walk(args.path):
                        for nm in names:
                            fp = os.path.join(root, nm)
                            if os.path.isfile(fp):
                                files.append(fp)
                else:
                    for nm in os.listdir(args.path):
                        fp = os.path.join(args.path, nm)
                        if os.path.isfile(fp):
                            files.append(fp)

                ok = 0
                fail = 0
                for fpath in files:
                    try:
                        result = uploader.upload(fpath, chunk_size=args.chunk_size)
                        file_id = result.get('id') if isinstance(result, dict) else None
                        name_display = (result.get('name') if isinstance(result, dict) else None) or os.path.basename(fpath)
                        raw_size = result.get('size') if isinstance(result, dict) else None
                        try:
                            size_b = int(raw_size)
                        except (TypeError, ValueError):
                            size_b = os.path.getsize(fpath)
                        size_h = format_size(size_b)

                        console.print("\n✅ [bold green]Upload berhasil![/]", highlight=False)
                        if file_id:
                            console.print(f"🔗 Link: [bold cyan]https://pixeldrain.com/u/{file_id}[/]", highlight=False)
                        console.print(f"📁 Nama: [bold]{name_display}[/]", highlight=False)
                        console.print(f"📏 Ukuran: [bold]{size_h}[/] ({size_b} bytes)", highlight=False)

                        if notifier.enabled and file_id:
                            notifier.notify_upload(name_display, size_b, file_id)
                        ok += 1
                    except Exception as e:
                        console.print(f"\n❌ [bold red]Error upload:[/] {fpath}: {e}")
                        fail += 1
                console.print(f"\n[bold]Ringkasan:[/] Berhasil: {ok} | Gagal: {fail}")
            else:
                result = uploader.upload(args.path, chunk_size=args.chunk_size)
                file_id = result.get('id') if isinstance(result, dict) else None
                name_display = (result.get('name') if isinstance(result, dict) else None) or os.path.basename(args.path)
                raw_size = result.get('size') if isinstance(result, dict) else None
                try:
                    size_b = int(raw_size)
                except (TypeError, ValueError):
                    size_b = os.path.getsize(args.path)
                size_h = format_size(size_b)

                console.print("\n✅ [bold green]Upload berhasil![/]", highlight=False)
                if file_id:
                    console.print(f"🔗 Link: [bold cyan]https://pixeldrain.com/u/{file_id}[/]", highlight=False)
                console.print(f"📁 Nama: [bold]{name_display}[/]", highlight=False)
                console.print(f"📏 Ukuran: [bold]{size_h}[/] ({size_b} bytes)", highlight=False)

                if notifier.enabled and file_id:
                    notifier.notify_upload(name_display, size_b, file_id)
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/] {str(e)}")
        exit(1)
    finally:
        try:
            if 'notifier' in locals() and notifier.enabled:
                notifier.stop()
        except Exception:
            pass

if __name__ == "__main__":
    main()