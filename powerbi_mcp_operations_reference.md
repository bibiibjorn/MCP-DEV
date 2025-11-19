# Microsoft Official Power BI MCP Server - Operations Reference Guide

## Overview
This document provides detailed technical reference for implementing Power BI MCP operations based on real-world usage patterns. Each operation includes the exact request structure, parameters, response format, and implementation notes.

---

## Table of Contents
1. [Connection Operations](#connection-operations)
2. [Model Operations](#model-operations)
3. [Table Operations](#table-operations)
4. [Measure Operations](#measure-operations)
5. [Relationship Operations](#relationship-operations)
6. [Calculation Group Operations](#calculation-group-operations)

---

## Connection Operations

### 1. List Local Instances

**Purpose**: Detect all running Power BI Desktop and Analysis Services instances on the local machine.

**Operation Name**: `connection_operations`

**Request Structure**:
```json
{
  "operation": "ListLocalInstances"
}
```

**Parameters**:
- None required

**Response Structure**:
```json
{
  "success": true,
  "message": "Found 1 local PowerBI Desktop and Analysis Services instances",
  "operation": "ListLocalInstances",
  "data": [
    {
      "processId": 16552,
      "port": 64960,
      "connectionString": "Data Source=localhost:64960;Application Name=MCP-PBIModeling",
      "parentProcessName": "PBIDesktop",
      "parentWindowTitle": "Financial Reporting - Concept version - VSB as source_10132025",
      "startTime": "2025-11-19T11:15:07.1340367+01:00"
    }
  ]
}
```

**Response Fields Explained**:
- `processId`: Windows process ID of the Power BI Desktop instance
- `port`: Local Analysis Services port (typically 6XXXX range)
- `connectionString`: Full connection string for XMLA endpoint
- `parentProcessName`: Always "PBIDesktop" for Power BI Desktop
- `parentWindowTitle`: Window title showing the .pbix file name
- `startTime`: ISO 8601 timestamp when the instance started

**Implementation Notes**:
1. Scans for all PBIDesktop.exe processes
2. Queries each process for embedded Analysis Services port
3. Extracts window title to identify which .pbix file is open
4. Returns empty array if no instances found
5. No authentication required for local instances

**Use Cases**:
- Initial connection discovery
- Multi-model detection (when multiple .pbix files are open)
- Health checks to verify Power BI Desktop is running

---

### 2. Connect to Instance

**Purpose**: Establish connection to a specific Power BI Desktop instance.

**Operation Name**: `connection_operations`

**Request Structure**:
```json
{
  "operation": "Connect",
  "dataSource": "localhost:64960"
}
```

**Parameters**:
- `dataSource` (string, required): Server and port in format "localhost:{port}"
  - Extract port from `ListLocalInstances` response
  - Example: "localhost:64960"

**Response Structure**:
```json
{
  "success": true,
  "message": "Connection 'PBIDesktop-Financial Reporting - Concept version - VSB as source_10132025-64960' established successfully",
  "operation": "Connect",
  "data": "PBIDesktop-Financial Reporting - Concept version - VSB as source_10132025-64960"
}
```

**Response Fields Explained**:
- `data`: Connection name/identifier for this session
  - Format: "PBIDesktop-{FileTitle}-{Port}"
  - Used to reference this connection in subsequent operations

**Implementation Notes**:
1. Creates XMLA connection to Analysis Services embedded in Power BI Desktop
2. Uses Windows authentication (current user context)
3. Connection name includes model name and port for identification
4. Connection persists for the MCP server session
5. Multiple connections can be maintained simultaneously

**Error Scenarios**:
- Port not accessible: `"Connection failed: Unable to connect to server"`
- Power BI Desktop closed: `"Connection lost"`
- Invalid port format: `"Invalid data source format"`

**Use Cases**:
- Initial connection after discovery
- Reconnection after Power BI Desktop restart
- Switching between multiple open models

---

## Model Operations

### 3. Get Model Statistics

**Purpose**: Retrieve comprehensive model metadata and object counts.

**Operation Name**: `model_operations`

**Request Structure**:
```json
{
  "operation": "GetStats"
}
```

**Parameters**:
- `connectionName` (string, optional): Uses last connected instance if not provided

**Response Structure**:
```json
{
  "success": true,
  "message": "Retrieved model statistics successfully",
  "operation": "GETSTATS",
  "modelName": "Model",
  "data": {
    "ModelName": "Model",
    "DatabaseName": "edb241b5-77e6-42a5-8199-67fc2c6224bd",
    "CompatibilityLevel": 1601,
    "TableCount": 109,
    "TotalMeasureCount": 239,
    "TotalColumnCount": 833,
    "TotalPartitionCount": 109,
    "RelationshipCount": 91,
    "RoleCount": 1,
    "DataSourceCount": 0,
    "CultureCount": 1,
    "PerspectiveCount": 0,
    "Tables": [
      {
        "name": "d_Company",
        "columnCount": 6,
        "measureCount": 0,
        "partitionCount": 1,
        "isHidden": false
      },
      {
        "name": "m_Measures",
        "columnCount": 1,
        "measureCount": 224,
        "partitionCount": 1,
        "isHidden": false
      }
      // ... additional tables
    ]
  }
}
```

**Response Fields Explained**:

**Model-Level Fields**:
- `ModelName`: Display name of the semantic model (typically "Model")
- `DatabaseName`: GUID identifier for the database
- `CompatibilityLevel`: Tabular model compatibility level
  - 1601 = Power BI Desktop (SQL Server 2019+)
  - 1200 = SQL Server 2016
  - Higher numbers = newer features available

**Aggregate Counts**:
- `TableCount`: Total tables (including hidden)
- `TotalMeasureCount`: All measures across all tables
- `TotalColumnCount`: All columns (data + calculated)
- `TotalPartitionCount`: Typically equals TableCount (one partition per table)
- `RelationshipCount`: All relationships (active + inactive)
- `RoleCount`: Row-level security roles
- `DataSourceCount`: External data sources (0 for import models in PBI Desktop)
- `CultureCount`: Translations (typically 1 for default)
- `PerspectiveCount`: Perspectives for simplifying model views

**Per-Table Information**:
- `name`: Table name (includes prefixes like d_, f_, s_, m_)
- `columnCount`: Total columns (including calculated columns)
- `measureCount`: Measures defined in this table
- `partitionCount`: Data partitions (typically 1)
- `isHidden`: Visibility in client tools

**Implementation Notes**:
1. Queries DMV (Dynamic Management Views) for metadata
2. Fast operation - retrieves counts only, no data
3. Does not require data refresh
4. Useful for model health checks and documentation

**Compatibility Level Reference**:
- 1200: SQL Server 2016, Power BI Desktop (basic)
- 1400: SQL Server 2017, Power BI Desktop (objects level security)
- 1500: SQL Server 2019, Power BI Desktop (calculation groups)
- 1600: Power BI Desktop (2021+, enhanced calculation groups)
- 1601: Current Power BI Desktop

**Use Cases**:
- Model documentation generation
- Health check dashboards
- Complexity assessment (table/measure counts)
- Version detection (compatibility level)

---

## Table Operations

### 4. List All Tables

**Purpose**: Get list of all tables with basic metadata.

**Operation Name**: `table_operations`

**Request Structure**:
```json
{
  "operation": "List"
}
```

**Parameters**:
- `connectionName` (string, optional): Connection identifier

**Response Structure**:
```json
{
  "success": true,
  "message": "Found 109 tables",
  "operation": "List",
  "data": [
    {
      "columnCount": 5,
      "partitionCount": 1,
      "name": "d_Company"
    },
    {
      "columnCount": 30,
      "partitionCount": 1,
      "name": "f_FINREP"
    },
    {
      "columnCount": 0,
      "measureCount": 224,
      "partitionCount": 1,
      "name": "m_Measures"
    }
    // ... additional tables
  ]
}
```

**Response Fields Explained**:
- `columnCount`: Number of columns (data + calculated)
- `measureCount`: Measures in this table (only if > 0)
- `partitionCount`: Data partitions
- `name`: Table name

**Table Naming Conventions (Common Patterns)**:
- `d_*`: Dimension tables (e.g., d_Company, d_Date)
- `f_*`: Fact tables (e.g., f_FINREP, f_Aging_Customer)
- `m_*`: Measure tables (e.g., m_Measures)
- `s_*`: Support/slicer tables (e.g., s_ReportLines, s_Period)
- `c_*`: Calculation groups (e.g., c_Time Intelligence P&L)
- `sfp_*`: Slicer field parameters (e.g., sfp_Reported Amount)
- `dfp_*`: Dynamic field parameters (e.g., dfp_dyn_Column)
- `r_*`: RLS (Row-Level Security) tables (e.g., r_RLS_Country)
- `dyn_*`: Dynamic tables (e.g., dyn_RowLevel_1)

**Implementation Notes**:
1. Returns all tables in model order
2. Includes hidden tables
3. Measure-only tables show columnCount: 0
4. Fast operation - metadata only

**Use Cases**:
- Table inventory
- Identifying measure tables
- Model structure analysis
- Documentation generation

---

## Relationship Operations

### 5. List All Relationships

**Purpose**: Retrieve all relationships with full metadata.

**Operation Name**: `relationship_operations`

**Request Structure**:
```json
{
  "operation": "List"
}
```

**Parameters**:
- `connectionName` (string, optional): Connection identifier

**Response Structure**:
```json
{
  "success": true,
  "message": "Found 91 relationships",
  "operation": "LIST",
  "data": [
    {
      "fromTable": "f_FINREP",
      "fromColumn": "#Company Code",
      "toTable": "d_Company",
      "toColumn": "Company Code",
      "isActive": true,
      "crossFilteringBehavior": "OneDirection",
      "fromCardinality": "Many",
      "toCardinality": "One",
      "name": "70c38ab1-00b9-bb04-7903-4027e569f76e"
    },
    {
      "fromTable": "f_FINREP",
      "fromColumn": "Document Currency",
      "toTable": "d_Currency_From",
      "toColumn": "From currency",
      "isActive": false,
      "crossFilteringBehavior": "OneDirection",
      "fromCardinality": "Many",
      "toCardinality": "One",
      "name": "670d53a0-f8fd-c28a-512f-d95e13a95e13"
    },
    {
      "fromTable": "s_Period",
      "fromColumn": "Year Month Seqnr",
      "toTable": "sfp_BS_Reported",
      "toColumn": "Value4",
      "isActive": true,
      "crossFilteringBehavior": "BothDirections",
      "fromCardinality": "One",
      "toCardinality": "One",
      "name": "0e81395e-a97a-d5b3-8e93-a8c29ca137fd"
    }
  ]
}
```

**Response Fields Explained**:

**Direction Fields**:
- `fromTable`: Source table (typically fact table)
- `fromColumn`: Source column
- `toTable`: Target table (typically dimension table)
- `toColumn`: Target column

**Relationship Properties**:
- `isActive`: Whether relationship is active
  - `true`: Used automatically in calculations
  - `false`: Must use USERELATIONSHIP() in DAX
- `crossFilteringBehavior`: Filter propagation direction
  - `"OneDirection"`: Filters flow from "to" → "from" (standard)
  - `"BothDirections"`: Filters flow in both directions (use carefully)
- `fromCardinality`: Source cardinality
  - `"Many"`: Multiple rows (typical for fact tables)
  - `"One"`: Unique values (typical for dimensions)
- `toCardinality`: Target cardinality
  - `"One"`: Dimension table (unique keys)
  - `"Many"`: Many-to-many relationship
- `name`: GUID identifier for the relationship

**Relationship Types**:

**1. Many-to-One (Standard Star Schema)**:
```json
{
  "fromCardinality": "Many",
  "toCardinality": "One",
  "crossFilteringBehavior": "OneDirection"
}
```
- Most common: Fact → Dimension
- Example: f_FINREP[Company Code] → d_Company[Company Code]

**2. Many-to-Many**:
```json
{
  "fromCardinality": "Many",
  "toCardinality": "Many",
  "crossFilteringBehavior": "OneDirection"
}
```
- Used for complex filtering scenarios
- Example: Field parameters to scenario tables
- Performance consideration: Can be expensive

**3. One-to-One with Bidirectional**:
```json
{
  "fromCardinality": "One",
  "toCardinality": "One",
  "crossFilteringBehavior": "BothDirections"
}
```
- Rare but powerful
- Example: s_Period ↔ sfp_BS_Reported
- Use case: Balance sheet time filtering

**4. Inactive Relationships**:
```json
{
  "isActive": false
}
```
- Role-playing dimensions
- Example: Document Currency vs Company Currency
- Used with USERELATIONSHIP() in DAX

**Implementation Notes**:
1. Returns all relationships (active + inactive)
2. GUID names are auto-generated by Power BI
3. Relationship order is not guaranteed
4. Hidden tables still show relationships

**Common Patterns**:

**Role-Playing Dimensions**:
```
Active:   f_FINREP[Company Code Currency] → d_Currency_From[From currency]
Inactive: f_FINREP[Document Currency] → d_Currency_From[From currency]
```

**Field Parameter Pattern**:
```
Many-to-Many: sfp_Reported Amount[Scenario] → d_Scenario[Version]
```

**RLS Pattern**:
```
Many-to-Many: d_Country[Country ID] → r_RLS_Country[Country ID]
```

**Use Cases**:
- Model diagram generation
- Relationship quality assessment
- Inactive relationship detection
- Many-to-many identification
- Bidirectional filter detection

---

## Measure Operations

### 6. List Measures by Table

**Purpose**: Get list of measures with optional table filter.

**Operation Name**: `measure_operations`

**Request Structure**:
```json
{
  "operation": "List",
  "tableName": "m_Measures",
  "maxResults": 30
}
```

**Parameters**:
- `tableName` (string, optional): Filter by specific table
- `maxResults` (integer, optional): Limit results (useful for large models)

**Response Structure**:
```json
{
  "success": true,
  "message": "Found 30 measures in table 'm_Measures'",
  "operation": "List",
  "tableName": "m_Measures",
  "data": [
    {
      "displayFolder": "Financial Model\\1.3 Base measures Balance Sheet",
      "name": "PL-COL-Background"
    },
    {
      "displayFolder": "Financial Model\\1.1 Base measures P&L\\Scenario Comparable",
      "name": "PL-AMT-BASE Scenario"
    },
    {
      "displayFolder": "Financial Model\\1.2 Profit & Loss\\1.2.1 P&L Base",
      "name": "PL-AMT-TC0 Reported"
    }
  ],
  "warnings": [
    "Results truncated: Showing 30 of 224 measures (limited by MaxResults=30)"
  ]
}
```

**Response Fields Explained**:
- `displayFolder`: Folder path for organization (uses `\\` separator)
- `name`: Measure name
- `warnings`: Array of informational messages (e.g., truncation)

**Display Folder Patterns**:
- Uses backslash separator: `"Parent\\Child\\Grandchild"`
- Empty string = root level
- Common patterns:
  - `"Financial Model\\1.1 Base measures P&L\\..."`
  - `"Financial Model\\1.2 Profit & Loss\\..."`
  - `"Financial Model\\9.9 Other"` (miscellaneous)

**Implementation Notes**:
1. Returns measures in model order (not alphabetical)
2. Without `tableName`, returns all measures from all tables
3. `maxResults` prevents overwhelming response size
4. Hidden measures are included
5. Does not return DAX expressions (use Get operation for that)

**Use Cases**:
- Measure inventory
- Folder structure analysis
- Measure naming convention review
- Finding specific measure location

---

### 7. Get Measure Details

**Purpose**: Retrieve complete measure definition including DAX expression.

**Operation Name**: `measure_operations`

**Request Structure**:
```json
{
  "operation": "Get",
  "tableName": "m_Measures",
  "measureName": "PL-AMT-BASE Scenario"
}
```

**Parameters**:
- `tableName` (string, required): Table containing the measure
- `measureName` (string, required): Exact measure name

**Response Structure**:
```json
{
  "success": true,
  "message": "Measure 'PL-AMT-BASE Scenario' retrieved successfully",
  "operation": "Get",
  "measureName": "PL-AMT-BASE Scenario",
  "tableName": "m_Measures",
  "data": {
    "tableName": "m_Measures",
    "name": "PL-AMT-BASE Scenario",
    "expression": "\n-- OPTIMIZATION NOTES:\n-- 1. Replaced FILTER with CALCULATETABLE for better query folding\n-- 2. Early exit for blank denominator (skip unnecessary work)\n-- 3. Consolidated denominator calculation using same helper function\n-- 4. Reduced variable overhead\n\n-- Get report configuration\nVAR DenominatorLine = SELECTEDVALUE('s_ReportLines'[Denominator])\nVAR ReportSign = SELECTEDVALUE('s_ReportLines'[Sign])\nVAR SelectedFormulaElement = SELECTEDVALUE('s_ReportLines'[Nominator element])\n\n-- Calculate sign multiplier\nVAR SignMultiplier = IF(ReportSign <> \"Keep\", -1, 1)\n\n-- Get numerator formula components (optimized filter)\nVAR NumeratorComponents = \n    CALCULATETABLE(\n        's_Formulas Combined',\n        's_Formulas Combined'[Formula Header] = SelectedFormulaElement\n    )\n\n-- Calculate numerator\nVAR NumeratorValue = \n    SignMultiplier * SUMX(\n        NumeratorComponents,\n        [PL-AMT-BASE Scenario Amount - Currency]\n    )\n\n-- Early exit if no denominator (most common case)\nVAR Result =\n    IF(\n        ISBLANK(DenominatorLine),\n        NumeratorValue,\n        -- Calculate denominator only when needed\n        VAR DenominatorComponents = \n            CALCULATETABLE(\n                's_Formulas Combined',\n                's_Formulas Combined'[Formula Header] = DenominatorLine\n            )\n        VAR DenominatorValue =\n            SUMX(\n                DenominatorComponents,\n                [PL-AMT-BASE Scenario Amount - Currency]\n            )\n        RETURN DIVIDE(NumeratorValue, DenominatorValue, 0)\n    )\n\nRETURN Result",
    "description": "",
    "formatString": "",
    "isHidden": false,
    "isSimpleMeasure": false,
    "displayFolder": "Financial Model\\1.1 Base measures P&L\\Scenario Comparable",
    "dataType": "Variant",
    "dataCategory": "",
    "lineageTag": "47d82f22-17e0-4a57-b117-b6b41aec01d1",
    "sourceLineageTag": "",
    "formatStringExpression": "VAR vLineformat = SELECTEDVALUE(s_ReportLines[Number Format])\nVAR vScale =  SELECTEDVALUE(s_Scale2[Nr])\nVAR vScaleSymbol = SELECTEDVALUE( s_Scale2[Display] )\nVAR vDecimal =  SELECTEDVALUE(s_Decimal2[Nr])\nVAR vDecimalPct =  SELECTEDVALUE(s_Decimalpct2[Nr])\nVAR vResult = CALCULATE(SELECTEDVALUE(s_Format2[Format]),\ns_Format2[Line Format] = vLineformat,\ns_Format2[Scale] = vScale, \ns_Format2[Decimal] = vDecimal,\ns_Format2[Decimal Pct] = vDecimalPct)\nRETURN\nvResult ",
    "annotations": [],
    "extendedProperties": [],
    "state": "Ready",
    "errorMessage": "",
    "modifiedTime": "2025-11-19T12:07:06.233333",
    "structureModifiedTime": "2025-08-29T14:48:39.883333"
  }
}
```

**Response Fields Explained**:

**Core Fields**:
- `expression`: Full DAX formula (multi-line string)
- `name`: Measure name
- `tableName`: Parent table
- `displayFolder`: Organization folder path

**Metadata Fields**:
- `description`: User-defined description (often empty)
- `dataType`: Return type
  - `"Variant"`: Default, type determined at runtime
  - `"Integer"`, `"Double"`, `"String"`, `"Boolean"`, `"DateTime"`
- `dataCategory`: Semantic type (e.g., "WebURL", "ImageURL", "Latitude")
- `isHidden`: Visibility flag
- `isSimpleMeasure`: Whether it's a simple aggregation

**Formatting**:
- `formatString`: Static format (e.g., `"#,0"`, `"0.00%"`)
- `formatStringExpression`: Dynamic DAX expression for format
  - Enables context-sensitive formatting
  - Example: Different decimals based on scale selection

**State Fields**:
- `state`: Calculation state
  - `"Ready"`: Valid, no errors
  - `"SemanticError"`: DAX has semantic issues
  - `"SyntaxError"`: Invalid DAX syntax
- `errorMessage`: Error details (if state != Ready)

**Lineage Fields** (Advanced):
- `lineageTag`: GUID for change tracking
- `sourceLineageTag`: Original source reference

**Timestamp Fields**:
- `modifiedTime`: Last DAX expression change
- `structureModifiedTime`: Last metadata change (name, folder, etc.)

**Annotations & Properties**:
- `annotations`: Key-value pairs (e.g., `{"key": "PBI_FormatHint", "value": "..."}`)
- `extendedProperties`: Custom metadata

**Implementation Notes**:
1. Expression includes comments and formatting
2. Format string can be DAX expression (advanced feature)
3. Empty description/formatString is common
4. Variant dataType is most flexible (auto-detection)
5. Measure references shown as `[MeasureName]` in expressions

**DAX Pattern Examples**:

**Optimization Comments**:
```dax
-- OPTIMIZATION NOTES:
-- 1. Replaced FILTER with CALCULATETABLE for better query folding
-- 2. Early exit for blank denominator (skip unnecessary work)
```

**Variable Pattern**:
```dax
VAR DenominatorLine = SELECTEDVALUE('s_ReportLines'[Denominator])
VAR ReportSign = SELECTEDVALUE('s_ReportLines'[Sign])
```

**Conditional Logic**:
```dax
VAR SignMultiplier = IF(ReportSign <> "Keep", -1, 1)
```

**Table Filtering**:
```dax
VAR NumeratorComponents = 
    CALCULATETABLE(
        's_Formulas Combined',
        's_Formulas Combined'[Formula Header] = SelectedFormulaElement
    )
```

**Iteration**:
```dax
VAR NumeratorValue = 
    SignMultiplier * SUMX(
        NumeratorComponents,
        [PL-AMT-BASE Scenario Amount - Currency]
    )
```

**Safe Division**:
```dax
DIVIDE(NumeratorValue, DenominatorValue, 0)
```

**Dynamic Format String**:
```dax
VAR vLineformat = SELECTEDVALUE(s_ReportLines[Number Format])
VAR vScale = SELECTEDVALUE(s_Scale2[Nr])
VAR vResult = CALCULATE(
    SELECTEDVALUE(s_Format2[Format]),
    s_Format2[Line Format] = vLineformat,
    s_Format2[Scale] = vScale
)
RETURN vResult
```

**Use Cases**:
- DAX learning and analysis
- Measure documentation
- Performance optimization review
- Dependency analysis (find referenced measures)
- Debugging measure errors
- Format string inspection

---

### 8. Get Complex Measure with Currency Logic

**Purpose**: Example of advanced DAX pattern with USERELATIONSHIP.

**Operation Name**: `measure_operations`

**Request Structure**:
```json
{
  "operation": "Get",
  "tableName": "m_Measures",
  "measureName": "PL-AMT-BASE Scenario Amount - Currency"
}
```

**Response Structure** (abridged for key patterns):
```json
{
  "success": true,
  "data": {
    "name": "PL-AMT-BASE Scenario Amount - Currency",
    "expression": "\n-- OPTIMIZATION NOTES:\n-- 1. Moved IF(IsDocumentCurrency) outside SUMX - evaluated once instead of per row\n-- 2. Replaced table reference FILTER with CALCULATETABLE for query folding\n-- 3. Materialized currency rates table outside iteration\n-- 4. Simplified relationship handling\n\n-- Get configuration values once\nVAR FormulaElement = SELECTEDVALUE('s_Formulas Combined'[Formula Element])\nVAR Multiplicator = SELECTEDVALUE('s_Formulas Combined'[Multiplicator])\nVAR SelectedCurrencyType = SELECTEDVALUE('s_Currency_Doc vs Company'[Type], \"Company Code Currency\")\nVAR IsDocumentCurrency = SelectedCurrencyType = \"Document Currency\"\n\n-- Materialize currency rates table with proper relationship\nVAR CurrencyRates =\n    CALCULATETABLE(\n        d_Currency_Rates,\n        USERELATIONSHIP(d_Currency_Rates[Exchange rate type], d_Scenario[Exchange Rate Type])\n    )\n\n-- Branch logic based on currency type (evaluated once, not per row)\nVAR Result = \n    IF(\n        IsDocumentCurrency,\n        -- Document Currency Path\n        SUMX(\n            CurrencyRates,\n            VAR LocalCurr = d_Currency_Rates[From currency]\n            VAR Period = d_Currency_Rates[Valid from]\n            VAR ExchangeRate = d_Currency_Rates[Exchange Rate]\n            VAR BaseAmount =\n                CALCULATE(\n                    SUM('f_FINREP'[Amount (document currency)]),\n                    USERELATIONSHIP('f_FINREP'[Document Currency], d_Currency_From[From currency]),\n                    d_Currency_From[From currency] = LocalCurr,\n                    d_Period[Date EOM] = Period,\n                    d_BS_PL_CF[Line] = FormulaElement\n                )\n            RETURN BaseAmount * ExchangeRate * Multiplicator\n        ),\n        -- Company Code Currency Path\n        SUMX(\n            CurrencyRates,\n            VAR LocalCurr = d_Currency_Rates[From currency]\n            VAR Period = d_Currency_Rates[Valid from]\n            VAR ExchangeRate = d_Currency_Rates[Exchange Rate]\n            VAR BaseAmount =\n                CALCULATE(\n                    SUM('f_FINREP'[Amount (company code currency)]),\n                    d_Currency_From[From currency] = LocalCurr,\n                    d_Period[Date EOM] = Period,\n                    d_BS_PL_CF[Line] = FormulaElement\n                )\n            RETURN BaseAmount * ExchangeRate * Multiplicator\n        )\n    )\n\nRETURN Result",
    "isHidden": true,
    "displayFolder": "Financial Model\\1.1 Base measures P&L\\Scenario Comparable\\Currency Calculation",
    "dataType": "Variant"
  }
}
```

**Advanced DAX Patterns Demonstrated**:

**1. USERELATIONSHIP Pattern**:
```dax
-- Activate inactive relationship temporarily
CALCULATETABLE(
    d_Currency_Rates,
    USERELATIONSHIP(d_Currency_Rates[Exchange rate type], d_Scenario[Exchange Rate Type])
)
```

**2. Table Materialization**:
```dax
-- Evaluate table once, outside iteration
VAR CurrencyRates =
    CALCULATETABLE(
        d_Currency_Rates,
        USERELATIONSHIP(...)
    )
```

**3. Conditional Branching**:
```dax
-- Evaluate condition once
VAR IsDocumentCurrency = SelectedCurrencyType = "Document Currency"
VAR Result = IF(
    IsDocumentCurrency,
    -- Branch 1: Document currency logic
    SUMX(...),
    -- Branch 2: Company currency logic
    SUMX(...)
)
```

**4. Role-Playing Dimension**:
```dax
-- Switch between two relationships to same dimension
-- Active relationship:
CALCULATE(SUM('f_FINREP'[Amount (company code currency)]))

-- Inactive relationship (requires USERELATIONSHIP):
CALCULATE(
    SUM('f_FINREP'[Amount (document currency)]),
    USERELATIONSHIP('f_FINREP'[Document Currency], d_Currency_From[From currency])
)
```

**5. Multi-Currency Conversion**:
```dax
SUMX(
    CurrencyRates,  -- Iterate over each currency rate
    VAR LocalCurr = d_Currency_Rates[From currency]
    VAR ExchangeRate = d_Currency_Rates[Exchange Rate]
    VAR BaseAmount = CALCULATE(
        SUM('f_FINREP'[Amount]),
        d_Currency_From[From currency] = LocalCurr  -- Filter to specific currency
    )
    RETURN BaseAmount * ExchangeRate * Multiplicator
)
```

**Performance Optimization Techniques**:
1. **Move condition outside iteration**: `IF()` before `SUMX()` instead of inside
2. **Materialize tables**: Evaluate `CALCULATETABLE()` once in VAR
3. **Use CALCULATETABLE over FILTER**: Better for query folding
4. **Default values**: `SELECTEDVALUE(..., "Default")` avoids BLANK checks

**Use Cases**:
- Multi-currency financial reporting
- Role-playing dimension handling
- Complex iterative calculations
- Performance-optimized DAX patterns

---

## Calculation Group Operations

### 9. List Calculation Groups

**Purpose**: Get all calculation groups with their items.

**Operation Name**: `calculation_group_operations`

**Request Structure**:
```json
{
  "operation": "ListGroups"
}
```

**Parameters**:
- `connectionName` (string, optional): Connection identifier

**Response Structure**:
```json
{
  "success": true,
  "message": "Found 5 calculation groups",
  "operation": "ListGroups",
  "data": [
    {
      "calculationItems": [
        {"ordinal": 0, "name": "MTD"},
        {"ordinal": 1, "name": "QTD"},
        {"ordinal": 2, "name": "YTD"},
        {"ordinal": 3, "name": "YTG"},
        {"ordinal": 4, "name": "FY"},
        {"ordinal": 5, "name": "Q1"},
        {"ordinal": 6, "name": "Q2"},
        {"ordinal": 7, "name": "Q3"},
        {"ordinal": 8, "name": "Q4"}
      ],
      "name": "c_Time Intelligence P&L"
    },
    {
      "calculationItems": [
        {"ordinal": 0, "name": "L3M"},
        {"ordinal": 1, "name": "L12M"},
        {"ordinal": 2, "name": "L2Y Full Year"},
        {"ordinal": 3, "name": "L2Y YTD"},
        {"ordinal": 4, "name": "L3Y Full Year"},
        {"ordinal": 5, "name": "L3Y YTD"},
        {"ordinal": 6, "name": "HTD"}
      ],
      "name": "c_Time Intelligence_LxM & Other"
    },
    {
      "calculationItems": [
        {"ordinal": 0, "name": "Base"},
        {"ordinal": 1, "name": "Cumulative"}
      ],
      "name": "c_Monthly_vs_Cumulative"
    },
    {
      "calculationItems": [
        {"ordinal": 0, "name": "Filter"}
      ],
      "name": "c_AccessPageFilter"
    },
    {
      "calculationItems": [
        {"ordinal": 0, "name": "Current Month"},
        {"ordinal": 1, "name": "Prior Month"},
        {"ordinal": 2, "name": "Prior Year"},
        {"ordinal": 3, "name": "End of Prior Year"}
      ],
      "name": "c_Time Intelligence BS"
    }
  ]
}
```

**Response Fields Explained**:

**Calculation Group Fields**:
- `name`: Calculation group name (typically prefixed with `c_`)
- `calculationItems`: Array of calculation items in this group

**Calculation Item Fields**:
- `ordinal`: Display order (0-based index)
- `name`: Item name shown in slicers

**Implementation Notes**:
1. Requires compatibility level 1500+ (Power BI 2020+)
2. Calculation groups modify measure behavior dynamically
3. Only shows item names, not DAX expressions (use GetGroup for full details)
4. Ordinal determines sort order in slicers

**Calculation Group Types**:

**1. Time Intelligence Groups**:
```json
{
  "name": "c_Time Intelligence P&L",
  "calculationItems": ["MTD", "QTD", "YTD", "YTG", "FY", "Q1", "Q2", "Q3", "Q4"]
}
```
- Modifies time context for all measures
- MTD = Month-To-Date, YTD = Year-To-Date, YTG = Year-To-Go

**2. Comparison Groups**:
```json
{
  "name": "c_Time Intelligence_LxM & Other",
  "calculationItems": ["L3M", "L12M", "L2Y Full Year", "L2Y YTD", ...]
}
```
- L3M = Last 3 Months, L12M = Last 12 Months
- L2Y = Last 2 Years

**3. Display Mode Groups**:
```json
{
  "name": "c_Monthly_vs_Cumulative",
  "calculationItems": ["Base", "Cumulative"]
}
```
- Switches between period values and running totals

**4. Balance Sheet Time**:
```json
{
  "name": "c_Time Intelligence BS",
  "calculationItems": ["Current Month", "Prior Month", "Prior Year", "End of Prior Year"]
}
```
- Point-in-time snapshots for balance sheet

**5. Utility Groups**:
```json
{
  "name": "c_AccessPageFilter",
  "calculationItems": ["Filter"]
}
```
- Single-item groups for specific behaviors

**Use Cases**:
- Time intelligence inventory
- Understanding dynamic measure behavior
- Documentation of calculation layers
- Slicer configuration reference

**Typical DAX Patterns** (not returned by List, shown for reference):

**MTD (Month-To-Date)**:
```dax
CALCULATE(
    SELECTEDMEASURE(),
    DATESMTD('d_Date'[Date])
)
```

**YTD (Year-To-Date)**:
```dax
CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD('d_Date'[Date])
)
```

**Prior Year**:
```dax
CALCULATE(
    SELECTEDMEASURE(),
    SAMEPERIODLASTYEAR('d_Date'[Date])
)
```

**Cumulative**:
```dax
CALCULATE(
    SELECTEDMEASURE(),
    DATESYTD('d_Date'[Date], "FY")
)
```

---

## Implementation Patterns

### Error Handling Pattern

**Standard Error Response**:
```json
{
  "success": false,
  "message": "Operation failed: [Error details]",
  "operation": "OperationName",
  "error": {
    "code": "ErrorCode",
    "details": "Additional context"
  }
}
```

**Common Error Codes**:
- `"ConnectionNotFound"`: No active connection
- `"ObjectNotFound"`: Table/measure doesn't exist
- `"InvalidOperation"`: Operation not supported
- `"InvalidParameter"`: Parameter validation failed

### Pagination Pattern

**Request with Limit**:
```json
{
  "operation": "List",
  "maxResults": 50
}
```

**Response with Warning**:
```json
{
  "data": [...],
  "warnings": [
    "Results truncated: Showing 50 of 224 items"
  ]
}
```

### Connection Management Pattern

**Multi-Model Workflow**:
```javascript
// 1. Discover all instances
const instances = await listLocalInstances();

// 2. Connect to each
for (const instance of instances) {
    await connect(instance.port);
}

// 3. Track connection names
const connections = instances.map(i => i.connectionName);

// 4. Use specific connection
await getStats(connections[0]);
```

---

## Performance Considerations

### Fast Operations (< 100ms)
- `ListLocalInstances`
- `GetStats`
- `List` operations (tables, measures, relationships)

### Medium Operations (100ms - 1s)
- `Get` operations (single measure/table details)
- `ListGroups` (calculation groups)

### Slow Operations (> 1s)
- DAX query execution
- Large data exports
- Complex relationship analysis

### Optimization Tips

**1. Batch Get Operations**:
```javascript
// Bad: Multiple round-trips
for (const measure of measures) {
    await getMeasure(measure.name);
}

// Good: Get list first, then selective Gets
const measureList = await listMeasures();
const keyMeasures = measureList.filter(m => m.name.startsWith("PL-AMT-"));
for (const measure of keyMeasures) {
    await getMeasure(measure.name);
}
```

**2. Use maxResults for Large Models**:
```json
{
  "operation": "List",
  "maxResults": 100  // Prevent overwhelming responses
}
```

**3. Cache Static Metadata**:
- Table list rarely changes - cache it
- Relationship structure is static - cache it
- Re-fetch only on model refresh

---

## Common Workflows

### 1. Model Documentation Workflow

```javascript
// Step 1: Discover and connect
const instances = await listLocalInstances();
await connect(instances[0].port);

// Step 2: Get overview
const stats = await getStats();

// Step 3: Get tables
const tables = await listTables();

// Step 4: Get relationships
const relationships = await listRelationships();

// Step 5: Get measures (paginated)
const measures = await listMeasures(null, 100);

// Step 6: Get calculation groups
const calcGroups = await listCalculationGroups();

// Generate documentation from collected data
```

### 2. Measure Analysis Workflow

```javascript
// Step 1: Find measure table
const tables = await listTables();
const measureTable = tables.find(t => t.measureCount > 0);

// Step 2: List measures
const measures = await listMeasures(measureTable.name);

// Step 3: Get details for key measures
for (const measure of measures.filter(m => m.name.startsWith("PL-AMT-"))) {
    const details = await getMeasure(measureTable.name, measure.name);
    // Analyze DAX pattern
    analyzeDaxExpression(details.expression);
}
```

### 3. Relationship Quality Check

```javascript
// Get all relationships
const relationships = await listRelationships();

// Identify issues
const manyToMany = relationships.filter(r => 
    r.fromCardinality === "Many" && r.toCardinality === "Many"
);

const bidirectional = relationships.filter(r => 
    r.crossFilteringBehavior === "BothDirections"
);

const inactive = relationships.filter(r => !r.isActive);

// Report findings
console.log(`Many-to-Many: ${manyToMany.length}`);
console.log(`Bidirectional: ${bidirectional.length}`);
console.log(`Inactive: ${inactive.length}`);
```

---

## API Response Standards

### Success Response Template
```json
{
  "success": true,
  "message": "Human-readable success message",
  "operation": "OPERATION_NAME",
  "data": { /* operation-specific data */ }
}
```

### Error Response Template
```json
{
  "success": false,
  "message": "Human-readable error message",
  "operation": "OPERATION_NAME",
  "error": {
    "code": "ERROR_CODE",
    "details": "Additional context"
  }
}
```

### Warning Pattern
```json
{
  "success": true,
  "data": [...],
  "warnings": [
    "Warning message 1",
    "Warning message 2"
  ]
}
```

---

## Data Type Reference

### Measure Data Types
- `"Variant"`: Auto-detected (most common)
- `"Integer"`: Whole numbers
- `"Double"`: Decimals
- `"Currency"`: Monetary values (4 decimal precision)
- `"String"`: Text
- `"Boolean"`: True/False
- `"DateTime"`: Date and time
- `"Decimal"`: High-precision decimal

### Relationship Cardinality
- `"One"`: Unique values, primary key
- `"Many"`: Non-unique values, foreign key

### Filter Direction
- `"OneDirection"`: Single-direction filter (standard)
- `"BothDirections"`: Bidirectional filter (use carefully)

### Calculation Group Ordinal
- 0-based integer
- Determines sort order in slicers
- Can be non-contiguous

---

## Naming Convention Insights

Based on the analyzed model, common prefixes:

**Table Prefixes**:
- `d_`: Dimension tables (master data)
- `f_`: Fact tables (transactional data)
- `m_`: Measure tables (calculation containers)
- `s_`: Support/slicer tables (filtering)
- `c_`: Calculation groups
- `sfp_`: Slicer field parameters
- `dfp_`: Dynamic field parameters
- `r_`: Row-level security tables
- `dyn_`: Dynamic tables

**Measure Prefixes**:
- `PL-AMT-`: Profit & Loss amount measures
- `PL-COL-`: P&L column formatting
- `BAL-AMT-`: Balance sheet amounts
- `TC0/TC1/TC2/TC3`: Time calculation variants

**Display Folder Patterns**:
- `"Financial Model\\1.1 Base measures P&L\\..."`
- Numbers for ordering: `"1.1"`, `"1.2"`, `"9.9"`
- Hierarchical structure with backslashes

---

## Compatibility Levels

### Compatibility Level Feature Matrix

| Level | Version | Key Features |
|-------|---------|--------------|
| 1200 | SQL Server 2016, Power BI | Basic tabular model |
| 1400 | SQL Server 2017, Power BI | Object-level security, M expressions |
| 1500 | SQL Server 2019, Power BI | **Calculation groups** |
| 1600 | Power BI 2021+ | Enhanced calculation groups |
| 1601 | Power BI Current | Latest features |

**Check Compatibility**:
```json
{
  "CompatibilityLevel": 1601
}
```

---

## Advanced Topics

### USERELATIONSHIP Pattern

**When to Use**:
- Role-playing dimensions (e.g., Ship Date vs Order Date)
- Multiple currency columns (Document vs Company)
- Alternative hierarchies

**DAX Pattern**:
```dax
CALCULATE(
    SUM(FactTable[Amount]),
    USERELATIONSHIP(FactTable[InactiveKey], DimTable[Key])
)
```

**TMSL Representation**:
```json
{
  "isActive": false,
  "fromColumn": "Document Currency",
  "toColumn": "From currency"
}
```

### Calculation Group Precedence

**Multiple Calculation Groups**:
When multiple calculation groups are applied, precedence determines evaluation order.

**Query Pattern** (not shown in responses, for implementation):
```sql
SELECT 
    [CalculationGroupAttribute].[Precedence]
FROM 
    $SYSTEM.TMSCHEMA_CALCULATION_GROUPS
```

---

## Testing & Validation

### Connection Test
```javascript
async function testConnection() {
    try {
        const instances = await listLocalInstances();
        if (instances.length === 0) {
            throw new Error("No Power BI instances running");
        }
        
        await connect(instances[0].port);
        const stats = await getStats();
        
        console.log(`✓ Connected to: ${stats.ModelName}`);
        console.log(`✓ Tables: ${stats.TableCount}`);
        console.log(`✓ Measures: ${stats.TotalMeasureCount}`);
        
        return true;
    } catch (error) {
        console.error(`✗ Connection failed: ${error.message}`);
        return false;
    }
}
```

### Measure Validation
```javascript
async function validateMeasures() {
    const measures = await listMeasures();
    
    for (const measure of measures) {
        const details = await getMeasure(measure.tableName, measure.name);
        
        if (details.state !== "Ready") {
            console.warn(`⚠ ${measure.name}: ${details.errorMessage}`);
        }
    }
}
```

---

## Appendix: Complete Operation Reference

| Operation | Tool | Purpose | Speed |
|-----------|------|---------|-------|
| ListLocalInstances | connection_operations | Find running instances | Fast |
| Connect | connection_operations | Establish connection | Fast |
| GetStats | model_operations | Model overview | Fast |
| List (tables) | table_operations | All tables | Fast |
| Get (table) | table_operations | Table details | Medium |
| List (measures) | measure_operations | All measures | Fast |
| Get (measure) | measure_operations | Measure details | Medium |
| List (relationships) | relationship_operations | All relationships | Fast |
| ListGroups | calculation_group_operations | All calc groups | Fast |

---

## Best Practices Summary

1. **Always check connection** before operations
2. **Use maxResults** for large models to prevent timeouts
3. **Cache static metadata** (tables, relationships)
4. **Handle errors gracefully** with try-catch
5. **Parse DAX carefully** - may contain special characters
6. **Check state field** before using measure
7. **Respect data types** - Variant is safest
8. **Document patterns** found in expressions
9. **Monitor timestamps** for change detection
10. **Test with small models** first

---

## References

- **XMLA Endpoint**: Analysis Services protocol over TCP
- **DMVs**: Dynamic Management Views for metadata
- **TMSL**: Tabular Model Scripting Language (JSON)
- **TMDL**: Tabular Model Definition Language (text files)
- **DAX**: Data Analysis Expressions
- **TOM**: Tabular Object Model

---

*Document Version: 1.0*  
*Based on Analysis: Financial Reporting Model (109 tables, 239 measures)*  
*MCP Server: Microsoft Official Power BI MCP*  
*Date: 2025-11-19*
