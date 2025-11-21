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
        "url": "https://learn.microsoft.com/en-us/power-bi/guidance/dax-avoid-avoid-filter-as-filter-argument",
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
        Source: Microsoft Learn Official Guidance
        """
    },

    "filter_all": {
        "title": "FILTER(ALL()) Anti-Pattern",
        "url": "https://www.daxpatterns.com/dynamic-segmentation/",
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

        Source: DAX Patterns - Dynamic Segmentation
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
        "url": "https://dax.guide/divide/",
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
        Source: DAX.Guide - DIVIDE function reference
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
        "url": "https://learn.microsoft.com/en-us/dax/best-practices/dax-countrows",
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
        Source: Microsoft Learn DAX Best Practices
        """
    },

    "measure_in_filter": {
        "title": "Measures in FILTER Predicates",
        "url": "https://www.daxpatterns.com/static-segmentation/",
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

        Source: DAX Patterns - Static Segmentation
        """
    },

    "unnecessary_iterators": {
        "title": "Unnecessary Iterator Functions",
        "url": "https://dax.guide/sumx/#when-to-use-sumx",
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

        Source: DAX.Guide - When to use SUMX
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

    # Additional sources beyond SQLBI
    "dax_patterns_time_intelligence": {
        "title": "Time Intelligence Patterns (DAX Patterns)",
        "url": "https://www.daxpatterns.com/time-intelligence/",
        "patterns": [
            r"(TOTALYTD|TOTALQTD|TOTALMTD)",
            r"DATESYTD|DATESQTD|DATESMTD",
            r"PREVIOUSYEAR|PREVIOUSQUARTER|PREVIOUSMONTH",
        ],
        "content": """
        Time Intelligence best practices from DAX Patterns:
        - Use CALCULATE with DATESINPERIOD for flexible time calculations
        - Avoid LASTDATE/FIRSTDATE in complex calculations
        - Consider calculation groups for time intelligence to reduce measure count
        - Use SAMEPERIODLASTYEAR for year-over-year comparisons
        """
    },

    "microsoft_dax_optimization": {
        "title": "DAX Query Optimization (Microsoft Learn)",
        "url": "https://learn.microsoft.com/en-us/power-bi/guidance/dax-avoid-avoid-filter-as-filter-argument",
        "patterns": [],  # General guidance
        "content": """
        Microsoft official DAX optimization guidance:
        - Avoid using FILTER as a CALCULATE filter argument
        - Use Boolean filter expressions instead of FILTER functions
        - Minimize the use of calculated columns
        - Prefer measures over calculated columns for aggregations
        """
    },

    "variable_best_practices": {
        "title": "DAX Variables Best Practices",
        "url": "https://learn.microsoft.com/en-us/dax/best-practices/dax-variables",
        "patterns": [
            r"\bVAR\b.*\bVAR\b.*\bVAR\b",  # Multiple VARs
        ],
        "content": """
        Variable usage best practices:
        - Use variables to avoid repeated calculation of the same expression
        - Variables are calculated once in the current filter context
        - Variables improve readability and maintainability
        - Use descriptive variable names (not V1, V2, etc.)
        - Variables reduce query complexity and improve performance

        Source: Microsoft Learn - Use variables to improve DAX formulas
        """
    },

    "addcolumns_in_measure": {
        "title": "Avoid AddColumns in Measure Expressions",
        "url": "https://learn.microsoft.com/en-us/dax/best-practices/",
        "patterns": [
            r"ADDCOLUMNS\s*\(",
        ],
        "content": """
        AddColumns in measures creates nested iterations:
        - Measures are calculated iteratively by default
        - Using ADDCOLUMNS inside measures creates nested iterations
        - This negatively affects report performance

        Alternative: Use variables or separate measures
        """
    },

    "calculate_keepfilters": {
        "title": "Use KEEPFILTERS for Better Filter Management",
        "url": "https://www.sqlbi.com/articles/using-keepfilters-in-dax/",
        "patterns": [
            r"CALCULATE\s*\([^)]*,\s*FILTER\s*\(",
        ],
        "content": """
        KEEPFILTERS offers valuable alternative for filter management:
        - Preserves existing filters instead of overwriting them
        - Provides more granular control over filtering
        - Often better than using FILTER in CALCULATE

        Example: CALCULATE([Sales], KEEPFILTERS(Product[Category] = "Electronics"))
        """
    },

    "formula_engine_storage_engine": {
        "title": "Understanding Formula Engine vs Storage Engine",
        "url": "https://www.sqlbi.com/articles/formula-engine-and-storage-engine-in-dax/",
        "patterns": [],
        "content": """
        Two engines execute DAX queries:

        Formula Engine (FE):
        - Single-threaded, no cache
        - Handles complex logic and expressions
        - Slower for large datasets

        Storage Engine (SE):
        - Multi-threaded, optimized for speed
        - Handles simple joins, grouping, filters, aggregations
        - Uses compressed VertiPaq data

        Best Practice: Maximize allocation to Storage Engine (ideal: 80% SE, 20% FE)
        """
    },

    "blank_vs_zero": {
        "title": "BLANK vs ZERO: Proper Handling",
        "url": "https://www.sqlbi.com/articles/blank-handling-in-dax/",
        "patterns": [
            r"=\s*0(?!\d)",  # = 0 comparisons
        ],
        "content": """
        BLANK and ZERO are semantically different:
        - BLANK: Absence of information
        - ZERO: Numeric value of zero

        Best Practices:
        - Don't replace BLANKs with zeros unnecessarily
        - Use ISBLANK() or == operator to check for BLANK
        - Avoid +0 pattern to force zeros (affects query optimizer)
        - BLANK improves query optimization by eliminating unnecessary scans

        Performance Impact: Converting BLANKs to zeros prevents Power BI from filtering unwanted rows
        """
    },

    "iferror_iserror": {
        "title": "Avoid IFERROR/ISERROR Functions",
        "url": "https://learn.microsoft.com/en-us/dax/best-practices/dax-error-functions",
        "patterns": [
            r"\bIFERROR\s*\(",
            r"\bISERROR\s*\(",
        ],
        "content": """
        IFERROR/ISERROR force step-by-step execution:
        - Forces Power BI to enter step-by-step execution for each row
        - Significantly impacts performance

        Better Alternatives:
        - Use IF with logical tests (no error needs to be raised)
        - Use DIVIDE function instead of manual division with error handling
        - Use functions with built-in error handling (FIND has default parameter)

        Example: Instead of IFERROR([Value]/[Divisor], 0), use DIVIDE([Value], [Divisor], 0)
        """
    },

    "bidirectional_relationships": {
        "title": "Bidirectional Relationships Guidance",
        "url": "https://learn.microsoft.com/en-us/power-bi/guidance/relationships-bidirectional-filtering",
        "patterns": [],
        "content": """
        Bidirectional relationships can impact performance and create ambiguity:

        When to Use:
        - Many-to-many relationships between dimensions (recommended approach)
        - Specific scenarios requiring filter propagation in both directions

        Risks:
        - Negatively impacts model query performance
        - Can create ambiguous paths and unpredictable results
        - May confuse report users

        Alternative: Use CROSSFILTER function in DAX for specific calculations instead of permanent bidirectional relationships
        """
    },

    "time_intelligence_calc_groups": {
        "title": "Time Intelligence with Calculation Groups",
        "url": "https://www.daxpatterns.com/standard-time-related-calculations/",
        "patterns": [
            r"(TOTALYTD|TOTALQTD|TOTALMTD|SAMEPERIODLASTYEAR|DATESYTD)",
        ],
        "content": """
        Calculation Groups eliminate measure explosion:

        Before: 7 measures × 13 time variations = 91 measures
        After: 7 measures + 1 calculation group = 7 measures

        Benefits:
        - Use SELECTEDMEASURE() to apply time intelligence dynamically
        - Cross-join multiple calculation groups for combinations
        - Supported in Power BI Premium, Azure AS, SQL Server 2019+

        Best Practices:
        - Use built-in DAX time intelligence functions for standard calendars
        - Use custom DAX logic for fiscal calendars starting in non-standard months
        """
    },

    "directquery_optimization": {
        "title": "DirectQuery Optimization",
        "url": "https://learn.microsoft.com/en-us/power-bi/connect-data/desktop-directquery-about",
        "patterns": [],
        "content": """
        DirectQuery specific optimizations:

        Query Folding:
        - Keep Power Query transformations simple and foldable
        - Preview "View Native Query" often to verify folding
        - Avoid complex transformations that can't be translated to SQL

        DAX Considerations:
        - Each measure creates a query to the data source
        - Calculated columns are evaluated at query time (not cached)
        - Minimize number of measures and complexity

        Best Practices:
        - Use query folding wherever possible
        - Push filters to the data source
        - Reduce data transferred from source
        - Analyze queries with DAX Studio
        """
    },

    "measure_design_practices": {
        "title": "Measure Design Best Practices",
        "url": "https://medium.com/@simon.harrison_Select_Distinct/best-practices-for-using-explicit-measures-in-power-bi-f23d60b7cbcd",
        "patterns": [],
        "content": """
        Measure design guidelines:

        Naming Conventions:
        - Use clear, descriptive names (Total Sales not TtlSales)
        - Avoid abbreviations for Q&A compatibility
        - Be consistent across all measures
        - Use business terminology, not technical terms

        Organization:
        - Create dedicated measure tables
        - Use display folders hierarchically
        - Group related measures together

        Variable Naming:
        - Use descriptive multi-word names to avoid conflicts with table names
        - Avoid generic names like Temp, Var1, V1
        - Make purpose clear from the name
        """
    },

    "summarize_addcolumns": {
        "title": "SUMMARIZE with ADDCOLUMNS Performance",
        "url": "https://www.sqlbi.com/articles/summarizecolumns-best-practices/",
        "patterns": [
            r"SUMMARIZE\s*\([^)]*ADDCOLUMNS",
        ],
        "content": """
        SUMMARIZE with ADDCOLUMNS optimization:

        Performance:
        - SUMMARIZE leverages VertiPaq Storage Engine for rapid table creation
        - Most performant approach for complex calculations
        - Better than iterating with FILTER

        Best Practice (2025):
        - SUMMARIZECOLUMNS can now be used in measures
        - Follow best practices to avoid incorrect results
        - Use SUMMARIZE+ADDCOLUMNS for on-the-fly table creation with calculations
        """
    },
}
