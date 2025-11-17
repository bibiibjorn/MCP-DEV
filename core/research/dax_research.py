"""
DAX Research Module - Retrieves optimization articles based on query patterns.
Integrates with existing analysis infrastructure.
"""
import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class DaxResearchProvider:
    """
    Provides DAX optimization research and guidance.
    Integrates with existing analysis workflows.
    """

    def __init__(self):
        self.article_patterns = self._load_article_patterns()

    def get_optimization_guidance(
        self, query: str, performance_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get optimization guidance for a DAX query.

        Args:
            query: DAX query to analyze
            performance_data: Optional performance metrics from profiling

        Returns:
            Research results with matched articles and recommendations
        """
        # Analyze query patterns
        matched_articles, pattern_matches = self._analyze_query_patterns(query)

        # Build article summaries (without web fetching for now)
        articles = self._build_article_summaries(matched_articles, pattern_matches)

        # Generate recommendations based on patterns and performance
        recommendations = self._generate_recommendations(
            pattern_matches, performance_data
        )

        return {
            "status": "success",
            "total_articles": len(articles),
            "articles": articles,
            "pattern_matches": pattern_matches,
            "recommendations": recommendations
        }

    def _analyze_query_patterns(self, query: str) -> Tuple[List[str], Dict[str, List[Dict]]]:
        """Analyze query for optimization patterns"""
        matched_articles = []
        pattern_matches = {}

        for article_id, config in self.article_patterns.items():
            patterns = config.get("patterns", [])

            if not patterns:
                # General framework article - always include
                matched_articles.append(article_id)
                continue

            article_matches = []
            for pattern in patterns:
                try:
                    for match in re.finditer(pattern, query, re.IGNORECASE | re.DOTALL):
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(query), match.end() + 50)

                        article_matches.append({
                            "matched_text": match.group(0).strip(),
                            "context": query[context_start:context_end].strip()
                        })
                except re.error:
                    logger.warning(f"Invalid regex pattern in article {article_id}")
                    continue

            if article_matches:
                matched_articles.append(article_id)
                pattern_matches[article_id] = article_matches

        return matched_articles, pattern_matches

    def _build_article_summaries(
        self, article_ids: List[str], pattern_matches: Dict[str, List]
    ) -> List[Dict[str, Any]]:
        """Build article summaries from patterns"""
        articles = []

        for article_id in article_ids:
            config = self.article_patterns.get(article_id, {})

            article = {
                "id": article_id,
                "title": config.get("title", article_id),
                "url": config.get("url", ""),
                "content": config.get("content", ""),
                "matched_patterns": pattern_matches.get(article_id, [])
            }

            articles.append(article)

        return articles

    def _generate_recommendations(
        self,
        pattern_matches: Dict[str, List],
        performance_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate specific recommendations based on patterns and performance"""
        recommendations = []

        # Pattern-based recommendations
        if "sumx_filter" in pattern_matches:
            recommendations.append(
                "Replace SUMX(FILTER(...)) with CALCULATE(SUM(...), filters) "
                "for 5-10x performance improvement"
            )

        if "nested_calculate" in pattern_matches:
            recommendations.append(
                "Avoid nested CALCULATE functions - consolidate filters into single CALCULATE"
            )

        if "filter_all" in pattern_matches:
            recommendations.append(
                "FILTER(ALL(...)) forces Formula Engine - use CALCULATE with filter arguments instead"
            )

        # Performance-based recommendations
        if performance_data:
            metrics = performance_data.get("Performance", {})
            se_percentage = (
                metrics.get("SE", 0) / metrics.get("Total", 1) * 100
                if metrics.get("Total", 0) > 0 else 0
            )

            if se_percentage < 60:
                recommendations.append(
                    f"Current SE%: {se_percentage:.1f}% - Target >80% by reducing row-by-row operations"
                )

            if metrics.get("SE_Queries", 0) > 20:
                recommendations.append(
                    f"High SE query count ({metrics['SE_Queries']}) - "
                    "Simplify measure logic to enable vertical fusion"
                )

        return recommendations

    def _load_article_patterns(self) -> Dict[str, Dict]:
        """Load article patterns from configuration"""
        from .article_patterns import ARTICLE_PATTERNS
        return ARTICLE_PATTERNS
