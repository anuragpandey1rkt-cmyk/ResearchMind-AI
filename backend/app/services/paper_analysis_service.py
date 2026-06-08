import json
import re
from pathlib import Path
from app.schemas.gap_detection import PaperSummary
from app.services.chunking import ChunkingService
from app.services.groq_client import GroqClient
from app.services.pdf_service import PdfService
from app.services.vector_store import ChromaVectorStore


SECTION_ALIASES = {
    "abstract": ["abstract"],
    "methodology": ["method", "methods", "methodology", "materials and methods", "experimental setup"],
    "results": ["results", "findings", "experiments", "evaluation"],
    "limitations": ["limitations", "threats to validity", "discussion"],
    "future_work": ["future work", "future directions", "conclusion", "conclusions"],
}


class PaperAnalysisService:
    def __init__(self) -> None:
        self.pdf_service = PdfService()
        self.chunker = ChunkingService()
        self.groq = GroqClient()
        self.vector_store = ChromaVectorStore()

    async def analyze_document(self, document) -> PaperSummary:
        pdf_data = await self.pdf_service.download_pdf(document.storage_path)
        text = self.pdf_service.extract_text(pdf_data)
        sections = self._extract_sections(text)
        heuristic = self._heuristic_summary(document.id, document.filename, text, sections)
        llm_summary = await self._llm_enrich(heuristic, text)
        summary = PaperSummary.model_validate({**heuristic.model_dump(), **llm_summary})
        chunks = self.chunker.chunk(text)
        self.vector_store.add_paper_artifacts(summary.model_dump(), chunks)
        return summary

    async def analyze_documents(self, documents: list) -> list[PaperSummary]:
        summaries = []
        for document in documents:
            summaries.append(await self.analyze_document(document))
        return summaries

    async def _llm_enrich(self, heuristic: PaperSummary, text: str) -> dict:
        prompt = (
            "Extract strict JSON for a research paper with keys: title, authors, abstract, methodology, results, "
            "limitations, future_work, key_findings, methods, datasets, metrics, research_areas. "
            "Use arrays for authors, limitations, future_work, key_findings, methods, datasets, metrics, research_areas. "
            "Do not invent missing values. Paper text:\n"
            f"{text[:18000]}"
        )
        content = await self.groq.chat(
            [
                {"role": "system", "content": "You extract structured facts from research papers. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        try:
            parsed = json.loads(content)
            return self._normalize_llm_summary(parsed)
        except Exception:
            return heuristic.model_dump()

    def _heuristic_summary(self, document_id: str, filename: str, text: str, sections: dict[str, str]) -> PaperSummary:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        title = self._clean_title(lines[0] if lines else filename)
        methodology = sections.get("methodology", "")
        results = sections.get("results", "")
        limitations_text = sections.get("limitations", "")
        future_text = sections.get("future_work", "")
        return PaperSummary(
            document_id=document_id,
            filename=filename,
            title=title,
            authors=self._extract_authors(lines[:12]),
            abstract=sections.get("abstract", "")[:2500],
            methodology=methodology[:2500],
            results=results[:2500],
            limitations=self._sentences(limitations_text, 6),
            future_work=self._sentences(future_text, 6),
            key_findings=self._sentences(results or sections.get("abstract", ""), 8),
            methods=self._keywords(methodology, ["transformer", "survey", "experiment", "simulation", "regression", "benchmark", "interview", "case study", "neural", "optimization"]),
            datasets=self._extract_named_items(text, ["dataset", "corpus", "benchmark", "data set"]),
            metrics=self._extract_named_items(text, ["accuracy", "f1", "precision", "recall", "auc", "rmse", "mae", "latency", "throughput", "bleu", "rouge"]),
            research_areas=self._research_areas(text),
        )

    def _extract_sections(self, text: str) -> dict[str, str]:
        section_hits: list[tuple[int, str]] = []
        for match in re.finditer(r"(?im)^\s*(\d+\.?\s*)?([A-Z][A-Za-z\s&-]{2,60})\s*$", text):
            heading = match.group(2).strip().lower()
            for canonical, aliases in SECTION_ALIASES.items():
                if heading in aliases or any(heading.startswith(alias) for alias in aliases):
                    section_hits.append((match.start(), canonical))
        section_hits = sorted(set(section_hits))
        sections: dict[str, str] = {}
        for idx, (start, name) in enumerate(section_hits):
            end = section_hits[idx + 1][0] if idx + 1 < len(section_hits) else min(len(text), start + 5000)
            body = text[start:end]
            sections.setdefault(name, body[:5000])
        if "abstract" not in sections:
            sections["abstract"] = text[:2200]
        return sections

    def _normalize_llm_summary(self, parsed: dict) -> dict:
        array_fields = ["authors", "limitations", "future_work", "key_findings", "methods", "datasets", "metrics", "research_areas"]
        normalized = {}
        for key, value in parsed.items():
            if key in array_fields:
                if isinstance(value, list):
                    normalized[key] = [str(item).strip() for item in value if str(item).strip()]
                elif isinstance(value, str) and value.strip():
                    normalized[key] = self._sentences(value, 8)
            elif isinstance(value, str):
                normalized[key] = value.strip()
        return normalized

    def _clean_title(self, title: str) -> str:
        title = re.sub(r"\s+", " ", title).strip()
        return title[:220] or "Untitled paper"

    def _extract_authors(self, lines: list[str]) -> list[str]:
        candidates = []
        for line in lines[1:6]:
            if "@" in line or re.search(r"\b(university|institute|department|school)\b", line, re.I):
                continue
            if 2 <= len(line.split()) <= 18 and not line.lower().startswith("abstract"):
                candidates.extend([part.strip() for part in re.split(r",| and ", line) if part.strip()])
        return candidates[:8]

    def _sentences(self, text: str, limit: int) -> list[str]:
        pieces = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
        return [piece.strip()[:450] for piece in pieces if len(piece.strip()) > 30][:limit]

    def _keywords(self, text: str, vocabulary: list[str]) -> list[str]:
        lowered = text.lower()
        found = [term.title() for term in vocabulary if term in lowered]
        return list(dict.fromkeys(found))[:10]

    def _extract_named_items(self, text: str, hints: list[str]) -> list[str]:
        found: list[str] = []
        lowered = text.lower()
        for hint in hints:
            if hint.lower() in lowered:
                found.append(hint.upper() if len(hint) <= 4 else hint.title())
        for match in re.finditer(r"\b([A-Z][A-Za-z0-9-]{2,}(?:\s+[A-Z][A-Za-z0-9-]{2,}){0,3})\b", text[:12000]):
            value = match.group(1).strip()
            if any(word.lower() in value.lower() for word in ["dataset", "benchmark", "corpus"]):
                found.append(value)
        return list(dict.fromkeys(found))[:12]

    def _research_areas(self, text: str) -> list[str]:
        vocabulary = [
            "artificial intelligence",
            "machine learning",
            "natural language processing",
            "computer vision",
            "healthcare",
            "education",
            "finance",
            "climate",
            "robotics",
            "cybersecurity",
            "human-computer interaction",
            "information retrieval",
        ]
        return self._keywords(text, vocabulary) or ["General Research"]
