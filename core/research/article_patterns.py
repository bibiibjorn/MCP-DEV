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
        1. Identify anti-patterns (SUMX+FILTER, nested CALCULATE, FILTER+ALL, etc.)
        2. Analyze context transitions and their performance impact
        3. Minimize row-by-row operations by using CALCULATE instead of iterators
        4. Consolidate filters to reduce context transitions
        5. Use variables (VAR) to cache intermediate results and reduce repeated calculations
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
        Before: SUMX(Sales, Sales[Qty] * RELATED(Product[Price]))
        After:  SUMX(Sales, Sales[Qty] * Sales[UnitPrice]) -- if denormalized
        Or:     Use NATURALLEFTOUTERJOIN to expand table before iteration
        """
    },

    "divide_zero_check": {
        "title": "DIVIDE vs Manual Division with Error Handling",
        "url": "https://www.sqlbi.com/articles/understanding-divide-performance/",
        "patterns": [
            r"IF\s*\([^=]+\s*=\s*0\s*,\s*[^,]+\s*,\s*[^/]+\s*/\s*[^)]+\)",
        ],
        "content": """
        Manual zero-division checks are less efficient than DIVIDE:
        - IF(...=0, ..., .../...) evaluated in Formula Engine
        - DIVIDE optimized by Storage Engine

        Optimization: Use DIVIDE function
        Before: IF([Denominator] = 0, 0, [Numerator] / [Denominator])
        After:  DIVIDE([Numerator], [Denominator], 0)

        Expected improvement: 2-3x performance gain
        """
    },

    "values_in_calculate": {
        "title": "VALUES in CALCULATE Filter Arguments",
        "url": "https://www.sqlbi.com/articles/optimizing-values-performance/",
        "patterns": [
            r"CALCULATE\s*\([^)]*,\s*VALUES\s*\(",
        ],
        "content": """
        Using VALUES in CALCULATE filter arguments can be inefficient:
        - May cause unnecessary context transitions
        - Can be replaced with direct column references

        Optimization: Use column references directly
        Before: CALCULATE([Sales], VALUES(Product[Category]))
        After:  CALCULATE([Sales], Product[Category])
        """
    },

    "countrows_filter": {
        "title": "COUNTROWS(FILTER()) Optimization",
        "url": "https://www.sqlbi.com/articles/optimizing-countrows-filter/",
        "patterns": [
            r"COUNTROWS\s*\(\s*FILTER\s*\(",
        ],
        "content": """
        COUNTROWS(FILTER()) forces row-by-row evaluation:
        - Cannot use xVelocity compression
        - Prevents parallelization

        Optimization: Use CALCULATE(COUNTROWS(...), filters)
        Before: COUNTROWS(FILTER(Table, Table[Column] > 100))
        After:  CALCULATE(COUNTROWS(Table), Table[Column] > 100)

        Expected improvement: 5-10x performance gain
        """
    },

    "measure_in_filter": {
        "title": "Measures in FILTER Predicates",
        "url": "https://www.sqlbi.com/articles/avoiding-measures-in-filter/",
        "patterns": [
            r"FILTER\s*\([^)]*,\s*\[[^\]]+\]\s*[><!=]",
        ],
        "content": """
        Using measures in FILTER predicates causes row-by-row context transitions:
        - Each row creates filter context for measure evaluation
        - Blocks Storage Engine optimization

        Optimization: Pre-calculate measure or use column references
        Before: FILTER(Products, [Total Sales] > 1000)
        After:  VAR Threshold = 1000
                RETURN FILTER(Products, Products[Sales] > Threshold)
        """
    },

    "unnecessary_iterators": {
        "title": "Unnecessary Iterator Functions",
        "url": "https://www.sqlbi.com/articles/when-to-use-iterators/",
        "patterns": [
            r"SUMX\s*\([^,]+,\s*[^\[]*\[[^\]]+\]\s*\)",  # SUMX without actual iteration expression
        ],
        "content": """
        Using iterators when simple aggregations suffice:
        - Iterators have overhead even for simple cases
        - Direct aggregation functions are faster

        Optimization: Use direct aggregation when possible
        Before: SUMX(Table, Table[Amount])
        After:  SUM(Table[Amount])

        Before: AVERAGEX(Table, Table[Value])
        After:  AVERAGE(Table[Value])
        """
    },

    "multiple_context_transitions": {
        "title": "Multiple Measure References in Single Expression",
        "url": "https://www.sqlbi.com/articles/context-transition-and-filters/",
        "patterns": [
            r"\[[^\]]+\]\s*[\+\-\*/]\s*\[[^\]]+\].*\[[^\]]+\]",  # Multiple measure references
        ],
        "content": """
        Multiple measure references cause multiple context transitions:
        - Each measure reference creates implicit CALCULATE
        - Can be optimized by caching results

        Optimization: Use variables to cache measure results
        Before: [Measure1] + [Measure2] + [Measure3]
        After:  VAR M1 = [Measure1]
                VAR M2 = [Measure2]
                VAR M3 = [Measure3]
                RETURN M1 + M2 + M3
        """
    },
}
