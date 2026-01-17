import logging
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List

import requests
from requests.adapters import HTTPAdapter


class FastThreadMediaDownloader:
    def __init__(self, limit=1350):
        self.limit = limit
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Pokemon-ETL/1.0"})

        adapter = HTTPAdapter(
            pool_connections=200,
            pool_maxsize=200,
            max_retries=2
        )
        self.session.mount("https://", adapter)

    # -------- STEP 1: GET POKEMON LIST --------
    def get_pokemon_list(self) -> List[str]:
        url = f"https://pokeapi.co/api/v2/pokemon?limit={self.limit}"
        data = self.session.get(url, timeout=10).json()
        return [p["url"] for p in data["results"]]

    # -------- STEP 2: FETCH SPRITES URLS (PARALLEL) --------
    def fetch_sprite_urls(self, pokemon_url: str) -> List[str]:
        data = self.session.get(pokemon_url, timeout=10).json()
        sprites = data.get("sprites", {})
        return self.extract_urls(sprites)

    def extract_urls(self, data) -> List[str]:
        urls = []
        stack = [data]

        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                stack.extend(item.values())
            elif isinstance(item, str) and item.startswith("http"):
                urls.append(item)

        return urls

    # -------- STEP 3: DOWNLOAD FILE --------
    def download_one(self, url: str):
        try:
            h = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{h}_{os.path.basename(url)}"
            path = os.path.join(self.download_dir, filename)

            if os.path.exists(path):
                return path

            r = self.session.get(url, stream=True, timeout=10)
            r.raise_for_status()

            with open(path, "wb") as f:
                for chunk in r.iter_content(16384):
                    f.write(chunk)

            return path
        except Exception:
            return None

    # -------- MAIN RUN --------
    def run(self):
        pokemon_urls = self.get_pokemon_list()

        # 1️⃣ Parallel sprite extraction
        sprite_urls = []
        with ThreadPoolExecutor(max_workers=80) as executor:
            futures = executor.map(self.fetch_sprite_urls, pokemon_urls)
            for urls in futures:
                sprite_urls.extend(urls)
        sprite_urls = list(set(sprite_urls))  # remove duplicates

        print(len(sprite_urls))

        # 2️⃣ Parallel downloads
        with ThreadPoolExecutor(max_workers=100) as executor:
            list(executor.map(self.download_one, sprite_urls))


if __name__ == "__main__":
    print(datetime.now())

    FastThreadMediaDownloader(limit=1350).run()

    print(datetime.now())

    # def download_single(self, url: str, save_folder: str) -> Optional[str]:
    #     if not url or not url.startswith("http"):
    #         return None
    #
    #     url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    #     filename = f"{url_hash}_{os.path.basename(url) or 'file'}"
    #     save_path = os.path.join(save_folder, filename)
    #
    #     if os.path.exists(save_path):
    #         return save_path
    #
    #     try:
    #         response = self.session.get(url, stream=True, timeout=8)
    #         response.raise_for_status()
    #
    #         with open(save_path, "wb") as f:
    #             for chunk in response.iter_content(chunk_size=8192):
    #                 f.write(chunk)
    #         return save_path
    #     except Exception as e:
    #         logger.error(f"Download failed: {url} -> {e}")
    #         return None
    #
    # def download_batch(self, urls: List[str], save_folder: str):
    #     os.makedirs(save_folder, exist_ok=True)
    #
    #     results = []
    #     for url in urls:
    #         results.append(self.download_single(url, save_folder))
    #
    #     successful = [r for r in results if r is not None]
    #     return successful
