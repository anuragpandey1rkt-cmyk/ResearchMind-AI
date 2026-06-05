import json
from collections import Counter, defaultdict
from langgraph.graph import END, StateGraph
from app.agents.gap_state import GapDetectionState
from app.schemas.gap_detection import Contradiction, GapItem, GapScores, InnovationSuggestion, KnowledgeGraph, ThemeCluster
from app.services.groq_client import GroqClient
from app.services.gap_retrieval_service import GapRetrievalService
from app.services.paper_analysis_service import PaperAnalysisService


class GapDetectionWorkflow:
    def __init__(self, paper_service: PaperAnalysisService | None = None, groq: GroqClient | None = None) -> None:
        self.paper_service = paper_service or PaperAnalysisService()
        self.groq = groq or GroqClient()
        self.retrieval = GapRetrievalService(self.paper_service.vector_store)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(GapDetectionState)
        graph.add_node("paper_analysis", self.paper_analysis_agent)
        graph.add_node("knowledge_synthesis", self.knowledge_synthesis_agent)
        graph.add_node("contradiction_detection", self.contradiction_detection_agent)
        graph.add_node("gap_detection", self.gap_detection_agent)
        graph.add_node("innovation", self.innovation_agent)
        graph.set_entry_point("paper_analysis")
        graph.add_edge("paper_analysis", "knowledge_synthesis")
        graph.add_edge("knowledge_synthesis", "contradiction_detection")
        graph.add_edge("contradiction_detection", "gap_detection")
        graph.add_edge("gap_detection", "innovation")
        graph.add_edge("innovation", END)
        return graph.compile()

    async def paper_analysis_agent(self, state: GapDetectionState) -> GapDetectionState:
        summaries = await self.paper_service.analyze_documents(state["documents"])
        state["papers"] = [summary.model_dump() for summary in summaries]
        return state

    async def knowledge_synthesis_agent(self, state: GapDetectionState) -> GapDetectionState:
        papers = state.get("papers", [])
        area_counts = Counter(area for paper in papers for area in paper.get("research_areas", []))
        method_counts = Counter(method for paper in papers for method in paper.get("methods", []))
        clusters = []
        for area, count in area_counts.most_common() or [("General Research", len(papers))]:
            related = [paper["title"] for paper in papers if area in paper.get("research_areas", [])]
            concepts = [method for method, _ in method_counts.most_common(6)]
            clusters.append(
                ThemeCluster(
                    name=area,
                    papers=related or [paper["title"] for paper in papers],
                    concepts=concepts,
                    saturation_score=min(100, int((count / max(1, len(papers))) * 100)),
                ).model_dump()
            )
        state["theme_clusters"] = clusters
        state["knowledge_graph"] = self._build_knowledge_graph(papers).model_dump()
        return state

    async def contradiction_detection_agent(self, state: GapDetectionState) -> GapDetectionState:
        prompt = (
            "Return strict JSON with key contradictions as an array. Each item has claim_a, claim_b, papers, severity, explanation. "
            "Compare conclusions and results for disagreements. Papers JSON:\n"
            f"{json.dumps(state.get('papers', []))[:18000]}"
        )
        contradictions = await self._json_array(prompt, "contradictions")
        if not contradictions:
            contradictions = self._heuristic_contradictions(state.get("papers", []))
        state["contradictions"] = [Contradiction.model_validate(item).model_dump() for item in contradictions[:12]]
        return state

    async def gap_detection_agent(self, state: GapDetectionState) -> GapDetectionState:
        papers = state.get("papers", [])
        state["retrieval_context"] = self.retrieval.retrieve_for_gap_detection(
            state.get("research_domain", ""),
            top_k=state.get("top_k", 12),
        )
        prompt = (
            "Return strict JSON with key gaps as an array. Each item has category, description, evidence, novelty_score, impact_score, feasibility_score. "
            "Identify missing approaches, datasets, experiments, populations, benchmarks, metrics, geographic coverage, and methodological limitations. "
            f"Domain: {state.get('research_domain')}\n"
            f"Retrieval JSON:\n{json.dumps(state.get('retrieval_context', {}))[:8000]}\n"
            f"Papers JSON:\n{json.dumps(papers)[:18000]}"
        )
        gaps = await self._json_array(prompt, "gaps")
        if not gaps:
            gaps = self._heuristic_gaps(papers)
        state["gaps"] = [GapItem.model_validate(item).model_dump() for item in gaps[:18]]
        state["scores"] = self._score_inventory(state["gaps"], state.get("theme_clusters", [])).model_dump()
        state["visualizations"] = self._visualizations(state)
        return state

    async def innovation_agent(self, state: GapDetectionState) -> GapDetectionState:
        prompt = (
            "Return strict JSON with key innovations as an array. Each item has title, type, rationale, novelty_score, "
            "feasibility_score, impact_score, commercialization_potential_score. Include thesis topics, product ideas, startup opportunities, "
            "and future research directions. Evidence JSON:\n"
            f"{json.dumps({'gaps': state.get('gaps', []), 'themes': state.get('theme_clusters', []), 'contradictions': state.get('contradictions', [])})[:16000]}"
        )
        innovations = await self._json_array(prompt, "innovations")
        if not innovations:
            innovations = self._heuristic_innovations(state.get("gaps", []), state.get("research_domain", "Research"))
        state["innovations"] = [InnovationSuggestion.model_validate(item).model_dump() for item in innovations[:16]]
        state["visualizations"] = self._visualizations(state)
        state["report_markdown"] = await self._write_report(state)
        return state

    async def run(self, analysis_id: str, documents: list, research_domain: str, top_k: int) -> GapDetectionState:
        initial: GapDetectionState = {
            "analysis_id": analysis_id,
            "documents": documents,
            "research_domain": research_domain,
            "top_k": top_k,
        }
        return await self.graph.ainvoke(initial)

    async def _json_array(self, prompt: str, key: str) -> list[dict]:
        content = await self.groq.chat(
            [{"role": "system", "content": "You are a principal AI research analyst. Return only valid JSON."}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )
        try:
            parsed = json.loads(content)
            value = parsed.get(key, [])
            return value if isinstance(value, list) else []
        except Exception:
            return []

    async def _write_report(self, state: GapDetectionState) -> str:
        if not self.groq.settings.groq_api_key:
            return self._fallback_report(state)
        prompt = (
            "Generate a professional Markdown Research Gap Report with sections: Executive Summary, Papers Reviewed, Common Themes, "
            "Existing Solutions, Contradictory Findings, Methodological Weaknesses, Missing Research Areas, Dataset Gaps, Evaluation Gaps, "
            "Emerging Opportunities, Suggested Research Topics, Potential Startup Ideas, Future Research Roadmap, References. "
            "Ground every claim in the provided paper summaries, gaps, contradictions, and innovations. JSON:\n"
            f"{json.dumps(state, default=str)[:26000]}"
        )
        return await self.groq.chat(
            [{"role": "system", "content": "You write rigorous, evidence-grounded research strategy reports."}, {"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=7000,
        )

    def _fallback_report(self, state: GapDetectionState) -> str:
        papers = state.get("papers", [])
        gaps = state.get("gaps", [])
        contradictions = state.get("contradictions", [])
        innovations = state.get("innovations", [])
        themes = state.get("theme_clusters", [])
        scores = state.get("scores", {})
        paper_lines = "\n".join(f"- {paper['title']}" for paper in papers) or "- No papers parsed."
        theme_lines = "\n".join(f"- {theme['name']}: {len(theme.get('papers', []))} papers, saturation {theme.get('saturation_score', 0)}%" for theme in themes) or "- No recurring themes detected."
        contradiction_lines = "\n".join(f"- {item['explanation']} Papers: {', '.join(item.get('papers', []))}" for item in contradictions) or "- No strong contradictions were detected by the heuristic analyzer."
        gap_lines = "\n".join(f"- {gap['category']}: {gap['description']}" for gap in gaps) or "- No high-confidence gaps were detected."
        innovation_lines = "\n".join(f"- {item['title']} ({item['type']}): {item['rationale']}" for item in innovations) or "- Expand the corpus and rerun analysis for stronger innovation signals."
        score_lines = "\n".join(f"- {key.replace('_', ' ').title()}: {value}" for key, value in scores.items())
        return f"""# {state.get('research_domain', 'Research')} Research Gap Report

## 1. Executive Summary

This report reviews {len(papers)} papers and identifies recurring themes, contradictions, methodological weaknesses, dataset gaps, evaluation gaps, and future opportunities. Scores were computed from the detected gap inventory and theme saturation.

{score_lines}

## 2. Papers Reviewed

{paper_lines}

## 3. Common Themes

{theme_lines}

## 4. Existing Solutions

The reviewed papers concentrate around the extracted methods, datasets, and metrics represented in the knowledge graph. Repeated themes indicate areas where existing work is comparatively mature.

## 5. Contradictory Findings

{contradiction_lines}

## 6. Methodological Weaknesses

{gap_lines}

## 7. Missing Research Areas

{gap_lines}

## 8. Dataset Gaps

{gap_lines}

## 9. Evaluation Gaps

{gap_lines}

## 10. Emerging Opportunities

{innovation_lines}

## 11. Suggested Research Topics

{innovation_lines}

## 12. Potential Startup Ideas

{innovation_lines}

## 13. Future Research Roadmap

1. Standardize datasets and evaluation metrics.
2. Validate findings across broader populations, geographies, and deployment contexts.
3. Compare underused methods against repeated baselines.
4. Convert high-impact gaps into benchmark tasks and reproducible studies.

## 14. References

{paper_lines}
"""

    def _build_knowledge_graph(self, papers: list[dict]) -> KnowledgeGraph:
        nodes = {}
        edges = {}

        def add_node(node_id: str, label: str, node_type: str, score: float = 1.0) -> None:
            nodes[node_id] = {"id": node_id, "label": label[:90], "type": node_type, "score": score}

        def add_edge(source: str, target: str, label: str, weight: float = 1.0) -> None:
            edge_id = f"{source}:{label}:{target}"
            edges[edge_id] = {"id": edge_id, "source": source, "target": target, "label": label, "weight": weight}

        for paper in papers:
            paper_id = f"paper:{paper['document_id']}"
            add_node(paper_id, paper["title"], "Paper")
            for author in paper.get("authors", []):
                node_id = f"author:{author.lower()}"
                add_node(node_id, author, "Author")
                add_edge(node_id, paper_id, "AUTHORED")
            for method in paper.get("methods", []):
                node_id = f"method:{method.lower()}"
                add_node(node_id, method, "Method")
                add_edge(paper_id, node_id, "USES")
            for dataset in paper.get("datasets", []):
                node_id = f"dataset:{dataset.lower()}"
                add_node(node_id, dataset, "Dataset")
                add_edge(paper_id, node_id, "USES")
            for metric in paper.get("metrics", []):
                node_id = f"metric:{metric.lower()}"
                add_node(node_id, metric, "Metric")
                add_edge(paper_id, node_id, "COMPARES")
            for area in paper.get("research_areas", []):
                node_id = f"area:{area.lower()}"
                add_node(node_id, area, "Research Area")
                add_edge(paper_id, node_id, "RELATED_TO")
            for idx, limitation in enumerate(paper.get("limitations", [])[:4]):
                node_id = f"limitation:{paper['document_id']}:{idx}"
                add_node(node_id, limitation, "Limitation", 0.8)
                add_edge(paper_id, node_id, "LIMITED_BY")
            for idx, future in enumerate(paper.get("future_work", [])[:4]):
                node_id = f"future:{paper['document_id']}:{idx}"
                add_node(node_id, future, "Future Work", 0.9)
                add_edge(paper_id, node_id, "SUGGESTS")

        return KnowledgeGraph(nodes=list(nodes.values()), edges=list(edges.values()))

    def _heuristic_contradictions(self, papers: list[dict]) -> list[dict]:
        contradictions = []
        positive_words = {"improves", "outperforms", "effective", "significant", "robust"}
        negative_words = {"limited", "fails", "underperforms", "insignificant", "unstable"}
        for i, first in enumerate(papers):
            for second in papers[i + 1 :]:
                first_text = " ".join(first.get("key_findings", [])).lower()
                second_text = " ".join(second.get("key_findings", [])).lower()
                if positive_words & set(first_text.split()) and negative_words & set(second_text.split()):
                    contradictions.append(
                        {
                            "claim_a": first.get("key_findings", ["Positive finding"])[0],
                            "claim_b": second.get("key_findings", ["Limiting finding"])[0],
                            "papers": [first["title"], second["title"]],
                            "severity": 62,
                            "explanation": "The papers appear to report different performance or robustness conclusions.",
                        }
                    )
        return contradictions[:8]

    def _heuristic_gaps(self, papers: list[dict]) -> list[dict]:
        gaps = []
        datasets = [dataset for paper in papers for dataset in paper.get("datasets", [])]
        metrics = [metric for paper in papers for metric in paper.get("metrics", [])]
        methods = [method for paper in papers for method in paper.get("methods", [])]
        if len(set(datasets)) < max(2, len(papers) // 2):
            gaps.append({"category": "Dataset Gaps", "description": "The reviewed papers use few named datasets or benchmarks, limiting external validity.", "evidence": datasets[:5], "novelty_score": 74, "impact_score": 82, "feasibility_score": 68})
        if len(set(metrics)) < 3:
            gaps.append({"category": "Evaluation Gaps", "description": "Evaluation metrics are sparse or inconsistent across papers, making comparison difficult.", "evidence": metrics[:5], "novelty_score": 66, "impact_score": 78, "feasibility_score": 76})
        if len(set(methods)) < 3:
            gaps.append({"category": "Methodological Limitations", "description": "The literature appears concentrated around a narrow set of methods.", "evidence": methods[:5], "novelty_score": 70, "impact_score": 75, "feasibility_score": 72})
        gaps.extend(
            {
                "category": "Open Problems",
                "description": limitation,
                "evidence": [paper["title"]],
                "novelty_score": 80,
                "impact_score": 76,
                "feasibility_score": 64,
            }
            for paper in papers
            for limitation in paper.get("limitations", [])[:2]
        )
        return gaps or [{"category": "Missing Research Areas", "description": "The corpus is small; broader paper coverage is needed to distinguish saturation from genuine gaps.", "evidence": [paper["title"] for paper in papers], "novelty_score": 58, "impact_score": 65, "feasibility_score": 84}]

    def _heuristic_innovations(self, gaps: list[dict], domain: str) -> list[dict]:
        suggestions = []
        for gap in gaps[:8]:
            suggestions.append(
                {
                    "title": f"{domain}: {gap['category']} study",
                    "type": "Thesis Topic",
                    "rationale": f"Addresses gap: {gap['description']}",
                    "novelty_score": min(95, gap.get("novelty_score", 60) + 5),
                    "feasibility_score": gap.get("feasibility_score", 60),
                    "impact_score": gap.get("impact_score", 60),
                    "commercialization_potential_score": 58 if gap["category"] != "Dataset Gaps" else 72,
                }
            )
        suggestions.append(
            {
                "title": f"Benchmark suite for {domain}",
                "type": "Startup Opportunity",
                "rationale": "Standardized datasets and evaluation dashboards can convert literature fragmentation into a reusable research infrastructure product.",
                "novelty_score": 76,
                "feasibility_score": 70,
                "impact_score": 82,
                "commercialization_potential_score": 84,
            }
        )
        return suggestions

    def _score_inventory(self, gaps: list[dict], themes: list[dict]) -> GapScores:
        avg = lambda key, default: int(sum(item.get(key, default) for item in gaps) / max(1, len(gaps)))
        saturation = int(sum(theme.get("saturation_score", 50) for theme in themes) / max(1, len(themes)))
        return GapScores(
            novelty_score=avg("novelty_score", 65),
            research_saturation_score=saturation,
            impact_score=avg("impact_score", 70),
            feasibility_score=avg("feasibility_score", 65),
            commercialization_potential_score=max(35, min(95, avg("impact_score", 65) - 5)),
        )

    def _visualizations(self, state: GapDetectionState) -> dict:
        gaps_by_category = Counter(gap["category"] for gap in state.get("gaps", []))
        opportunities = [
            {
                "title": item["title"],
                "impact": item["impact_score"],
                "feasibility": item["feasibility_score"],
                "commercialization": item["commercialization_potential_score"],
            }
            for item in state.get("innovations", [])
        ]
        papers_by_theme = defaultdict(int)
        for cluster in state.get("theme_clusters", []):
            papers_by_theme[cluster["name"]] += len(cluster.get("papers", []))
        return {
            "theme_clusters": state.get("theme_clusters", []),
            "research_trends": [{"name": name, "papers": count} for name, count in papers_by_theme.items()],
            "gap_heatmap": [{"category": key, "count": value} for key, value in gaps_by_category.items()],
            "opportunity_matrix": opportunities,
            "innovation_scores": state.get("scores", {}),
        }
