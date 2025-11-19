# Microsoft Official Power BI MCP Server - Complete Technical Documentation

**Version**: 1.0  
**Last Updated**: November 2025  
**Server Name**: Microsoft-Official-PBI-MCP  
**Repository**: microsoft/powerbi-modeling-mcp

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Connection & Database Management](#connection--database-management)
3. [Model Operations](#model-operations)
4. [Table Operations](#table-operations)
5. [Column Operations](#column-operations)
6. [Measure Operations](#measure-operations)
7. [Relationship Operations](#relationship-operations)
8. [DAX Query Operations](#dax-query-operations)
9. [Function Operations](#function-operations)
10. [Calculation Groups](#calculation-groups)
11. [Hierarchies & Calendars](#hierarchies--calendars)
12. [Partitions](#partitions)
13. [Perspectives](#perspectives)
14. [Security Roles](#security-roles)
15. [Cultures & Translations](#cultures--translations)
16. [Query Groups & Named Expressions](#query-groups--named-expressions)
17. [Trace Operations](#trace-operations)
18. [Transaction Management](#transaction-management)
19. [Batch Operations](#batch-operations)
20. [Export Capabilities](#export-capabilities)
21. [Performance Best Practices](#performance-best-practices)

---

## Architecture Overview

### Core Technologies
- **Protocol**: ADOMD.NET + Analysis Services Management Objects (AMO)
- **Connection Types**: 
  - Power BI Desktop (XMLA - local TCP ports 50000-60000)
  - Microsoft Fabric Workspace (XMLA endpoint via Azure AD)
  - PBIP/TMDL folders (offline metadata)
- **Authentication**: Azure Identity SDK with interactive browser auth
- **Transaction Support**: Full ACID transactions (begin/commit/rollback)
- **Operating Modes**: ReadWrite (with confirmation), ReadOnly, SkipConfirmation

### Key Features
- Direct TOM (Tabular Object Model) manipulation
- Real-time metadata changes
- Full TMDL/TMSL export capabilities
- Query tracing with VertiPaq SE analysis
- Batch operations with transaction control
- Comprehensive metadata management

---

## 1. Connection & Database Management

### connection_operations

**Purpose**: Manage connections to Power BI models and Analysis Services

#### Operations

**Connect** - Direct connection to Power BI Desktop or XMLA endpoint
```json
{
  "operation": "Connect",
  "dataSource": "localhost:54321",
  "initialCatalog": "MyDataset",
  "clearCredential": false
}
```
- Searches local TCP ports for AS instances
- Uses ADOMD connection strings
- Auto-generates connection name if not provided

**ConnectFabric** - Connect to Fabric semantic model
```json
{
  "operation": "ConnectFabric",
  "workspaceName": "Sales Workspace",
  "semanticModelName": "Sales Model",
  "tenantName": "myorg",
  "clearCredential": false
}
```
- Uses OAuth2 bearer token
- Constructs XMLA endpoint: `powerbi://api.powerbi.com/v1.0/myorg/{workspace}`
- Interactive browser authentication
- Requires Fabric Administrator permissions

**ConnectFolder** - Load PBIP/TMDL folder
```json
{
  "operation": "ConnectFolder",
  "folderPath": "C:\\Projects\\MyModel",
  "connectionName": "MyModel_Offline"
}
```
- Loads TMDL metadata from `database.tmdl`
- Creates offline TOM in-memory representation
- Searches in root or `definition` subfolder

**ListLocalInstances** - Discover running Power BI Desktop instances
```json
{
  "operation": "ListLocalInstances"
}
```
- Returns: Instance name, port, database name

**Technical Details**:
- Connection pool management
- Credential caching with `clearCredential` flag
- Last-used connection tracking
- Rename connections for better organization

---

### database_operations

**Purpose**: Manage semantic model databases

#### Operations

**List** - List all databases on server
```json
{
  "operation": "List"
}
```

**Update** - Update database metadata
```json
{
  "operation": "Update",
  "databaseName": "SalesModel",
  "updateDefinition": {
    "description": "Updated description",
    "compatibilityLevel": 1604
  }
}
```

**Create** - Create new offline database
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "NewModel",
    "compatibilityLevel": 1605,
    "isOffline": true
  },
  "connectionName": "NewModel_Conn"
}
```

**ImportFromTmdlFolder** - Import TMDL to new database
```json
{
  "operation": "ImportFromTmdlFolder",
  "tmdlFolderPath": "C:\\TMDL\\MyModel"
}
```

**ExportToTmdlFolder** - Export to TMDL folder structure
```json
{
  "operation": "ExportToTmdlFolder",
  "tmdlFolderPath": "C:\\Export\\MyModel"
}
```

**DeployToFabric** - Deploy model to Fabric workspace
```json
{
  "operation": "DeployToFabric",
  "deployToFabricRequest": {
    "targetWorkspaceName": "Production",
    "newDatabaseName": "Sales_PROD",
    "includeRestricted": false
  }
}
```
- Uses XMLA Create/CreateOrReplace TMSL commands
- Generates TMSL script from current model
- Connects to target workspace XMLA endpoint

**ExportTMDL** - Export database metadata as TMDL
```json
{
  "operation": "ExportTMDL",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1,
    "filePath": "C:\\Export\\database.tmdl",
    "serializationOptions": {
      "includeChildren": true,
      "includeRestrictedInformation": false
    }
  }
}
```

**ExportTMSL** - Export as TMSL JSON script
```json
{
  "operation": "ExportTMSL",
  "tmslExportOptions": {
    "tmslOperationType": "CreateOrReplace",
    "formatJson": true,
    "maxReturnCharacters": -1
  }
}
```

---

## 2. Model Operations

### model_operations

**Purpose**: Manage semantic model properties and metadata

#### Operations

**Get** - Retrieve model metadata
```json
{
  "operation": "Get",
  "modelName": "Model"
}
```
Returns: culture, collation, defaultMode, data access options

**GetStats** - Get model statistics
```json
{
  "operation": "GetStats"
}
```
Returns: table count, measure count, column count, relationships

**Refresh** - Refresh model data
```json
{
  "operation": "Refresh",
  "refreshType": "Full"
}
```
Refresh types: Full, Calculate, ClearValues, DataOnly, Defragment, Automatic

**Update** - Update model properties
```json
{
  "operation": "Update",
  "updateDefinition": {
    "description": "Sales and inventory model",
    "culture": "en-US",
    "discourageImplicitMeasures": true,
    "defaultPowerBIDataSourceVersion": "PowerBI_V3"
  }
}
```

**Rename** - Rename the model
```json
{
  "operation": "Rename",
  "newName": "SalesModel_v2"
}
```

**ExportTMDL** - Export model as TMDL
```json
{
  "operation": "ExportTMDL",
  "tmdlExportOptions": {
    "filePath": "C:\\model.tmdl",
    "maxReturnCharacters": -1,
    "serializationOptions": {
      "includeChildren": false,
      "includeInferredDataTypes": false
    }
  }
}
```

**Technical Details**:
- Model is the root container for all metadata
- compatibilityLevel determines available features
- defaultMode: Import, DirectQuery, DualComposite
- Model annotations store metadata like refresh schedule

---

## 3. Table Operations

### table_operations

**Purpose**: Manage tables in semantic model

#### Operations

**List** - List all tables
```json
{
  "operation": "List"
}
```

**Get** - Get table definition
```json
{
  "operation": "Get",
  "tableName": "FactSales"
}
```

**Create** - Create new table
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "DimProduct",
    "partitionName": "Part1",
    "mode": "Import",
    "dataSourceName": "SQLSource",
    "schemaName": "dbo",
    "sqlQuery": "SELECT * FROM Products",
    "columns": [
      {
        "name": "ProductKey",
        "dataType": "Int64",
        "sourceColumn": "ProductKey",
        "isKey": true
      },
      {
        "name": "ProductName",
        "dataType": "String",
        "sourceColumn": "ProductName"
      }
    ]
  }
}
```

**Update** - Update table properties
```json
{
  "operation": "Update",
  "tableName": "FactSales",
  "updateDefinition": {
    "description": "Sales fact table",
    "isHidden": false,
    "dataCategory": "Uncategorized"
  }
}
```

**Delete** - Delete table
```json
{
  "operation": "Delete",
  "tableName": "OldTable",
  "shouldCascadeDelete": true
}
```
- Cascade delete removes dependent objects (relationships, hierarchies)

**Refresh** - Refresh table data
```json
{
  "operation": "Refresh",
  "tableName": "FactSales",
  "refreshType": "Full"
}
```

**Rename** - Rename table
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "currentName": "Fact_Sales",
    "newName": "FactSales"
  }
}
```

**GetSchema** - Get table column schema
```json
{
  "operation": "GetSchema",
  "tableName": "FactSales"
}
```
Returns: column names, data types, source columns

**ExportTMDL/ExportTMSL** - Export table definition
```json
{
  "operation": "ExportTMDL",
  "tableName": "FactSales",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1,
    "serializationOptions": {
      "includeChildren": true
    }
  }
}
```

---

## 4. Column Operations

### column_operations

**Purpose**: Manage table columns

#### Operations

**List** - List columns in table
```json
{
  "operation": "List",
  "tableName": "FactSales",
  "maxResults": 200
}
```

**Get** - Get column definition
```json
{
  "operation": "Get",
  "tableName": "FactSales",
  "columnName": "SalesAmount"
}
```

**Create** - Create new column
```json
{
  "operation": "Create",
  "tableName": "FactSales",
  "createDefinition": {
    "name": "TotalCost",
    "dataType": "Decimal",
    "expression": "[UnitCost] * [Quantity]",
    "formatString": "$#,0.00",
    "description": "Calculated total cost",
    "displayFolder": "Calculations"
  }
}
```

Column types:
- **Data columns**: sourceColumn from partition query
- **Calculated columns**: DAX expression
- **AlternateOf columns**: for composite models

**Update** - Update column properties
```json
{
  "operation": "Update",
  "tableName": "FactSales",
  "columnName": "SalesAmount",
  "updateDefinition": {
    "formatString": "$#,0.00",
    "summarizeBy": "Sum",
    "isHidden": false,
    "displayFolder": "Measures\\Revenue",
    "sortByColumn": "SalesDate"
  }
}
```

**Delete** - Delete column
```json
{
  "operation": "Delete",
  "tableName": "FactSales",
  "columnName": "OldColumn",
  "shouldCascadeDelete": true
}
```

**Rename** - Rename column
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "tableName": "FactSales",
    "currentName": "Amount",
    "newName": "SalesAmount"
  }
}
```

**Technical Details**:
- dataType: Int64, String, Double, Decimal, DateTime, Boolean
- summarizeBy: Sum, Average, Min, Max, Count, None
- sortByColumn: specify sort order column (e.g., MonthName sorted by MonthNumber)
- displayFolder: organize columns in hierarchical folders
- lineageTag: tracks column lineage through transformations

---

## 5. Measure Operations

### measure_operations

**Purpose**: Manage DAX measures

#### Operations

**List** - List measures (optionally filter by table)
```json
{
  "operation": "List",
  "tableName": "FactSales",
  "maxResults": 200
}
```

**Get** - Get measure definition
```json
{
  "operation": "Get",
  "measureName": "Total Sales"
}
```

**Create** - Create new measure
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "Total Sales",
    "tableName": "FactSales",
    "expression": "SUM(FactSales[SalesAmount])",
    "formatString": "$#,0.00",
    "description": "Total sales amount",
    "displayFolder": "Revenue\\Core Metrics"
  }
}
```

Advanced measure example:
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "YoY Growth %",
    "tableName": "_Measures",
    "expression": "DIVIDE([Sales CY] - [Sales PY], [Sales PY])",
    "formatString": "0.00%",
    "description": "Year-over-year growth percentage",
    "displayFolder": "Time Intelligence",
    "detailRowsExpression": "TOPN(100, VALUES(FactSales[OrderID]))"
  }
}
```

**Update** - Update measure properties
```json
{
  "operation": "Update",
  "measureName": "Total Sales",
  "updateDefinition": {
    "expression": "SUMX(FactSales, [SalesAmount] * [ExchangeRate])",
    "formatString": "€#,0.00",
    "isHidden": false
  }
}
```

**Delete** - Delete measure
```json
{
  "operation": "Delete",
  "measureName": "Old Measure",
  "shouldCascadeDelete": true
}
```

**Rename** - Rename measure
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "currentName": "Sales Total",
    "newName": "Total Sales",
    "tableName": "FactSales"
  }
}
```

**Move** - Move measure to different table
```json
{
  "operation": "Move",
  "moveDefinition": {
    "name": "Total Sales",
    "currentTableName": "FactSales",
    "destinationTableName": "_Measures"
  }
}
```

**ExportTMDL** - Export measure as TMDL
```json
{
  "operation": "ExportTMDL",
  "measureName": "Total Sales",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- Measures are model-level calculations (not row context)
- formatStringExpression: dynamic format strings based on conditions
- detailRowsExpression: defines drill-through behavior
- isSimpleMeasure: indicates if measure is simple aggregation
- KPI property: associates measure with KPI metadata

---

## 6. Relationship Operations

### relationship_operations

**Purpose**: Manage table relationships

#### Operations

**List** - List all relationships
```json
{
  "operation": "List"
}
```

**Get** - Get relationship definition
```json
{
  "operation": "Get",
  "relationshipName": "FactSales_DimDate"
}
```

**Create** - Create new relationship
```json
{
  "operation": "Create",
  "relationshipDefinition": {
    "name": "FactSales_DimProduct",
    "fromTable": "FactSales",
    "fromColumn": "ProductKey",
    "toTable": "DimProduct",
    "toColumn": "ProductKey",
    "fromCardinality": "Many",
    "toCardinality": "One",
    "crossFilteringBehavior": "OneDirection",
    "isActive": true,
    "securityFilteringBehavior": "OneDirection"
  }
}
```

Relationship properties:
- **fromCardinality/toCardinality**: None, One, Many
- **crossFilteringBehavior**: OneDirection, BothDirections, Automatic
- **securityFilteringBehavior**: OneDirection, BothDirections, None
- **isActive**: only one active relationship per column pair
- **joinOnDateBehavior**: DatePart, DateAndTime

**Update** - Update relationship properties
```json
{
  "operation": "Update",
  "relationshipName": "FactSales_DimDate",
  "relationshipUpdate": {
    "crossFilteringBehavior": "BothDirections",
    "isActive": true
  }
}
```

**Delete** - Delete relationship
```json
{
  "operation": "Delete",
  "relationshipName": "OldRelationship"
}
```

**Rename** - Rename relationship
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "currentName": "Relationship1",
    "newName": "FactSales_DimDate"
  }
}
```

**Activate/Deactivate** - Toggle relationship active state
```json
{
  "operation": "Activate",
  "relationshipName": "FactSales_DimDate_Alternate"
}
```

**Find** - Find relationships for table
```json
{
  "operation": "Find",
  "tableName": "FactSales"
}
```
Returns: all relationships where table is involved

**ExportTMDL** - Export relationship as TMDL
```json
{
  "operation": "ExportTMDL",
  "relationshipName": "FactSales_DimProduct",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- Relationships enable filter propagation between tables
- Bidirectional filtering can cause ambiguity - use carefully
- Inactive relationships accessible via USERELATIONSHIP()
- securityFilteringBehavior controls RLS filter direction

---

## 7. DAX Query Operations

### dax_query_operations

**Purpose**: Execute and validate DAX queries

#### Operations

**Execute** - Run DAX query
```json
{
  "operation": "Execute",
  "query": "EVALUATE TOPN(10, DimProduct, [Total Sales], DESC)",
  "maxRows": 1000,
  "getExecutionMetrics": true,
  "executionMetricsOnly": false,
  "timeoutSeconds": 200
}
```

Returns:
- Query results as table
- Row count
- Execution metrics (if enabled)

**Validate** - Validate DAX query syntax
```json
{
  "operation": "Validate",
  "query": "EVALUATE VALUES(DimProduct[ProductName])",
  "timeoutSeconds": 10
}
```
Returns: validation status, error messages

**ClearCache** - Clear formula engine cache
```json
{
  "operation": "ClearCache"
}
```
Forces fresh calculation on next query

**Execution Metrics**:
When `getExecutionMetrics: true`:
- Total duration
- SE (Storage Engine) query count
- FE (Formula Engine) time
- VertiPaq scan statistics
- Cache hit ratio

**Query Examples**:

Basic table evaluation:
```dax
EVALUATE
TOPN(100, FactSales)
```

Calculated table:
```dax
EVALUATE
ADDCOLUMNS(
    VALUES(DimProduct[ProductName]),
    "Total Sales", [Total Sales],
    "Units Sold", [Total Quantity]
)
ORDER BY [Total Sales] DESC
```

Time intelligence:
```dax
EVALUATE
SUMMARIZECOLUMNS(
    DimDate[Year],
    "Sales CY", [Total Sales],
    "Sales PY", CALCULATE([Total Sales], SAMEPERIODLASTYEAR(DimDate[Date]))
)
```

**Technical Details**:
- Uses ADOMD.NET AdomdCommand
- executionMetricsOnly: returns metrics without row data (faster)
- Timeout default: 200s for execute, 10s for validate
- Results returned as JSON table format

---

## 8. Function Operations

### function_operations

**Purpose**: Manage user-defined DAX functions

#### Operations

**List** - List all functions
```json
{
  "operation": "List"
}
```

**Get** - Get function definition
```json
{
  "operation": "Get",
  "functionName": "GetExchangeRate"
}
```

**Create** - Create new function
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "ConvertCurrency",
    "expression": "ConvertCurrency(Amount, FromCurrency, ToCurrency) = Amount * LOOKUPVALUE(ExchangeRates[Rate], ExchangeRates[From], FromCurrency, ExchangeRates[To], ToCurrency)",
    "description": "Converts amount from one currency to another"
  }
}
```

Function syntax:
```
FunctionName(Param1 [, Param2, ...]) = Expression
```

**Update** - Update function
```json
{
  "operation": "Update",
  "functionName": "ConvertCurrency",
  "updateDefinition": {
    "expression": "ConvertCurrency(Amount, FromCurrency, ToCurrency, RateDate) = Amount * CALCULATE(VALUES(ExchangeRates[Rate]), ExchangeRates[From] = FromCurrency, ExchangeRates[To] = ToCurrency, ExchangeRates[Date] = RateDate)",
    "description": "Converts with date-specific rate"
  }
}
```

**Delete** - Delete function
```json
{
  "operation": "Delete",
  "functionName": "OldFunction"
}
```

**Rename** - Rename function
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "currentName": "CurrConv",
    "newName": "ConvertCurrency"
  }
}
```

**ExportTMDL** - Export function as TMDL
```json
{
  "operation": "ExportTMDL",
  "functionName": "ConvertCurrency",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Use Cases**:
- Complex reusable calculations
- Currency conversion logic
- Business rule encapsulation
- Time intelligence patterns

**Technical Details**:
- Functions are model-level reusable expressions
- Can be called from any measure or calculated column
- Support multiple parameters with type inference
- state property indicates: Ready, SemanticError, SyntaxError

---

## 9. Calculation Groups

### calculation_group_operations

**Purpose**: Manage calculation groups and calculation items

#### Operations

##### Calculation Group Operations

**ListGroups** - List all calculation groups
```json
{
  "operation": "ListGroups"
}
```

**GetGroup** - Get calculation group definition
```json
{
  "operation": "GetGroup",
  "calculationGroupName": "Time Intelligence"
}
```

**CreateGroup** - Create new calculation group
```json
{
  "operation": "CreateGroup",
  "createGroupDefinition": {
    "name": "Time Intelligence",
    "description": "Standard time calculations",
    "precedence": 10,
    "calculationItems": [
      {
        "name": "Current",
        "expression": "SELECTEDMEASURE()"
      },
      {
        "name": "YTD",
        "expression": "CALCULATE(SELECTEDMEASURE(), DATESYTD(DimDate[Date]))",
        "ordinal": 1
      },
      {
        "name": "PY",
        "expression": "CALCULATE(SELECTEDMEASURE(), SAMEPERIODLASTYEAR(DimDate[Date]))",
        "ordinal": 2
      }
    ]
  }
}
```

**UpdateGroup** - Update calculation group properties
```json
{
  "operation": "UpdateGroup",
  "calculationGroupName": "Time Intelligence",
  "updateGroupDefinition": {
    "description": "Updated time intelligence calculations",
    "precedence": 5
  }
}
```

**DeleteGroup** - Delete calculation group
```json
{
  "operation": "DeleteGroup",
  "calculationGroupName": "Old Group"
}
```

**RenameGroup** - Rename calculation group
```json
{
  "operation": "RenameGroup",
  "calculationGroupName": "Time Calc",
  "newCalculationGroupName": "Time Intelligence"
}
```

##### Calculation Item Operations

**ListItems** - List items in calculation group
```json
{
  "operation": "ListItems",
  "calculationGroupName": "Time Intelligence"
}
```

**GetItem** - Get calculation item definition
```json
{
  "operation": "GetItem",
  "calculationGroupName": "Time Intelligence",
  "calculationItemName": "YTD"
}
```

**CreateItem** - Create new calculation item
```json
{
  "operation": "CreateItem",
  "calculationGroupName": "Time Intelligence",
  "createItemDefinition": {
    "name": "QTD",
    "expression": "CALCULATE(SELECTEDMEASURE(), DATESQTD(DimDate[Date]))",
    "ordinal": 3
  }
}
```

**UpdateItem** - Update calculation item
```json
{
  "operation": "UpdateItem",
  "calculationGroupName": "Time Intelligence",
  "calculationItemName": "YTD",
  "updateItemDefinition": {
    "expression": "CALCULATE(SELECTEDMEASURE(), DATESYTD(DimDate[Date]), ALL(DimDate))"
  }
}
```

**DeleteItem** - Delete calculation item
```json
{
  "operation": "DeleteItem",
  "calculationGroupName": "Time Intelligence",
  "calculationItemName": "Old Item"
}
```

**RenameItem** - Rename calculation item
```json
{
  "operation": "RenameItem",
  "calculationGroupName": "Time Intelligence",
  "calculationItemName": "PriorYear",
  "newCalculationItemName": "PY"
}
```

**ReorderItems** - Change item sort order
```json
{
  "operation": "ReorderItems",
  "calculationGroupName": "Time Intelligence",
  "itemNamesInOrder": ["Current", "YTD", "QTD", "PY", "YoY"]
}
```

**ExportTMDL** - Export calculation group as TMDL
```json
{
  "operation": "ExportTMDL",
  "calculationGroupName": "Time Intelligence",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Advanced Examples**:

Currency conversion calculation group:
```json
{
  "name": "Currency",
  "calculationItems": [
    {
      "name": "USD",
      "expression": "SELECTEDMEASURE()"
    },
    {
      "name": "EUR",
      "expression": "SELECTEDMEASURE() * 0.85",
      "formatStringExpression": "'€'#,0.00"
    },
    {
      "name": "GBP",
      "expression": "SELECTEDMEASURE() * 0.73",
      "formatStringExpression": "'£'#,0.00"
    }
  ]
}
```

**Technical Details**:
- Calculation groups modify measure behavior dynamically
- precedence: determines application order (lower = earlier)
- SELECTEDMEASURE() references the underlying measure
- formatStringExpression: dynamic formatting per item
- ordinal: controls display order in slicers

---

## 10. Hierarchies & Calendars

### user_hierarchy_operations

**Purpose**: Manage user-defined hierarchies

#### Operations

**List** - List hierarchies in table
```json
{
  "operation": "List",
  "tableName": "DimProduct"
}
```

**Get** - Get hierarchy definition
```json
{
  "operation": "Get",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy"
}
```

**Create** - Create new hierarchy
```json
{
  "operation": "Create",
  "tableName": "DimProduct",
  "createDefinition": {
    "name": "Product Hierarchy",
    "description": "Category > Subcategory > Product",
    "levels": [
      {
        "name": "Category",
        "columnName": "ProductCategory",
        "ordinal": 0
      },
      {
        "name": "Subcategory",
        "columnName": "ProductSubcategory",
        "ordinal": 1
      },
      {
        "name": "Product",
        "columnName": "ProductName",
        "ordinal": 2
      }
    ]
  }
}
```

**Update** - Update hierarchy properties
```json
{
  "operation": "Update",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "updateDefinition": {
    "description": "Product organizational hierarchy",
    "isHidden": false
  }
}
```

**Delete** - Delete hierarchy
```json
{
  "operation": "Delete",
  "tableName": "DimProduct",
  "hierarchyName": "Old Hierarchy",
  "shouldCascadeDelete": true
}
```

**Rename** - Rename hierarchy
```json
{
  "operation": "Rename",
  "tableName": "DimProduct",
  "hierarchyName": "Prod Hier",
  "newName": "Product Hierarchy"
}
```

**GetColumns** - Get columns used in hierarchy
```json
{
  "operation": "GetColumns",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy"
}
```

##### Level Operations

**AddLevel** - Add level to hierarchy
```json
{
  "operation": "AddLevel",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelCreateDefinition": {
    "name": "Brand",
    "columnName": "BrandName",
    "ordinal": 1
  }
}
```

**RemoveLevel** - Remove level from hierarchy
```json
{
  "operation": "RemoveLevel",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelName": "Brand"
}
```

**UpdateLevel** - Update level properties
```json
{
  "operation": "UpdateLevel",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelName": "Category",
  "levelUpdateDefinition": {
    "description": "Product category level"
  }
}
```

**RenameLevel** - Rename level
```json
{
  "operation": "RenameLevel",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelName": "Cat",
  "newLevelName": "Category"
}
```

**ReorderLevels** - Change level order
```json
{
  "operation": "ReorderLevels",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelNamesInOrder": ["Category", "Brand", "Subcategory", "Product"]
}
```

**ExportTMDL** - Export hierarchy as TMDL
```json
{
  "operation": "ExportTMDL",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

---

### calendar_operations

**Purpose**: Manage calendar objects for time intelligence

#### Operations

**List** - List calendars in table
```json
{
  "operation": "List",
  "tableName": "DimDate"
}
```

**Get** - Get calendar definition
```json
{
  "operation": "Get",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar"
}
```

**Create** - Create new calendar
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "Fiscal Calendar",
    "tableName": "DimDate",
    "description": "July-June fiscal year",
    "calendarColumnGroups": [
      {
        "groupType": "TimeUnitAssociation",
        "timeUnitAssociation": {
          "timeUnit": "Years",
          "primaryColumnName": "FiscalYear",
          "associatedColumns": ["FiscalYearName"]
        }
      },
      {
        "groupType": "TimeUnitAssociation",
        "timeUnitAssociation": {
          "timeUnit": "Quarters",
          "primaryColumnName": "FiscalQuarter",
          "associatedColumns": ["FiscalQuarterName"]
        }
      }
    ]
  }
}
```

**Update** - Update calendar properties
```json
{
  "operation": "Update",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "updateDefinition": {
    "description": "Updated fiscal calendar description"
  }
}
```

**Delete** - Delete calendar
```json
{
  "operation": "Delete",
  "tableName": "DimDate",
  "calendarName": "Old Calendar"
}
```

**Rename** - Rename calendar
```json
{
  "operation": "Rename",
  "tableName": "DimDate",
  "renameDefinition": {
    "currentName": "Fiscal",
    "newName": "Fiscal Calendar"
  }
}
```

##### Column Group Operations

**CreateColumnGroup** - Add column group to calendar
```json
{
  "operation": "CreateColumnGroup",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "columnGroupCreateDefinition": {
    "groupType": "TimeRelatedGroup",
    "timeRelatedGroup": {
      "columns": ["FiscalMonthNumber", "FiscalMonthName"]
    }
  }
}
```

**ListColumnGroups** - List column groups in calendar
```json
{
  "operation": "ListColumnGroups",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar"
}
```

**GetColumnGroup** - Get column group definition
```json
{
  "operation": "GetColumnGroup",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "columnGroupIndex": 0
}
```

**UpdateColumnGroup** - Update column group
```json
{
  "operation": "UpdateColumnGroup",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "columnGroupIndex": 0,
  "columnGroupUpdateDefinition": {
    "groupType": "TimeRelatedGroup",
    "timeRelatedGroup": {
      "columns": ["FiscalMonthNumber", "FiscalMonthName", "FiscalMonthShortName"]
    }
  }
}
```

**DeleteColumnGroup** - Delete column group
```json
{
  "operation": "DeleteColumnGroup",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "columnGroupIndex": 1
}
```

**ExportTMDL** - Export calendar as TMDL
```json
{
  "operation": "ExportTMDL",
  "tableName": "DimDate",
  "calendarName": "Fiscal Calendar",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- Calendars require compatibilityLevel >= 1701
- timeUnit values: Years, Quarters, Months, Weeks, Days
- TimeRelatedGroup: groups related columns together
- TimeUnitAssociation: defines primary column + associations
- Used by DAX time intelligence functions for calendar awareness

---

## 11. Partitions

### partition_operations

**Purpose**: Manage table partitions for data loading

#### Operations

**List** - List partitions (optionally filter by table)
```json
{
  "operation": "List",
  "tableName": "FactSales"
}
```

**Get** - Get partition definition
```json
{
  "operation": "Get",
  "tableName": "FactSales",
  "partitionName": "Sales_2024"
}
```

**Create** - Create new partition

M Expression partition:
```json
{
  "operation": "Create",
  "tableName": "FactSales",
  "createDefinition": {
    "name": "Sales_2024",
    "mode": "Import",
    "sourceType": "M",
    "expression": "let\n  Source = Sql.Database(\"server\", \"db\"),\n  Sales = Source{[Schema=\"dbo\",Item=\"Sales\"]}[Data],\n  Filtered = Table.SelectRows(Sales, each [Year] = 2024)\nin\n  Filtered"
  }
}
```

SQL Query partition:
```json
{
  "operation": "Create",
  "tableName": "FactSales",
  "createDefinition": {
    "name": "Sales_2024",
    "mode": "Import",
    "sourceType": "Query",
    "dataSourceName": "SQLServer",
    "query": "SELECT * FROM Sales WHERE Year = 2024"
  }
}
```

Calculated partition:
```json
{
  "operation": "Create",
  "tableName": "DateTable",
  "createDefinition": {
    "name": "Dates",
    "mode": "Import",
    "sourceType": "Calculated",
    "expression": "CALENDAR(DATE(2020,1,1), DATE(2025,12,31))"
  }
}
```

Named Expression partition (Power Query):
```json
{
  "operation": "Create",
  "tableName": "Products",
  "createDefinition": {
    "name": "Products_Part1",
    "mode": "Import",
    "sourceType": "M",
    "expressionSourceName": "Products_Query",
    "queryGroupName": "Shared Queries"
  }
}
```

**Update** - Update partition properties
```json
{
  "operation": "Update",
  "tableName": "FactSales",
  "partitionName": "Sales_2024",
  "updateDefinition": {
    "query": "SELECT * FROM Sales WHERE Year = 2024 AND Status = 'Active'",
    "description": "Active sales for 2024"
  }
}
```

**Delete** - Delete partition
```json
{
  "operation": "Delete",
  "tableName": "FactSales",
  "partitionName": "Old_Partition"
}
```

**Refresh** - Refresh partition data
```json
{
  "operation": "Refresh",
  "tableName": "FactSales",
  "partitionName": "Sales_2024",
  "refreshType": "Full"
}
```

**Rename** - Rename partition
```json
{
  "operation": "Rename",
  "tableName": "FactSales",
  "partitionName": "Part1",
  "newName": "Sales_2024"
}
```

**ExportTMDL** - Export partition as TMDL
```json
{
  "operation": "ExportTMDL",
  "tableName": "FactSales",
  "partitionName": "Sales_2024",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**ExportTMSL** - Export partition as TMSL
```json
{
  "operation": "ExportTMSL",
  "tableName": "FactSales",
  "partitionName": "Sales_2024",
  "tmslExportOptions": {
    "tmslOperationType": "Refresh",
    "refreshType": "Full",
    "formatJson": true
  }
}
```

**Partition Types**:
- **M**: Power Query expression
- **Query**: SQL query (legacy)
- **Calculated**: DAX table expression
- **Entity**: Dataflow reference
- **PolicyRange**: Incremental refresh policy

**Technical Details**:
- mode: Import, DirectQuery, Dual
- Multiple partitions enable parallel loading
- Incremental refresh uses PolicyRange partitions
- retainDataTillForceCalculate: controls data retention

---

## 12. Perspectives

### perspective_operations

**Purpose**: Manage perspectives and perspective members

#### Operations

##### Perspective Operations

**List** - List all perspectives
```json
{
  "operation": "list_perspectives"
}
```

**Get** - Get perspective definition
```json
{
  "operation": "get_perspective",
  "perspectiveName": "Sales Analysis"
}
```

**Create** - Create new perspective
```json
{
  "operation": "create_perspective",
  "createDefinition": {
    "name": "Sales Analysis",
    "description": "Sales team perspective with key metrics"
  }
}
```

**Update** - Update perspective properties
```json
{
  "operation": "update_perspective",
  "perspectiveName": "Sales Analysis",
  "updateDefinition": {
    "description": "Updated sales analysis view"
  }
}
```

**Delete** - Delete perspective
```json
{
  "operation": "delete_perspective",
  "perspectiveName": "Old Perspective"
}
```

**Rename** - Rename perspective
```json
{
  "operation": "rename_perspective",
  "perspectiveName": "Sales",
  "newPerspectiveName": "Sales Analysis"
}
```

##### Perspective Table Operations

**ListTables** - List tables in perspective
```json
{
  "operation": "list_perspective_tables",
  "perspectiveName": "Sales Analysis"
}
```

**GetTable** - Get perspective table definition
```json
{
  "operation": "get_perspective_table",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales"
}
```

**AddTable** - Add table to perspective
```json
{
  "operation": "add_table_to_perspective",
  "perspectiveName": "Sales Analysis",
  "tableCreateDefinition": {
    "tableName": "FactSales",
    "includeAll": false
  }
}
```

**RemoveTable** - Remove table from perspective
```json
{
  "operation": "remove_table_from_perspective",
  "perspectiveName": "Sales Analysis",
  "tableName": "DimInternal"
}
```

**UpdateTable** - Update perspective table properties
```json
{
  "operation": "update_perspective_table",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales",
  "tableUpdateDefinition": {
    "includeAll": true
  }
}
```

##### Perspective Column Operations

**ListColumns** - List columns in perspective table
```json
{
  "operation": "list_perspective_columns",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales"
}
```

**GetColumn** - Get perspective column definition
```json
{
  "operation": "get_perspective_column",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales",
  "columnName": "SalesAmount"
}
```

**AddColumn** - Add column to perspective
```json
{
  "operation": "add_column_to_perspective_table",
  "perspectiveName": "Sales Analysis",
  "columnCreateDefinition": {
    "tableName": "FactSales",
    "columnName": "SalesAmount"
  }
}
```

**RemoveColumn** - Remove column from perspective
```json
{
  "operation": "remove_column_from_perspective_table",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales",
  "columnName": "InternalCost"
}
```

##### Perspective Measure Operations

**ListMeasures** - List measures in perspective
```json
{
  "operation": "list_perspective_measures",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales"
}
```

**GetMeasure** - Get perspective measure definition
```json
{
  "operation": "get_perspective_measure",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales",
  "measureName": "Total Sales"
}
```

**AddMeasure** - Add measure to perspective
```json
{
  "operation": "add_measure_to_perspective_table",
  "perspectiveName": "Sales Analysis",
  "measureCreateDefinition": {
    "tableName": "FactSales",
    "measureName": "Total Sales"
  }
}
```

**RemoveMeasure** - Remove measure from perspective
```json
{
  "operation": "remove_measure_from_perspective_table",
  "perspectiveName": "Sales Analysis",
  "tableName": "FactSales",
  "measureName": "Internal Metric"
}
```

##### Perspective Hierarchy Operations

**ListHierarchies** - List hierarchies in perspective
```json
{
  "operation": "list_perspective_hierarchies",
  "perspectiveName": "Sales Analysis",
  "tableName": "DimProduct"
}
```

**GetHierarchy** - Get perspective hierarchy definition
```json
{
  "operation": "get_perspective_hierarchy",
  "perspectiveName": "Sales Analysis",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy"
}
```

**AddHierarchy** - Add hierarchy to perspective
```json
{
  "operation": "add_hierarchy_to_perspective_table",
  "perspectiveName": "Sales Analysis",
  "hierarchyCreateDefinition": {
    "tableName": "DimProduct",
    "hierarchyName": "Product Hierarchy"
  }
}
```

**RemoveHierarchy** - Remove hierarchy from perspective
```json
{
  "operation": "remove_hierarchy_from_perspective_table",
  "perspectiveName": "Sales Analysis",
  "tableName": "DimProduct",
  "hierarchyName": "Internal Hierarchy"
}
```

**ExportTMDL** - Export perspective as TMDL
```json
{
  "operation": "ExportTMDL",
  "perspectiveName": "Sales Analysis",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- Perspectives are client-side filters on metadata
- includeAll: automatically includes all current and future members
- Useful for role-based model views
- No performance impact - metadata filtering only

---

## 13. Security Roles

### security_role_operations

**Purpose**: Manage Row-Level Security (RLS) roles

#### Operations

##### Role Operations

**List** - List all roles
```json
{
  "operation": "List"
}
```

**Get** - Get role definition
```json
{
  "operation": "Get",
  "roleName": "Sales Team"
}
```

**Create** - Create new role
```json
{
  "operation": "Create",
  "createRoleDefinition": {
    "name": "Sales Team",
    "description": "Sales team members",
    "modelPermission": "Read"
  }
}
```

**Update** - Update role properties
```json
{
  "operation": "Update",
  "roleName": "Sales Team",
  "updateRoleDefinition": {
    "description": "Updated sales team role",
    "modelPermission": "Read"
  }
}
```

**Delete** - Delete role
```json
{
  "operation": "Delete",
  "roleName": "Old Role"
}
```

**Rename** - Rename role
```json
{
  "operation": "Rename",
  "roleName": "Sales",
  "newRoleName": "Sales Team"
}
```

##### Table Permission Operations

**ListPermissions** - List table permissions for role
```json
{
  "operation": "ListPermissions",
  "roleName": "Sales Team"
}
```

**GetPermission** - Get table permission definition
```json
{
  "operation": "GetPermission",
  "roleName": "Sales Team",
  "tableName": "FactSales"
}
```

**CreatePermission** - Create table permission (RLS filter)
```json
{
  "operation": "CreatePermission",
  "roleName": "Sales Team",
  "createTablePermissionDefinition": {
    "tableName": "FactSales",
    "filterExpression": "[RegionKey] = LOOKUPVALUE(DimEmployee[RegionKey], DimEmployee[Email], USERPRINCIPALNAME())",
    "metadataPermission": "None"
  }
}
```

Advanced RLS patterns:

Static filter:
```json
{
  "tableName": "FactSales",
  "filterExpression": "[SalesRegion] = \"EMEA\""
}
```

Dynamic user-based filter:
```json
{
  "tableName": "DimSalesperson",
  "filterExpression": "[Email] = USERPRINCIPALNAME()"
}
```

Manager hierarchy:
```json
{
  "tableName": "DimEmployee",
  "filterExpression": "PATHCONTAINS(PATH([EmployeeKey], [ManagerKey]), LOOKUPVALUE(DimEmployee[EmployeeKey], DimEmployee[Email], USERPRINCIPALNAME()))"
}
```

**UpdatePermission** - Update table permission
```json
{
  "operation": "UpdatePermission",
  "roleName": "Sales Team",
  "tableName": "FactSales",
  "updateTablePermissionDefinition": {
    "filterExpression": "[RegionKey] IN VALUES(DimUserRegions[RegionKey])"
  }
}
```

**DeletePermission** - Delete table permission
```json
{
  "operation": "DeletePermission",
  "roleName": "Sales Team",
  "tableName": "FactSales"
}
```

**GetEffectivePermissions** - Test role permissions for user
```json
{
  "operation": "GetEffectivePermissions",
  "roleName": "Sales Team"
}
```

**ExportTMDL** - Export role as TMDL
```json
{
  "operation": "ExportTMDL",
  "roleName": "Sales Team",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**ExportTMSL** - Export role as TMSL
```json
{
  "operation": "ExportTMSL",
  "roleName": "Sales Team",
  "tmslExportOptions": {
    "tmslOperationType": "Create",
    "formatJson": true
  }
}
```

**Technical Details**:
- modelPermission: Read, ReadRefresh, Refresh, Administrator
- metadataPermission: None, Default (controls metadata visibility)
- filterExpression: DAX boolean expression per row
- Use USERPRINCIPALNAME() for dynamic security
- Test with "View As" in Power BI Desktop
- securityFilteringBehavior on relationships affects filter propagation

---

## 14. Cultures & Translations

### culture_operations

**Purpose**: Manage model localization cultures

#### Operations

**List** - List all cultures in model
```json
{
  "operation": "List"
}
```

**Get** - Get culture definition
```json
{
  "operation": "Get",
  "cultureName": "fr-FR"
}
```

**Create** - Create new culture
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "fr-FR",
    "description": "French translations"
  }
}
```

**Update** - Update culture properties
```json
{
  "operation": "Update",
  "cultureName": "fr-FR",
  "updateDefinition": {
    "description": "Updated French translations"
  }
}
```

**Delete** - Delete culture
```json
{
  "operation": "Delete",
  "cultureName": "de-DE"
}
```

**Rename** - Rename culture
```json
{
  "operation": "Rename",
  "cultureName": "fr",
  "newCultureName": "fr-FR"
}
```

**GetValidNames** - Get list of valid culture names
```json
{
  "operation": "GetValidNames",
  "includeNeutralCultures": true,
  "includeUserCustomCultures": false
}
```

**GetValidDetails** - Get detailed culture information
```json
{
  "operation": "GetValidDetails",
  "includeNeutralCultures": true
}
```
Returns: LCID, culture name, display name, language

**GetDetailsByName** - Get culture details by name
```json
{
  "operation": "GetDetailsByName",
  "cultureName": "fr-FR"
}
```

**GetDetailsByLCID** - Get culture details by LCID
```json
{
  "operation": "GetDetailsByLCID",
  "lcid": 1036
}
```

**ExportTMDL** - Export culture as TMDL
```json
{
  "operation": "ExportTMDL",
  "cultureName": "fr-FR",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- Culture names follow BCP 47 (e.g., en-US, fr-FR, de-DE)
- LCID: Windows Locale Identifier (integer)
- Neutral cultures: just language (e.g., "en", "fr")
- includeNeutralCultures: include "en" in addition to "en-US"

---

### object_translation_operations

**Purpose**: Manage translations for model objects

#### Operations

**List** - List translations (with filters)
```json
{
  "operation": "List",
  "listFilters": {
    "filterCultureName": "fr-FR",
    "filterObjectType": "Measure",
    "filterObjectName": "Total Sales"
  }
}
```

**Get** - Get specific translation
```json
{
  "operation": "Get",
  "getDefinition": {
    "cultureName": "fr-FR",
    "objectType": "Measure",
    "tableName": "FactSales",
    "measureName": "Total Sales",
    "property": "Caption"
  }
}
```

**Create** - Create translation
```json
{
  "operation": "Create",
  "createDefinition": {
    "cultureName": "fr-FR",
    "objectType": "Measure",
    "tableName": "FactSales",
    "measureName": "Total Sales",
    "property": "Caption",
    "value": "Total des Ventes",
    "createCultureIfNotExists": true
  }
}
```

**Update** - Update translation
```json
{
  "operation": "Update",
  "updateDefinition": {
    "cultureName": "fr-FR",
    "objectType": "Table",
    "tableName": "FactSales",
    "property": "Caption",
    "value": "Ventes Factuelles"
  }
}
```

**Delete** - Delete translation
```json
{
  "operation": "Delete",
  "deleteDefinition": {
    "cultureName": "de-DE",
    "objectType": "Column",
    "tableName": "FactSales",
    "columnName": "SalesAmount",
    "property": "Caption"
  }
}
```

**Object Types**:
- Model
- Table
- Column
- Measure
- Hierarchy
- Level
- KPI

**Translatable Properties**:
- Caption (display name)
- Description
- DisplayFolder

**Translation Examples**:

Table translation:
```json
{
  "cultureName": "es-ES",
  "objectType": "Table",
  "tableName": "FactSales",
  "property": "Caption",
  "value": "Hechos de Ventas"
}
```

Measure translation with description:
```json
{
  "cultureName": "fr-FR",
  "objectType": "Measure",
  "tableName": "FactSales",
  "measureName": "Total Sales",
  "property": "Description",
  "value": "Montant total des ventes"
}
```

Hierarchy level translation:
```json
{
  "cultureName": "de-DE",
  "objectType": "Level",
  "tableName": "DimProduct",
  "hierarchyName": "Product Hierarchy",
  "levelName": "Category",
  "property": "Caption",
  "value": "Kategorie"
}
```

---

## 15. Query Groups & Named Expressions

### query_group_operations

**Purpose**: Manage Power Query group organization

#### Operations

**LIST** - List all query groups
```json
{
  "operation": "LIST"
}
```

**GET** - Get query group definition
```json
{
  "operation": "GET",
  "queryGroupName": "Shared Queries"
}
```

**CREATE** - Create query group
```json
{
  "operation": "CREATE",
  "createDefinition": {
    "folder": "Shared Queries",
    "description": "Shared Power Query expressions"
  }
}
```

**UPDATE** - Update query group
```json
{
  "operation": "UPDATE",
  "queryGroupName": "Shared Queries",
  "updateDefinition": {
    "description": "Updated shared queries",
    "folder": "Shared\\Common"
  }
}
```

**DELETE** - Delete query group
```json
{
  "operation": "DELETE",
  "queryGroupName": "Old Queries"
}
```

**ExportTMDL** - Export query group as TMDL
```json
{
  "operation": "ExportTMDL",
  "queryGroupName": "Shared Queries",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

---

### named_expression_operations

**Purpose**: Manage Power Query expressions and parameters

#### Operations

**List** - List all named expressions
```json
{
  "operation": "List"
}
```

**Get** - Get named expression definition
```json
{
  "operation": "Get",
  "namedExpressionName": "Products_Query"
}
```

**Create** - Create named expression (Power Query)
```json
{
  "operation": "Create",
  "createDefinition": {
    "name": "Products_Query",
    "kind": "M",
    "expression": "let\n  Source = Sql.Database(\"server\", \"db\"),\n  Products = Source{[Schema=\"dbo\",Item=\"Products\"]}[Data]\nin\n  Products",
    "description": "Products from SQL Server",
    "queryGroupName": "Shared Queries"
  }
}
```

**CreateParameter** - Create Power Query parameter
```json
{
  "operation": "CreateParameter",
  "createDefinition": {
    "name": "ServerName",
    "kind": "M",
    "expression": "\"localhost\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]",
    "description": "SQL Server name parameter"
  }
}
```

Parameter with metadata:
```m
"default_value" meta [
  IsParameterQuery=true, 
  Type="Text", 
  IsParameterQueryRequired=true,
  List={"value1", "value2", "value3"}
]
```

**Update** - Update named expression
```json
{
  "operation": "Update",
  "namedExpressionName": "Products_Query",
  "updateDefinition": {
    "expression": "let\n  Source = Sql.Database(ServerName, \"db\"),\n  Products = Source{[Schema=\"dbo\",Item=\"Products\"]}[Data],\n  Filtered = Table.SelectRows(Products, each [IsActive] = true)\nin\n  Filtered"
  }
}
```

**Delete** - Delete named expression
```json
{
  "operation": "Delete",
  "namedExpressionName": "Old_Query"
}
```

**Rename** - Rename named expression
```json
{
  "operation": "Rename",
  "renameDefinition": {
    "currentName": "Prod_Query",
    "newName": "Products_Query"
  }
}
```

**ExportTMDL** - Export named expression as TMDL
```json
{
  "operation": "ExportTMDL",
  "namedExpressionName": "Products_Query",
  "tmdlExportOptions": {
    "maxReturnCharacters": -1
  }
}
```

**Technical Details**:
- kind: "M" for Power Query, "DAX" for calculations
- Named expressions are shared M queries
- Parameters have meta tags with parameter metadata
- queryGroupName: organizes expressions into folders

---

## 16. Trace Operations

### trace_operations

**Purpose**: Capture and analyze query execution traces

#### Operations

**Start** - Start trace capture
```json
{
  "operation": "Start",
  "events": [
    "QueryBegin",
    "QueryEnd",
    "VertiPaqSEQueryBegin",
    "VertiPaqSEQueryEnd",
    "DirectQueryBegin",
    "DirectQueryEnd",
    "ExecutionMetrics"
  ],
  "filterCurrentSessionOnly": true
}
```

**Default Events** (if not specified):
- CommandBegin/CommandEnd
- QueryBegin/QueryEnd
- VertiPaqSEQueryBegin/VertiPaqSEQueryEnd
- VertiPaqSEQueryCacheMatch
- DirectQueryBegin/DirectQueryEnd
- ExecutionMetrics
- Error

**Stop** - Stop trace capture
```json
{
  "operation": "Stop"
}
```

**Pause** - Pause trace capture
```json
{
  "operation": "Pause"
}
```

**Resume** - Resume trace capture
```json
{
  "operation": "Resume"
}
```

**Clear** - Clear captured events
```json
{
  "operation": "Clear"
}
```

**Get** - Get trace status
```json
{
  "operation": "Get"
}
```

**List** - List all active traces
```json
{
  "operation": "List"
}
```

**Fetch** - Fetch captured events
```json
{
  "operation": "Fetch",
  "columns": [
    "EventClassName",
    "EventSubclassName",
    "StartTime",
    "Duration",
    "CpuTime",
    "TextData"
  ],
  "clearAfterFetch": false
}
```

**Available Columns**:
- EventClassName, EventSubclassName
- TextData (query text)
- DatabaseName
- ActivityId, RequestId, SessionId
- ApplicationName
- CurrentTime, StartTime, EndTime
- Duration, CpuTime
- NTUserName
- RequestProperties, RequestParameters
- ObjectName, ObjectPath, ObjectReference
- Spid, IntegerData
- ProgressTotal, ObjectId
- Error

**ExportJSON** - Export trace events to JSON file
```json
{
  "operation": "ExportJSON",
  "filePath": "C:\\Traces\\query_trace.json",
  "clearAfterFetch": false
}
```

**Use Cases**:

Performance analysis:
```json
{
  "operation": "Start",
  "events": ["QueryBegin", "QueryEnd", "ExecutionMetrics"]
}
```

VertiPaq SE debugging:
```json
{
  "operation": "Start",
  "events": [
    "VertiPaqSEQueryBegin",
    "VertiPaqSEQueryEnd",
    "VertiPaqSEQueryCacheMatch"
  ]
}
```

DirectQuery monitoring:
```json
{
  "operation": "Start",
  "events": ["DirectQueryBegin", "DirectQueryEnd"]
}
```

**Technical Details**:
- Uses Analysis Services SessionTrace
- filterCurrentSessionOnly: true captures only current session events
- ExecutionMetrics provides detailed timing breakdown
- Duration/CpuTime in milliseconds
- ActivityId links related events
- clearAfterFetch: controls event buffer management

---

## 17. Transaction Management

### transaction_operations

**Purpose**: Manage ACID transactions for atomic changes

#### Operations

**Begin** - Start transaction
```json
{
  "operation": "Begin",
  "connectionName": "MyModel"
}
```
Returns: transactionId

**Commit** - Commit transaction changes
```json
{
  "operation": "Commit",
  "transactionId": "txn-12345"
}
```

**Rollback** - Rollback transaction changes
```json
{
  "operation": "Rollback",
  "transactionId": "txn-12345"
}
```

**GetStatus** - Get transaction status
```json
{
  "operation": "GetStatus",
  "transactionId": "txn-12345"
}
```

**ListActive** - List all active transactions
```json
{
  "operation": "ListActive"
}
```

**Transaction Usage Pattern**:

```javascript
// 1. Begin transaction
let txn = await beginTransaction()

try {
  // 2. Perform multiple operations
  await createMeasure(...)
  await createColumn(...)
  await updateRelationship(...)
  
  // 3. Commit if all succeed
  await commitTransaction(txn.transactionId)
  
} catch (error) {
  // 4. Rollback on error
  await rollbackTransaction(txn.transactionId)
}
```

**Technical Details**:
- Provides atomicity for multi-step operations
- All changes pending until commit
- Rollback restores previous state
- Nested transactions not supported
- Transaction scope limited to single connection

---

## 18. Batch Operations

### batch_table_operations

**Purpose**: Batch operations on tables

#### Operations

**BatchCreate** - Create multiple tables
```json
{
  "operation": "BatchCreate",
  "batchCreateRequest": {
    "items": [
      {
        "name": "DimProduct",
        "mode": "Import",
        "partitionName": "Products",
        "dataSourceName": "SQL"
      },
      {
        "name": "DimCustomer",
        "mode": "Import",
        "partitionName": "Customers",
        "dataSourceName": "SQL"
      }
    ],
    "options": {
      "useTransaction": true,
      "continueOnError": false
    }
  }
}
```

**BatchUpdate** - Update multiple tables
**BatchDelete** - Delete multiple tables
**BatchGet** - Get multiple table definitions
**BatchRename** - Rename multiple tables

---

### batch_column_operations

**Purpose**: Batch operations on columns

#### Operations

**BatchCreate** - Create multiple columns
```json
{
  "operation": "BatchCreate",
  "batchCreateRequest": {
    "items": [
      {
        "tableName": "FactSales",
        "name": "TotalCost",
        "expression": "[UnitCost] * [Quantity]",
        "dataType": "Decimal"
      },
      {
        "tableName": "FactSales",
        "name": "Profit",
        "expression": "[SalesAmount] - [TotalCost]",
        "dataType": "Decimal"
      }
    ],
    "options": {
      "useTransaction": true,
      "continueOnError": false
    }
  }
}
```

**BatchUpdate** - Update multiple columns
**BatchDelete** - Delete multiple columns
**BatchGet** - Get multiple column definitions
**BatchRename** - Rename multiple columns

---

### batch_measure_operations

**Purpose**: Batch operations on measures

#### Operations

**BatchCreate** - Create multiple measures
```json
{
  "operation": "BatchCreate",
  "batchCreateRequest": {
    "items": [
      {
        "name": "Total Sales",
        "tableName": "_Measures",
        "expression": "SUM(FactSales[SalesAmount])",
        "formatString": "$#,0.00"
      },
      {
        "name": "Total Quantity",
        "tableName": "_Measures",
        "expression": "SUM(FactSales[Quantity])",
        "formatString": "#,0"
      },
      {
        "name": "Avg Price",
        "tableName": "_Measures",
        "expression": "DIVIDE([Total Sales], [Total Quantity])",
        "formatString": "$#,0.00"
      }
    ],
    "options": {
      "useTransaction": true,
      "continueOnError": false
    }
  }
}
```

**BatchUpdate** - Update multiple measures
**BatchDelete** - Delete multiple measures
**BatchGet** - Get multiple measure definitions
**BatchRename** - Rename multiple measures
**BatchMove** - Move multiple measures between tables

---

### batch_function_operations

**Purpose**: Batch operations on user-defined functions

**Operations**: BatchCreate, BatchUpdate, BatchDelete, BatchGet, BatchRename

---

### batch_perspective_operations

**Purpose**: Batch operations on perspective members

#### Operations

**BatchAddTables** - Add multiple tables to perspective
```json
{
  "operation": "BatchAddTables",
  "batchAddPerspectiveTablesRequest": {
    "perspectiveName": "Sales View",
    "items": [
      {
        "tableName": "FactSales",
        "includeAll": true
      },
      {
        "tableName": "DimProduct",
        "includeAll": false
      }
    ],
    "options": {
      "useTransaction": true,
      "continueOnError": false
    }
  }
}
```

**BatchAddColumns** - Add multiple columns to perspective
**BatchAddMeasures** - Add multiple measures to perspective
**BatchAddHierarchies** - Add multiple hierarchies to perspective
**BatchRemoveTables/Columns/Measures/Hierarchies** - Remove multiple members
**BatchGetTables/Columns/Measures/Hierarchies** - Get multiple member definitions
**BatchUpdateTables** - Update multiple table properties

---

### batch_object_translation_operations

**Purpose**: Batch operations on object translations

#### Operations

**BatchCreate** - Create multiple translations
```json
{
  "operation": "BatchCreate",
  "batchCreateRequest": {
    "items": [
      {
        "cultureName": "fr-FR",
        "objectType": "Table",
        "tableName": "FactSales",
        "property": "Caption",
        "value": "Ventes",
        "createCultureIfNotExists": true
      },
      {
        "cultureName": "fr-FR",
        "objectType": "Measure",
        "tableName": "FactSales",
        "measureName": "Total Sales",
        "property": "Caption",
        "value": "Total des Ventes"
      },
      {
        "cultureName": "fr-FR",
        "objectType": "Column",
        "tableName": "FactSales",
        "columnName": "SalesAmount",
        "property": "Caption",
        "value": "Montant"
      }
    ],
    "options": {
      "useTransaction": true,
      "continueOnError": false
    }
  }
}
```

**BatchUpdate** - Update multiple translations
**BatchDelete** - Delete multiple translations
**BatchGet** - Get multiple translation definitions

**Batch Operation Options**:
- **useTransaction**: true = atomic (all-or-nothing), false = individual operations
- **continueOnError**: true = continue on errors, false = stop on first error

---

## 19. Export Capabilities

### TMDL Export (YAML-like format)

**Purpose**: Human-readable, source control friendly format

**Format**: Hierarchical text format similar to YAML

**Export Options**:
```json
{
  "filePath": "C:\\Export\\object.tmdl",
  "maxReturnCharacters": -1,
  "serializationOptions": {
    "includeChildren": true,
    "includeInferredDataTypes": false,
    "includeRestrictedInformation": false
  }
}
```

**Options**:
- **filePath**: Optional file path to save
- **maxReturnCharacters**: 
  - -1 = no limit (full content)
  - 0 = don't return (only save to file)
  - >0 = limit characters returned
- **includeChildren**: Include child objects (tables → columns, measures)
- **includeInferredDataTypes**: Include system-inferred types
- **includeRestrictedInformation**: Include internal metadata

**Sample TMDL Output**:
```tmdl
table FactSales
  lineageTag: abc123
  
  measure 'Total Sales'
    expression: SUM(FactSales[SalesAmount])
    formatString: $#,0.00
    lineageTag: def456
  
  column SalesAmount
    dataType: decimal
    sourceColumn: SalesAmount
    summarizeBy: sum
    lineageTag: ghi789
```

**Supported Objects**:
- Database
- Model
- Tables
- Columns
- Measures
- Functions
- Calculation Groups
- Hierarchies
- Calendars
- Partitions
- Relationships
- Perspectives
- Security Roles
- Cultures
- Query Groups
- Named Expressions

---

### TMSL Export (JSON script format)

**Purpose**: Executable JSON scripts for deployment

**Format**: JSON-based TMSL (Tabular Model Scripting Language)

**Export Options**:
```json
{
  "filePath": "C:\\Export\\script.json",
  "maxReturnCharacters": -1,
  "formatJson": true,
  "tmslOperationType": "CreateOrReplace",
  "refreshType": "Full",
  "includeRestricted": false
}
```

**TMSL Operation Types**:
- **Create**: Create new object
- **CreateOrReplace**: Create or replace if exists
- **Alter**: Modify existing object
- **Delete**: Delete object
- **Refresh**: Refresh data

**Sample TMSL Output**:
```json
{
  "createOrReplace": {
    "object": {
      "database": "Model",
      "table": "FactSales"
    },
    "table": {
      "name": "FactSales",
      "columns": [
        {
          "name": "SalesAmount",
          "dataType": "decimal",
          "sourceColumn": "SalesAmount"
        }
      ],
      "measures": [
        {
          "name": "Total Sales",
          "expression": "SUM(FactSales[SalesAmount])"
        }
      ]
    }
  }
}
```

**Execution**: TMSL scripts can be executed via:
- SQL Server Management Studio (SSMS)
- XMLA endpoints
- PowerShell with AMO
- REST API

---

## 20. Performance Best Practices

### Connection Management

**Reuse Connections**:
```javascript
// GOOD: Reuse connection
let conn = await connect()
await operation1(conn)
await operation2(conn)
await operation3(conn)
await disconnect(conn)

// BAD: Reconnect for each operation
await connect()
await operation1()
await disconnect()
await connect()
await operation2()
await disconnect()
```

**Close Explicitly**:
```javascript
try {
  let conn = await connect()
  await doWork(conn)
} finally {
  await disconnect(conn)
}
```

---

### Transaction Management

**Use Transactions for Batch Changes**:
```javascript
let txn = await beginTransaction()
try {
  await batchCreateMeasures(items)
  await commitTransaction(txn)
} catch (error) {
  await rollbackTransaction(txn)
}
```

**Keep Transaction Scope Tight**:
```javascript
// GOOD: Short-lived transaction
await beginTransaction()
await quickOperations()
await commit()

// BAD: Long-lived transaction
await beginTransaction()
await longRunningQuery()  // Don't do this
await commit()
```

---

### Batch Operations

**Prefer Batch Over Individual**:
```javascript
// GOOD: Single batch operation
await batchCreateMeasures([m1, m2, m3, m4, m5])

// BAD: Multiple individual operations
await createMeasure(m1)
await createMeasure(m2)
await createMeasure(m3)
await createMeasure(m4)
await createMeasure(m5)
```

**Use Transaction Option**:
```json
{
  "options": {
    "useTransaction": true,    // Atomic operation
    "continueOnError": false   // Fail fast
  }
}
```

---

### Query Performance

**Limit Result Sets**:
```javascript
// Use maxRows to limit results
await executeQuery(dax, { maxRows: 1000 })

// Use TOPN in DAX
"EVALUATE TOPN(100, FactSales)"
```

**Clear Cache for Testing**:
```javascript
// Clear before performance testing
await clearCache()
await executeQuery(dax, { getExecutionMetrics: true })
```

**Use Execution Metrics**:
```javascript
let result = await executeQuery(dax, {
  getExecutionMetrics: true,
  executionMetricsOnly: true  // Faster if you only need metrics
})
```

---

### Export Optimization

**Control Output Size**:
```json
{
  "maxReturnCharacters": 10000,  // Limit return size
  "filePath": "output.tmdl",     // Write to file
  "serializationOptions": {
    "includeChildren": false,     // Exclude children
    "includeRestrictedInformation": false
  }
}
```

**Use Appropriate Format**:
- **TMDL**: Source control, human review
- **TMSL**: Deployment scripts, automation

---

### Trace Best Practices

**Filter Events**:
```javascript
// Only capture needed events
await startTrace({
  events: ["QueryBegin", "QueryEnd"],
  filterCurrentSessionOnly: true
})
```

**Clear Buffers**:
```javascript
// Prevent memory buildup
await fetchEvents({ clearAfterFetch: true })
```

**Export Large Traces**:
```javascript
// Write directly to file for large traces
await exportTraceJSON({ 
  filePath: "trace.json",
  clearAfterFetch: true 
})
```

---

### Model Size Management

**Delete Cascade**:
```javascript
// Clean up dependent objects
await deleteTable("OldTable", { shouldCascadeDelete: true })
```

**Partition Strategy**:
- Use multiple partitions for parallel loading
- Implement incremental refresh for large facts
- Delete old partitions to manage size

**Hidden Objects**:
```javascript
// Hide intermediate calculations
await updateColumn({ isHidden: true })
```

---

### Error Handling

**Check Connection Before Operations**:
```javascript
let conn = await getConnection()
if (!conn.isConnected) {
  await connect()
}
```

**Validate Before Execute**:
```javascript
// Validate DAX syntax first
let validation = await validateQuery(dax)
if (validation.isValid) {
  await executeQuery(dax)
}
```

**Graceful Failure**:
```javascript
try {
  await batchOperation(items, {
    continueOnError: true,  // Continue despite errors
    useTransaction: false   // Don't rollback all on error
  })
} catch (error) {
  console.log("Some operations failed:", error.results)
}
```

---

## Summary

The Microsoft Official Power BI MCP Server provides comprehensive programmatic access to Power BI semantic models through:

**Core Capabilities**:
- ✅ Full metadata management (tables, columns, measures, relationships)
- ✅ DAX query execution with performance metrics
- ✅ User-defined functions and calculation groups
- ✅ Row-level security (RLS) and perspectives
- ✅ Localization (cultures and translations)
- ✅ Advanced features (hierarchies, calendars, partitions)
- ✅ Query tracing and diagnostics
- ✅ Transaction support for atomic changes
- ✅ Batch operations for efficiency
- ✅ TMDL/TMSL export for source control and deployment

**Connection Options**:
- Power BI Desktop (local XMLA)
- Microsoft Fabric Workspace (cloud XMLA)
- PBIP/TMDL folders (offline)

**Best For**:
- Automated model documentation
- CI/CD pipelines for semantic models
- Bulk metadata operations
- Model analysis and optimization
- Cross-model standardization
- Testing and validation
- Advanced DAX development

**Authentication**:
- Interactive browser auth for Fabric
- Windows authentication for Desktop
- No authentication for PBIP folders

---

## Additional Resources

**Official Documentation**:
- [Power BI MCP Server GitHub](https://github.com/microsoft/powerbi-modeling-mcp)
- [Tabular Object Model (TOM)](https://learn.microsoft.com/analysis-services/tom/)
- [TMSL Reference](https://learn.microsoft.com/analysis-services/tmsl/)
- [TMDL Documentation](https://learn.microsoft.com/power-bi/developer/projects/tmdl-overview)

**Related Tools**:
- [Tabular Editor](https://tabulareditor.com/)
- [DAX Studio](https://daxstudio.org/)
- [SQLBI Tools](https://www.sqlbi.com/tools/)

**Community**:
- [Power BI Community](https://community.powerbi.com/)
- [SQLBI Articles](https://www.sqlbi.com/articles/)
- [Guy in a Cube](https://www.youtube.com/c/GuyinaCube)

---

**Document Version**: 1.0  
**Last Updated**: November 19, 2025  
**Author**: Generated for Bjorn Braet - Finvision Wealth Management
