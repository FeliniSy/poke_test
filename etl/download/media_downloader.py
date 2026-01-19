import os
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from datetime import datetime
from typing import List, Optional, Tuple
import threading

import requests
from requests.adapters import HTTPAdapter


class FastThreadMediaDownloader:
    def __init__(
            self,
            limit=1325,
            fetch_workers: int = 60,
            download_workers: int = 250,
            form_workers: int = 40,
            chunk_size: int = 65536,
    ):
        self.limit = limit
        self.fetch_workers = fetch_workers
        self.download_workers = download_workers
        self.form_workers = form_workers
        self.chunk_size = chunk_size
        self._seen_urls = set()
        self._url_lock = threading.Lock()
        self.download_dir = "downloads"
        os.makedirs(self.download_dir, exist_ok=True)

        # Statistics with thread-safe counters
        self._stats_lock = threading.Lock()
        self.total_sprites = 0
        self.total_forms_processed = 0
        self.total_form_media = 0
        self.failed_downloads = 0
        self.pokemon_processed = 0

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Pokemon-ETL/1.0"})

        adapter = HTTPAdapter(
            pool_connections=400,
            pool_maxsize=400,
            max_retries=3,
            pool_block=True,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    # -------- STEP 1: GET POKEMON LIST --------
    def get_pokemon_list(self) -> List[str]:
        url = f"https://pokeapi.co/api/v2/pokemon?limit={self.limit}"
        data = self.session.get(url, timeout=10).json()
        return [p["url"] for p in data["results"]]

    # -------- STEP 2: FETCH POKEMON DATA (SPRITES + FORMS) --------
    def fetch_pokemon_data(self, pokemon_url: str) -> tuple[str, List[Tuple[str, str]], List[dict]]:
        """Fetch both sprites and forms data for a Pokemon"""
        data = self.session.get(pokemon_url, timeout=10).json()
        sprites = data.get("sprites", {})
        forms = data.get("forms", [])
        name = data.get("name", "unknown")
        return name, self.extract_urls(sprites), forms

    def extract_urls(self, data, prefix: str = "") -> List[Tuple[str, str]]:
        """Recursively extract all image URLs from nested data"""
        urls: List[Tuple[str, str]] = []
        if isinstance(data, dict):
            for key, value in data.items():
                next_prefix = f"{prefix}_{key}" if prefix else key
                urls.extend(self.extract_urls(value, next_prefix))
        elif isinstance(data, str) and data.startswith("http"):
            urls.append((prefix or "sprite", data))
        return urls

    # -------- STEP 3: FETCH FORM MEDIA --------
    def fetch_form_media(self, form: dict, form_base_dir: str, pokemon_name: str) -> int:
        """Fetch all media for a single form"""
        form_url = form.get("url")
        if not form_url:
            return 0

        try:
            # Fetch form data
            form_data = self.session.get(form_url, timeout=10).json()
            form_name = form_data.get("name") or form.get("name") or "form"

            # Create form directory
            form_dir = os.path.join(form_base_dir, form_name)
            os.makedirs(form_dir, exist_ok=True)

            # Extract all media URLs from form data
            form_media_urls = self.extract_urls(form_data)

            # Download each media file
            downloaded = 0
            for sprite_key, url in form_media_urls:
                with self._url_lock:
                    if url in self._seen_urls:
                        continue
                    self._seen_urls.add(url)

                result = self.download_one(url, form_dir, sprite_key, f"{pokemon_name}_{form_name}")
                if result:
                    downloaded += 1

            return downloaded

        except Exception as e:
            print(f"  ❌ Form failed: {form.get('name', 'unknown')} - {e}")
            return 0

    # -------- STEP 4: DOWNLOAD FILE --------
    def download_one(self, url: str, folder_path: str, sprite_key: str, pokemon_name: str) -> Optional[str]:
        """Download a single media file"""
        try:
            ext = os.path.splitext(url)[1] or ".png"
            safe_key = sprite_key.replace("/", "_").replace("\\", "_")
            filename = f"{safe_key}_{pokemon_name}{ext}"
            full_path = os.path.join(folder_path, filename)

            # Skip if already exists
            if os.path.exists(full_path):
                return full_path

            # Download file
            r = self.session.get(url, stream=True, timeout=10)
            r.raise_for_status()

            with open(full_path, "wb") as f:
                for chunk in r.iter_content(self.chunk_size):
                    if chunk:
                        f.write(chunk)

            return full_path

        except Exception as e:
            with self._stats_lock:
                self.failed_downloads += 1
            return None

    # -------- MAIN RUN --------
    def run(self):
        print("=" * 70)
        print("🎮 POKEMON MEDIA DOWNLOADER")
        print("=" * 70)
        print(f"📊 Target: {self.limit} Pokemon")
        print(f"⚙️  Workers: fetch={self.fetch_workers}, download={self.download_workers}, forms={self.form_workers}")
        print(f"📁 Output: {os.path.abspath(self.download_dir)}")
        print("=" * 70)
        print()

        start_time = datetime.now()
        pokemon_urls = self.get_pokemon_list()

        with ThreadPoolExecutor(max_workers=self.fetch_workers) as fetch_pool, \
                ThreadPoolExecutor(max_workers=self.download_workers) as download_pool, \
                ThreadPoolExecutor(max_workers=self.form_workers) as form_pool:

            # Submit all Pokemon fetch tasks
            fetch_futures = {
                fetch_pool.submit(self.fetch_pokemon_data, url): url
                for url in pokemon_urls
            }

            download_futures = []
            form_futures = []
            max_in_flight = self.download_workers * 4

            # Process Pokemon as they complete
            for fetch_future in as_completed(fetch_futures):
                try:
                    name, sprite_items, forms = fetch_future.result()

                    with self._stats_lock:
                        self.pokemon_processed += 1
                        current = self.pokemon_processed

                    # Print progress every 10 Pokemon
                    if current % 10 == 0:
                        print(f"⏳ Processed {current}/{len(pokemon_urls)} Pokemon...")

                    # Create directory structure
                    pokemon_dir = os.path.join(self.download_dir, name)
                    sprite_dir = os.path.join(pokemon_dir, "sprites")
                    form_base_dir = os.path.join(pokemon_dir, "forms")
                    os.makedirs(sprite_dir, exist_ok=True)

                    # Submit sprite downloads
                    for sprite_key, url in sprite_items:
                        with self._url_lock:
                            if url in self._seen_urls:
                                continue
                            self._seen_urls.add(url)

                        download_futures.append(
                            download_pool.submit(self.download_one, url, sprite_dir, sprite_key, name)
                        )

                        # Throttle in-flight downloads
                        if len(download_futures) >= max_in_flight:
                            done, download_futures = wait(download_futures, return_when=FIRST_COMPLETED)
                            download_futures = list(download_futures)

                            # Count successful sprite downloads
                            for f in done:
                                if f.result() is not None:
                                    with self._stats_lock:
                                        self.total_sprites += 1

                    # Submit form fetch tasks
                    if forms:
                        with self._stats_lock:
                            self.total_forms_processed += len(forms)

                        for form in forms:
                            form_futures.append(
                                form_pool.submit(self.fetch_form_media, form, form_base_dir, name)
                            )

                except Exception as e:
                    print(f"❌ Pokemon fetch failed: {e}")

            # Wait for remaining sprite downloads
            print("\n⏳ Finishing sprite downloads...")
            for future in as_completed(download_futures):
                if future.result() is not None:
                    with self._stats_lock:
                        self.total_sprites += 1

            # Wait for all form downloads and count results
            print("⏳ Finishing form downloads...")
            for future in as_completed(form_futures):
                try:
                    count = future.result()
                    with self._stats_lock:
                        self.total_form_media += count
                except Exception as e:
                    print(f"❌ Form download error: {e}")

        # Calculate statistics
        duration = datetime.now() - start_time
        total_files = self.total_sprites + self.total_form_media
        speed = total_files / duration.total_seconds() if duration.total_seconds() > 0 else 0

        # Print final statistics
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        print(f"✅ Pokemon Processed:            {self.pokemon_processed:,}")
        print(f"✅ Total Sprites Downloaded:     {self.total_sprites:,}")
        print(f"✅ Total Forms Processed:        {self.total_forms_processed:,}")
        print(f"✅ Total Form Media Downloaded:  {self.total_form_media:,}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"📁 TOTAL FILES DOWNLOADED:       {total_files:,}")
        print(f"❌ Failed Downloads:             {self.failed_downloads:,}")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"⏱️  Total Time:                   {duration}")
        print(f"⚡ Download Speed:                {speed:.1f} files/second")
        print(f"📂 Output Directory:             {os.path.abspath(self.download_dir)}")
        print("=" * 70)


if __name__ == "__main__":
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    downloader = FastThreadMediaDownloader(
        limit=135,  # Number of Pokemon to download
        fetch_workers=60,  # Parallel Pokemon fetchers
        download_workers=250,  # Parallel file downloaders
        form_workers=40,  # Parallel form fetchers
    )

    downloader.run()

    print(f"\n⏰ End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")