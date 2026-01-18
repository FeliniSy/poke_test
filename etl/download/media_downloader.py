import logging
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from datetime import datetime
from typing import List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter


class MediaDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Pokemon-ETL/1.0"})
        adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def download_single(self, url: str, save_folder: str) -> Optional[str]:
        if not url or not url.startswith("http"):
            return None

        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        filename = f"{url_hash}_{os.path.basename(url) or 'file'}"
        save_path = os.path.join(save_folder, filename)

        if os.path.exists(save_path):
            return save_path

        try:
            response = self.session.get(url, stream=True, timeout=8)
            response.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path
        except Exception:
            return None

    # def download_batch(self, urls: List[str], save_folder: str) -> List[str]:
    #     os.makedirs(save_folder, exist_ok=True)
    #
    #     results = []
    #     for url in urls:
    #         results.append(self.download_single(url, save_folder))
    #
    #     return [r for r in results if r is not None]


class FastThreadMediaDownloader:
    def __init__(
        self,
        limit=1350,
        fetch_workers: int = 40,
        download_workers: int = 200,
        chunk_size: int = 65536,
    ):
        self.limit = limit
        self.fetch_workers = fetch_workers
        self.download_workers = download_workers
        self.chunk_size = chunk_size
        self._seen_urls = set()
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Pokemon-ETL/1.0"})

        adapter = HTTPAdapter(
            pool_connections=400,
            pool_maxsize=400,
            max_retries=2,
            pool_block=True,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # -------- STEP 1: GET POKEMON LIST --------
    def get_pokemon_list(self) -> List[str]:
        url = f"https://pokeapi.co/api/v2/pokemon?limit={self.limit}"
        data = self.session.get(url, timeout=10).json()
        return [p["url"] for p in data["results"]]

    # -------- STEP 2: FETCH SPRITES URLS (PARALLEL) --------
    def fetch_sprite_urls(self, pokemon_url: str) -> tuple[str, List[Tuple[str, str]]]:
        data = self.session.get(pokemon_url, timeout=10).json()
        sprites = data.get("sprites", {})
        name = data.get("name", "unknown")
        return name, self.extract_urls(sprites)

    def extract_urls(self, data, prefix: str = "") -> List[Tuple[str, str]]:
        urls: List[Tuple[str, str]] = []
        if isinstance(data, dict):
            for key, value in data.items():
                next_prefix = f"{prefix}_{key}" if prefix else key
                urls.extend(self.extract_urls(value, next_prefix))
        elif isinstance(data, str) and data.startswith("http"):
            urls.append((prefix or "sprite", data))
        return urls

    # -------- STEP 3: DOWNLOAD FILE --------
    def download_one(self, url: str, folder_path: str, sprite_key: str, pokemon_name: str):
        try:
            ext = os.path.splitext(url)[1] or ".png"
            safe_key = sprite_key.replace("/", "_")
            filename = f"{safe_key}_{pokemon_name}{ext}"
            full_path = os.path.join(folder_path, filename)

            if os.path.exists(full_path):
                return full_path

            r = self.session.get(url, stream=True, timeout=10)
            r.raise_for_status()

            with open(full_path, "wb") as f:
                for chunk in r.iter_content(self.chunk_size):
                    if chunk:
                        f.write(chunk)

            return full_path
        except Exception:
            return None

    # -------- MAIN RUN --------
    def run(self):
        pokemon_urls = self.get_pokemon_list()
        download_futures = []
        max_in_flight = max(1, self.download_workers * 4)

        # 1️⃣ Parallel sprite extraction -> 2️⃣ Pipeline downloads
        with ThreadPoolExecutor(max_workers=self.fetch_workers) as fetch_pool, ThreadPoolExecutor(
            max_workers=self.download_workers
        ) as download_pool:
            futures = fetch_pool.map(self.fetch_sprite_urls, pokemon_urls)
            for name, sprite_items in futures:
                if not sprite_items:
                    continue
                folder_path = os.path.join(self.download_dir, name)
                os.makedirs(folder_path, exist_ok=True)
                for sprite_key, url in sprite_items:
                    if url in self._seen_urls:
                        continue
                    self._seen_urls.add(url)
                    download_futures.append(
                        download_pool.submit(self.download_one, url, folder_path, sprite_key, name)
                    )
                    if len(download_futures) >= max_in_flight:
                        _, download_futures = wait(download_futures, return_when=FIRST_COMPLETED)
                        download_futures = list(download_futures)

            for future in as_completed(download_futures):
                _ = future.result()


if __name__ == "__main__":
    start = datetime.now()

    FastThreadMediaDownloader(limit=135).run()

    print(datetime.now() - start)
