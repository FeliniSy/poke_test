import requests
from google.cloud import client, storage
from requests.adapters import HTTPAdapter

from utils.settings import PROJECT_ID


class PokeApiClient:
    def __init__(self, base_url: str):
        self.client = client or storage.Client(project=PROJECT_ID)
        self.base_url = base_url
        self.session = requests.Session()

        adapter = HTTPAdapter(
            pool_connections=100,
            pool_maxsize=100,
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter
                           )

    def fetch_raw_pokemon_data(self, pokemon_id: int) -> dict:
        url = self.base_url.format(f"/{pokemon_id}")
        response = self.session.get(url, timeout=5)
        response.raise_for_status()
        return response.json()

    def fetch_all_ids(self, limit) -> list[int]:
        url = self.base_url.format(f"?limit={limit}")
        response = self.session.get(url)
        results = response.json().get('results', [])
        return [int(p["url"].rstrip("/").split("/")[-1]) for p in results]
