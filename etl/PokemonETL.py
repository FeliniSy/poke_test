# import logging
# import os
# import shutil
# from concurrent.futures import ThreadPoolExecutor
# from datetime import datetime
#
# from etl.download.media_downloader import MediaDownloader
# from etl.extract.PokeApiClient import PokeApiClient
# from etl.pokemon.pokemon_factory import PokemonFactory
# from etl.upload.media_uploader import MediaUploader
# from utils.helper import extract_urls
# from utils.logger import logger
# from utils.settings import URL
#
# logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
#
# class PokemonETLManager:
#     def __init__(self):
#         self.client = PokeApiClient(URL)
#         self.downloader = MediaDownloader()
#         self.uploader = MediaUploader()
#         self.temp_dir = 'downloads'
#         self.pokemon_data_list = []
#
#     def download_phase_task(self, p_id: int):
#         try:
#             raw_data = self.client.fetch_raw_pokemon_data(p_id)
#             poke_obj = PokemonFactory.from_api(raw_data)
#
#             self.pokemon_data_list.append(poke_obj)
#
#             urls = extract_urls(raw_data.get('sprites', {}))
#             if urls:
#                 local_folder = os.path.join(self.temp_dir, poke_obj.name)
#                 self.downloader.download_batch(urls, local_folder)
#             return poke_obj.name
#         except Exception as e:
#             logger.warning(f"Download phase failed for id={p_id}: {e}")
#             return None
#
#     def upload_phase_task(self, pokemon_name: str):
#         try:
#             local_folder = os.path.join(self.temp_dir, pokemon_name)
#             if os.path.exists(local_folder):
#                 self.uploader.upload_folder(local_folder, pokemon_name)
#                 shutil.rmtree(local_folder)
#                 return True
#         except Exception as e:
#             return False
#
#     def run(self, limit):
#         start_time = datetime.now()
#
#         ids = self.client.fetch_all_ids(limit)
#         logger.info(f"--- STARTING DOWNLOAD PHASE ---")
#         with ThreadPoolExecutor(max_workers=100) as executor:
#             downloaded_names = list(executor.map(self.download_phase_task, ids))
#
#         successful_names = [name for name in downloaded_names if name]
#
#         logger.info(f"--- STARTING UPLOAD PHASE ---")
#         with ThreadPoolExecutor(max_workers=120) as executor:
#             executor.map(self.upload_phase_task, successful_names)
#
#         # logger.info("Bulk inserting to Database...")
#         # self.poke_saver.save_pokemon(self.pokemon_data_list)
#
#         logger.info(f"Total Duration: {datetime.now() - start_time}")