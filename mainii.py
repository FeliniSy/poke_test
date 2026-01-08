import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage

# --- CONFIGURATION ---
DOWNLOAD_DIR = "downloads"
BUCKET_NAME = "pokemon_api"
PROJECT_ID = "pokemon-api-483406"
MAX_WORKERS = 100  # High thread count for network-bound tasks

# Initialize Client ONCE (Global)
# This uses a single connection pool for all 45,000 uploads
client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET_NAME)

stats = {"count": 0}
lock = threading.Lock()


def fast_upload(file_path):
    """The leanest possible upload function."""
    try:
        # Use basename for the destination path in GCS
        blob_name = f"pokemon/{os.path.basename(file_path)}"
        blob = bucket.blob(blob_name)

        # checksum=None skips MD5 calculation (Saves significant CPU/Time)
        # content_type is set manually to skip auto-detection overhead
        blob.upload_from_filename(file_path, checksum=None, content_type='image/png')

        with lock:
            stats["count"] += 1
            if stats["count"] % 500 == 0:
                print(f"🚀 Progress: {stats['count']} files uploaded...")
    except Exception as e:
        print(f"❌ Failed {file_path}: {e}")


def main():
    # 1. Gather all files first (Pre-processing)
    all_files = [
        os.path.join(DOWNLOAD_DIR, f)
        for f in os.listdir(DOWNLOAD_DIR)
        if os.path.isfile(os.path.join(DOWNLOAD_DIR, f))
    ]

    total_files = len(all_files)
    print(f"📦 Found {total_files} files. Starting high-speed upload...")

    start_time = time.perf_counter()

    # 2. Use a high-capacity ThreadPool
    # We use .map() for the fastest distribution of tasks
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(fast_upload, all_files)

    duration = time.perf_counter() - start_time
    avg_speed = total_files / duration
    print(f"\n✅ FINISHED!")
    print(f"Total Time: {duration:.2f} seconds")
    print(f"Average Speed: {avg_speed:.2f} files/second")


if __name__ == "__main__":
    main()