import os
import threading
import time
from asyncio import as_completed
from concurrent.futures.thread import ThreadPoolExecutor
from google.cloud import storage

import requests

# Ensure the download directory exists
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

thread_local = threading.local()


def fetch(pokemon_id):
    try:
        # Fixed the URL formatting
        url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print(f"Fetched data for Pokemon ID: {pokemon_id}")
            return response.json()
        return None
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch pokemon {pokemon_id}: {e}")
        return None


def extract_url(d):
    urls = []
    if isinstance(d, dict):
        for value in d.values():
            urls.extend(extract_url(value))
    elif isinstance(d, list):
        for item in d:
            urls.extend(extract_url(item))
    elif isinstance(d, str) and d.startswith("http") and any(ext in d for ext in ['.png', '.jpg', '.gif']):
            urls.append(d)
    return list(set(urls))  # Use set to remove duplicate image URLs


def download_site(url):
    try:
        session = get_session_for_thread()
        filename = os.path.join(DOWNLOAD_DIR, url.split("/")[-1])
        with session.get(url, timeout=5) as response:
            response.raise_for_status()
            with open(filename, "wb") as f:
                f.write(response.content)
                print("ooo")
    except Exception as e:
        print(e)


def get_session_for_thread():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.session()
    return thread_local.session


def download_all_sites(sites):
    # Creating the session here and passing it down is much faster
    with ThreadPoolExecutor(max_workers=50) as executor:
        executor.map(download_site, sites)


def get_list():
    url = "https://pokeapi.co/api/v2/pokemon?limit=1350"  # Reduced limit for testing
    return [int(p["url"].split("/")[-2]) for p in requests.get(url).json()["results"]]

def process_pokemon(pokemon_id):
    """Handles everything for one Pokemon: Fetch JSON -> Extract -> Download Images"""
    session = get_session_for_thread()
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}"
    try:
        resp = session.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            image_urls = extract_url(data.get('sprites', {}))
            # We can even nest another ThreadPool here,
            # but for 10-20 images, a simple loop inside a thread is often fine
            for img_url in image_urls:
                download_site(img_url)
    except Exception as e:
        print(f"Error on {pokemon_id}: {e}")

DOWNLOAD_DIR = "downloads"

uploaded_count = 0
upload_lock = threading.Lock()
client = storage.Client(project="pokemon-api-483406")


def upload_gcd(file_path,bucket_name):
    global uploaded_count
    try:
        bucket = client.bucket(bucket_name)

        blob_path = f"pokemon/{os.path.basename(file_path)}"
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(file_path,checksum=None)
        with upload_lock:
            uploaded_count += 1
            if uploaded_count % 100 ==0:
                print(f"Uploaded: {uploaded_count}/45264 ")
        return blob.public_url
    except Exception as e:
        print(f"failed to upload{file_path}", e)
        return None




def main():
    start = time.perf_counter()
    bucket_name = "pokemon_api"
    uploaded_pokemon_count  = 0

    files_to_upload = [
        os.path.join(DOWNLOAD_DIR,f)
        for f in os.listdir(DOWNLOAD_DIR)
        if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))
    ]

    print(f"found {len(files_to_upload)}")

    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(upload_gcd,f_path,bucket_name): f_path for f_path in files_to_upload}

        # for future in as_completed(futures):
        #     url = future.result()
        #     if url:
        #         uploaded_pokemon_count += 1
        #         print(f"Uploaded: {url}")

    end_time = time.perf_counter() - start
    print(f"--- Finished! Uploaded {uploaded_pokemon_count} files in {end_time:.2f} seconds ---")


    # ids = get_list()
    # start_time = time.perf_counter()
    #
    # # The Key: We run ALL Pokémon processes at the same time
    # with ThreadPoolExecutor(max_workers=50) as executor:
    #     executor.map(process_pokemon, ids)
    #
    # duration = time.perf_counter() - start_time
    # print(f"Total time for all Pokemon: {duration:.4f} seconds")


if __name__ == "__main__":
    main()
