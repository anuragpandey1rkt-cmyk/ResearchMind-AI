import asyncio
from duckduckgo_search import DDGS
from app.schemas.research import Source


class SearchService:
    async def search(self, query: str, max_results: int = 8) -> list[Source]:
        def run_search() -> list[Source]:
            with DDGS() as ddgs:
                rows = list(ddgs.text(query, max_results=max_results, safesearch="moderate"))
            sources: list[Source] = []
            for idx, row in enumerate(rows, start=1):
                sources.append(
                    Source(
                        title=row.get("title") or "Untitled source",
                        url=row.get("href") or row.get("url") or "",
                        snippet=row.get("body") or "",
                        rank=idx,
                    )
                )
            return [source for source in sources if source.url]

        try:
            return await asyncio.to_thread(run_search)
        except Exception:
            return []

    async def search_many(self, queries: list[str], max_per_query: int = 5) -> list[Source]:
        results = await asyncio.gather(*(self.search(query, max_per_query) for query in queries))
        seen: set[str] = set()
        merged: list[Source] = []
        for group in results:
            for source in group:
                if source.url not in seen:
                    seen.add(source.url)
                    source.rank = len(merged) + 1
                    merged.append(source)
        return merged
