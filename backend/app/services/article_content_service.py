import trafilatura


class ArticleContentService:

    def extract(self, url: str) -> str | None:
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            return None
        
        return trafilatura.extract(downloaded)