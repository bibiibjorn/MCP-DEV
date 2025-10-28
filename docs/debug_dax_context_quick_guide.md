# Debug DAX Context - Quick Reference Guide

## Overview

The `debug_dax_context` tool helps you understand how DAX evaluates your expressions step-by-step, showing exactly where context transitions occur.

## Quick Start

### Basic Usage

```json
{
  "expression": "CALCULATE([Net Sales], d_Date[YearSortnr]=2024)"
}
```

This gives you a beautiful, easy-to-read analysis with emojis and explanations.

## Output Formats

### 1. Friendly Format (Default) ⭐

**Best for:** Learning, sharing, understanding

```json
{
  "expression": "CALCULATE([Net Sales], d_Date[YearSortnr]=2024)",
  "format": "friendly"
}
```

**What you get:**
- 🔍 Clear headers and sections
- 📍 Visual pointers showing execution position
- 🔄 Context information (filter and row context)
- 📖 Plain English explanations
- 💡 Key takeaways and tips
- ⏱️ Performance information (when available)

### 2. Steps Format

**Best for:** Programmatic access, custom processing

```json
{
  "expression": "CALCULATE([Net Sales], d_Date[YearSortnr]=2024)",
  "format": "steps"
}
```

**What you get:**
- Raw JSON with step-by-step data
- Code fragments
- Context information
- Explanations
- Easy to parse for automation

### 3. Report Format

**Best for:** Deep analysis, optimization, performance tuning

```json
{
  "expression": "SUMX(Sales, [Total] * [Rate])",
  "format": "report",
  "include_optimization": true,
  "include_profiling": true
}
```

**What you get:**
- Complete context analysis
- Complexity score
- Nesting level analysis
- Performance warnings
- Optimization suggestions with code examples
- Best practice recommendations

## Understanding the Output

### The ▶ Pointer

```
CALCULATE( ▶ [Net Sales], d_Date[YearSortnr
```

The ▶ arrow shows **exactly** where DAX is evaluating at that step.

### Context Types

**Filter Context:**
- Active filters from slicers, visuals, or CALCULATE
- Controls which rows are visible for aggregation
- Example: "Year = 2024"

**Row Context:**
- When iterating over table rows
- Created by iterator functions (SUMX, FILTER, etc.)
- Each row is evaluated individually

### Context Transitions

**What are they?**
Context transitions occur when DAX switches between filter context and row context.

**Common causes:**
- `CALCULATE()` - creates/modifies filter context
- Iterator functions - create row context
- Measure references - cause implicit CALCULATE

**Why care?**
- Each transition has a performance cost
- Understanding them helps write efficient DAX
- Prevents unexpected results

## Common Use Cases

### 1. Understanding Why a Measure is Slow

```json
{
  "expression": "SUMX(Sales, [Complex Measure])",
  "format": "report"
}
```

Look for:
- Multiple nested context transitions
- Measure references inside iterators
- Deep CALCULATE nesting

### 2. Learning DAX Concepts

```json
{
  "expression": "CALCULATE([Total], Table[Column] = \"Value\")",
  "format": "friendly"
}
```

The friendly format explains each step in plain English.

### 3. Debugging Unexpected Results

```json
{
  "expression": "Your problematic DAX here",
  "format": "friendly"
}
```

See exactly what context is active at each step.

### 4. Optimizing Complex Measures

```json
{
  "expression": "Your complex DAX here",
  "format": "report",
  "include_optimization": true
}
```

Get specific suggestions for improvement with code examples.

## Performance Tips

Based on the analysis, here are common optimizations:

### ❌ Avoid: Measure References in Iterators

```dax
SUMX(Sales, [Total Sales] * [Tax Rate])  // Bad: context transition per row
```

### ✅ Better: Use Columns

```dax
SUMX(Sales, Sales[Amount] * Sales[TaxRate])  // Good: no transitions
```

### ❌ Avoid: Deep CALCULATE Nesting

```dax
CALCULATE(
    CALCULATE(
        CALCULATE([Measure], Filter1),
        Filter2
    ),
    Filter3
)
```

### ✅ Better: Use Variables

```dax
VAR Step1 = CALCULATE([Measure], Filter1)
VAR Step2 = CALCULATE(Step1, Filter2)
RETURN CALCULATE(Step2, Filter3)
```

## Icon Reference

| Icon | Meaning |
|------|---------|
| 🔍 | Analysis/Debugging |
| 📝 | Your expression |
| 🎯 | Summary/Results |
| 📍 | Execution point |
| 🔄 | Context information |
| 📖 | Explanation |
| ⏱️ | Timing/Performance |
| ✅ | Success/Complete |
| 💡 | Tips/Insights |
| ℹ️ | Information |
| ⚠️ | Warning |
| 🔴 | Critical |
| 🟡 | Warning |
| 🔵 | Info |

## Advanced Options

### Breakpoints (Advanced)

```json
{
  "expression": "Long complex DAX...",
  "breakpoints": [45, 120, 200]
}
```

Pauses analysis at specific character positions (for very complex expressions).

### Control Profiling

```json
{
  "expression": "Your DAX",
  "format": "report",
  "include_profiling": false,
  "include_optimization": false
}
```

Get just the context analysis without extra suggestions.

## Examples

### Example 1: Simple CALCULATE

**Input:**
```json
{
  "expression": "CALCULATE([Sales], Year[Year] = 2024)"
}
```

**Key Finding:**
- One context transition (CALCULATE)
- Filter applied to Year table
- Measure [Sales] evaluated in new filter context

### Example 2: Iterator with Measure

**Input:**
```json
{
  "expression": "SUMX(Products, [Unit Price] * [Quantity])",
  "format": "report"
}
```

**Key Finding:**
- Row context created by SUMX
- Two measure references cause context transitions per row
- Suggestion: Use columns instead if possible

### Example 3: Complex Nested Expression

**Input:**
```json
{
  "expression": "CALCULATE([Sales], FILTER(ALL(Date), Date[Year] = 2024))",
  "format": "report"
}
```

**Key Finding:**
- Multiple context transitions
- ALL removes existing filter context
- FILTER creates row context
- CALCULATE applies new filter

## Troubleshooting

### "No context transitions detected"

This is actually good! Your DAX is simple and efficient.

### "High complexity score"

Consider breaking the measure into smaller sub-measures.

### "Excessive CALCULATE nesting"

Use variables (VAR) to reduce nesting depth.

### "Multiple iterators with measure references"

Each measure reference in an iterator causes a context transition per row. Use columns when possible.

## Related Tools

- `analyze_dax_context` - Quick context analysis
- `visualize_filter_context` - Visual diagrams of context flow
- `run_dax` with `mode="profile"` - Actual execution timing

## Getting Help

If you need more explanation:
1. Start with `format="friendly"` to understand the basics
2. Use `format="report"` to get optimization suggestions
3. Check the explanations for each step
4. Look at the key takeaways at the end

The tool is designed to teach you DAX while debugging!
