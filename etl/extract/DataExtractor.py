class MediaExtractor:
    @staticmethod
    def extract_urls(data: dict) -> list[str]:
        urls = []
        if isinstance(data, dict):
            for v in data.values():
                urls.extend(MediaExtractor.extract_urls(v))
        elif isinstance(data, str) and data.startswith("http"):
            urls.append(data)
        return urls
