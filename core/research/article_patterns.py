"""
Article pattern definitions for DAX optimization research.
"""

ARTICLE_PATTERNS = {
    "general_framework": {
        "title": "DAX Query Performance Optimization Framework",
        "url": "https://www.sqlbi.com/articles/optimizing-dax-expressions-involving-aggregate-functions/",
        "patterns": [],  # Always included
        "content": """
        General DAX optimization framework:
        1. Analyze high-level metrics (SE%, FE%, SE query count)
        2. Review EventDetails waterfall for bottlenecks
        3. Identify callbacks, large materializations, excessive scans
        4. Map symptoms to specific optimization patterns
        5. Test optimizations and validate semantic equivalence
        """
    },

    "sumx_filter": {
        "title": "SUMX and FILTER Optimization",
        "url": "https://www.sqlbi.com/articles/optimizing-sumx/",
        "patterns": [
            r"SUMX\s*\(\s*FILTER\s*\(",
            r"AVERAGEX\s*\(\s*FILTER\s*\(",
        ],
        "content": """
        SUMX(FILTER(...)) anti-pattern:
        - Forces row-by-row evaluation in Formula Engine
        - Prevents query fusion and parallelization

        Optimization: Use CALCULATE instead
        Before: SUMX(FILTER(Table, [Column] = Value), [Amount])
        After:  CALCULATE(SUM(Table[Amount]), Table[Column] = Value)

        Expected improvement: 5-10x performance gain
        """
    },

    "filter_all": {
        "title": "FILTER(ALL()) Anti-Pattern",
        "url": "https://www.sqlbi.com/articles/avoiding-filter-in-nested-iterators/",
        "patterns": [
            r"FILTER\s*\(\s*ALL\s*\(",
            r"FILTER\s*\(\s*ALLSELECTED\s*\(",
        ],
        "content": """
        FILTER(ALL(...)) forces Formula Engine evaluation:
        - Cannot be pushed to Storage Engine
        - Materializes entire table in memory
        - Blocks query fusion

        Optimization: Use CALCULATE with filter arguments
        Before: FILTER(ALL(Table), [Column] > 100)
        After:  CALCULATE(VALUES(Table), Table[Column] > 100)
        """
    },

    "nested_calculate": {
        "title": "Nested CALCULATE Anti-Pattern",
        "url": "https://www.sqlbi.com/articles/understanding-context-transition/",
        "patterns": [
            r"CALCULATE\s*\([^)]*CALCULATE\s*\(",
        ],
        "content": """
        Nested CALCULATE causes multiple context transitions:
        - Each CALCULATE creates a new filter context
        - Multiple transitions = performance overhead
        - Can produce unexpected results

        Optimization: Consolidate filters into single CALCULATE
        Before: CALCULATE(CALCULATE([Measure], Filter1), Filter2)
        After:  CALCULATE([Measure], Filter1, Filter2)
        """
    },

    "related_in_iterator": {
        "title": "RELATED in Iterators",
        "url": "https://www.sqlbi.com/articles/avoiding-related-in-iterators/",
        "patterns": [
            r"(SUMX|AVERAGEX|COUNTX)\s*\([^)]*RELATED\s*\(",
        ],
        "content": """
        Using RELATED in iterators causes row-by-row lookups:
        - Each row requires a relationship traversal
        - Cannot leverage relationship optimizations

        Optimization: Use TREATAS or expand table before iteration
        """
    },
}
