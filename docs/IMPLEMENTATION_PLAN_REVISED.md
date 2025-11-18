# REVISED Implementation Plan: Embedded Workflow & Agentic Intelligence

**Version:** 2.0 (Revised for Embedded Intelligence)
**Date:** 2025-01-18
**Status:** Planning Phase

---

## 🎯 Core Philosophy: INVISIBLE INTELLIGENCE

**The user should NEVER have to manually invoke intelligence features.**

Instead:
- ✅ **Intent analysis** happens automatically on every request
- ✅ **Recommendations** are automatically added to responses
- ✅ **Workflows** are suggested and executed by the AI automatically
- ✅ **Learning** happens silently in the background
- ✅ **Progress tracking** shows automatically for long operations

---

## Architecture Overview

### User Experience Flow

**User's Perspective:**
```
User: "I need to do a full review of my Power BI model"

Claude (AI): "I'll run a comprehensive model review for you. This includes:
- Connecting to your model
- Running best practice analysis
- Checking relationships
- Generating documentation

Starting now..."

[Progress appears automatically]
⏳ Connecting to Power BI... ✅
⏳ Running BPA analysis... 🔄 45% complete
...
```

**What Happens Behind the Scenes:**
1. User sends natural language request to Claude
2. Claude invokes regular MCP tool (could be any tool)
3. **Intent Middleware** (in MCP server) analyzes the request automatically
4. Server detects "this is a model review request"
5. Server **automatically executes workflow** OR **enriches response with guidance**
6. Claude receives enhanced response with next steps
7. **Learning system** logs the interaction silently

---

## Revised Architecture

### 1. Request Pipeline with Automatic Intelligence

```
User Request
    ↓
Claude AI
    ↓
MCP Call (e.g., "list_tables")
    ↓
┌─────────────────────────────────────┐
│  MCP SERVER (pbixray_server_enhanced.py)  │
│                                     │
│  @app.call_tool()                   │
│  ├─ Intent Middleware (AUTOMATIC)   │ ← Analyzes request context
│  ├─ Workflow Detection (AUTOMATIC)  │ ← Detects multi-step intent
│  ├─ Tool Execution                  │
│  ├─ Response Enrichment (AUTOMATIC) │ ← Adds recommendations
│  └─ Learning Logger (AUTOMATIC)     │ ← Logs for improvement
└─────────────────────────────────────┘
    ↓
Enhanced Response with:
- Original tool result
- _next_steps (automatic recommendations)
- _workflow_suggestion (if applicable)
- _progress (for long operations)
    ↓
Claude AI
    ↓
User sees intelligent, proactive response
```

### 2. Embedded Components (No User Tools Needed)

```
core/intelligence/
├── middleware/
│   ├── intent_middleware.py      # Automatic intent analysis
│   ├── response_enricher.py      # Automatic recommendation injection
│   └── workflow_detector.py      # Automatic workflow detection
├── background/
│   ├── learning_logger.py        # Silent interaction logging
│   └── analytics_aggregator.py   # Background analytics
└── workflows/
    ├── workflow_executor.py      # Execute workflows (called by server)
    └── workflow_templates.py     # Pre-defined workflows
```

### 3. Modified Tool Response Format

Every tool response automatically includes:

```json
{
  "success": true,
  "data": {
    // Original tool result
  },

  // AUTOMATICALLY ADDED BY SERVER:
  "_intelligence": {
    "detected_intent": {
      "category": "analysis",
      "confidence": 0.85,
      "entities": {"model": "Sales_Model"}
    },
    "next_steps": [
      {
        "suggestion": "Run comprehensive BPA analysis",
        "tool": "05_comprehensive_analysis",
        "reason": "Common next step after connecting",
        "priority": "high",
        "auto_params": {"scope": "all"}
      }
    ],
    "workflow_suggestion": {
      "available": true,
      "workflow_name": "Complete Model Review",
      "description": "Automatically analyze your entire model",
      "estimated_duration": "5 minutes",
      "steps": ["connect", "list_tables", "run_bpa", "analyze_relationships", "export_docs"],
      "can_auto_execute": true  // Claude can execute with user permission
    }
  },

  "_progress": {
    // Only present for long-running operations
    "status": "running",
    "percentage": 45,
    "current_step": "Analyzing relationships (3/5)",
    "estimated_remaining_seconds": 60
  }
}
```

---

## Implementation Details

### 1. Intent Middleware (Automatic)

```python
# core/intelligence/middleware/intent_middleware.py

class IntentMiddleware:
    """
    Automatically analyzes intent from request context
    Runs on EVERY tool call
    """

    def __init__(self, config):
        self.config = config
        self.intent_analyzer = IntentAnalyzer(config)

    def analyze_request(self, tool_name: str, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Automatically analyze intent from the request

        This runs in the background on every tool call
        User never sees this - it enriches the response
        """
        # Build request context
        request_context = {
            "tool_name": tool_name,
            "arguments": arguments,
            "session_context": context,
            "previous_tools": context.get("tool_history", [])[-5:],  # Last 5 tools
            "connected_model": context.get("model_name")
        }

        # Analyze intent (fast, <10ms)
        intent = self.intent_analyzer.infer_intent(request_context)

        return {
            "category": intent.category,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "inferred_workflow": intent.suggested_workflow  # None if not applicable
        }
```

### 2. Response Enricher (Automatic)

```python
# core/intelligence/middleware/response_enricher.py

class ResponseEnricher:
    """
    Automatically adds recommendations to every response
    User never calls this - it's middleware
    """

    def __init__(self, config):
        self.config = config
        self.recommendation_engine = RecommendationEngine(config)

    def enrich_response(
        self,
        tool_name: str,
        result: Dict[str, Any],
        intent_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Automatically enrich response with intelligence

        Returns the original result plus _intelligence metadata
        """
        # Don't enrich if tool failed
        if not result.get("success"):
            return result

        # Get next-step recommendations (fast, <20ms)
        next_steps = self.recommendation_engine.get_next_steps(
            tool_name=tool_name,
            result=result,
            intent=intent_data,
            context=context
        )

        # Get workflow suggestion if applicable
        workflow_suggestion = None
        if intent_data.get("inferred_workflow"):
            workflow_suggestion = self._build_workflow_suggestion(
                intent_data["inferred_workflow"],
                context
            )

        # Add intelligence metadata (doesn't modify original result)
        result["_intelligence"] = {
            "detected_intent": {
                "category": intent_data.get("category"),
                "confidence": intent_data.get("confidence"),
                "entities": intent_data.get("entities", {})
            },
            "next_steps": next_steps[:3],  # Top 3 recommendations
            "workflow_suggestion": workflow_suggestion
        }

        return result

    def _build_workflow_suggestion(self, workflow_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build workflow suggestion for Claude"""
        from core.intelligence.workflows.workflow_templates import WorkflowTemplates

        template = WorkflowTemplates.get_template(workflow_id)
        if not template:
            return None

        return {
            "available": True,
            "workflow_id": workflow_id,
            "workflow_name": template.template_name,
            "description": template.description,
            "estimated_duration": f"{template.estimated_duration_seconds // 60} minutes",
            "steps": [s["step_name"] for s in template.step_templates],
            "can_auto_execute": True,  # Claude can execute this
            "message_to_claude": (
                f"Suggest to the user: 'I can run the {template.template_name} workflow "
                f"which will automatically {template.description.lower()}. "
                f"This takes about {template.estimated_duration_seconds // 60} minutes. "
                f"Would you like me to proceed?'"
            )
        }
```

### 3. Modified Main Server Integration

```python
# src/pbixray_server_enhanced.py (MODIFIED)

from core.intelligence.middleware.intent_middleware import IntentMiddleware
from core.intelligence.middleware.response_enricher import ResponseEnricher
from core.intelligence.background.learning_logger import LearningLogger

# Initialize intelligence middleware (runs automatically)
intent_middleware = IntentMiddleware(config)
response_enricher = ResponseEnricher(config)
learning_logger = LearningLogger(config)

# Maintain session context for intelligence
session_context = {
    "tool_history": [],
    "model_name": None,
    "last_analysis_run": None,
    "user_preferences": {}
}

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Execute tool with AUTOMATIC intelligence"""
    try:
        _t0 = time.time()

        # Update session context
        if connection_state.is_connected():
            session_context["model_name"] = connection_state.current_model_name

        # 1. AUTOMATIC: Analyze intent (runs in background, <10ms)
        intent_data = intent_middleware.analyze_request(
            tool_name=name,
            arguments=arguments,
            context=session_context
        )

        # ... existing validation and rate limiting ...

        # 2. Execute tool (normal flow)
        result = dispatcher.dispatch(name, arguments)

        # 3. AUTOMATIC: Enrich response with recommendations (runs in background, <20ms)
        if isinstance(result, dict):
            result = response_enricher.enrich_response(
                tool_name=name,
                result=result,
                intent_data=intent_data,
                context=session_context
            )

        # 4. AUTOMATIC: Log interaction for learning (async, non-blocking)
        _dur = (time.time() - _t0)
        learning_logger.log_interaction_async(
            tool_name=name,
            arguments=arguments,
            result=result,
            execution_time=_dur,
            intent=intent_data
        )

        # 5. Update session context
        session_context["tool_history"].append({
            "tool": name,
            "timestamp": time.time(),
            "success": result.get("success", False)
        })

        # Keep only last 10 tools
        if len(session_context["tool_history"]) > 10:
            session_context["tool_history"] = session_context["tool_history"][-10:]

        # ... rest of existing code (token limits, etc.) ...

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in {name}: {e}", exc_info=True)
        # ... existing error handling ...
```

### 4. Workflow Executor (Called by Claude, Not User)

Instead of user calling workflows, we expose ONE simple tool that Claude uses:

```python
# server/handlers/workflow_handler.py

def handle_execute_workflow_internal(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Internal workflow execution - called by CLAUDE, not user

    Claude calls this when user agrees to a workflow suggestion
    User never directly invokes this
    """
    workflow_id = args.get("workflow_id")
    parameters = args.get("parameters", {})

    # Get template
    template = WorkflowTemplates.get_template(workflow_id)
    if not template:
        return {"success": False, "error": f"Workflow not found: {workflow_id}"}

    # Instantiate and execute
    workflow = WorkflowTemplates.instantiate_template(template, parameters)

    # Execute with progress tracking
    # Progress updates are sent back to Claude via streaming if supported
    import asyncio
    result = asyncio.run(workflow_engine.execute_workflow(workflow))

    return result

# Register as internal tool (Claude sees it, user doesn't need to know about it)
registry.register(ToolDefinition(
    name="_execute_workflow",  # Underscore prefix = internal tool
    description="[INTERNAL] Execute a pre-defined workflow. Use when user agrees to a workflow suggestion from _intelligence.workflow_suggestion",
    handler=handle_execute_workflow_internal,
    input_schema={
        "type": "object",
        "properties": {
            "workflow_id": {
                "type": "string",
                "description": "Workflow ID from _intelligence.workflow_suggestion"
            },
            "parameters": {
                "type": "object",
                "description": "Parameters for the workflow"
            }
        },
        "required": ["workflow_id"]
    },
    category="internal",
    sort_order=9999  # At end of tool list
))
```

---

## How It Works in Practice

### Example 1: User Wants Model Review

**User:** "Can you review my Power BI model?"

**What happens:**

1. **Claude thinks:** "I should list tables first to start"
2. **Claude calls:** `02_list_tables`

3. **MCP Server automatically:**
   - Intent middleware detects: "user wants comprehensive review"
   - Response enricher adds workflow suggestion to result

4. **Claude receives:**
```json
{
  "success": true,
  "tables": [...],
  "_intelligence": {
    "workflow_suggestion": {
      "available": true,
      "workflow_id": "model_review_complete",
      "workflow_name": "Complete Model Review",
      "message_to_claude": "Suggest to the user: 'I can run the Complete Model Review workflow...'"
    }
  }
}
```

5. **Claude responds to user:**
   "I found 15 tables in your model. I can run a complete model review workflow that will automatically:
   - Run best practice analysis
   - Check all relationships
   - Generate documentation

   This takes about 5 minutes. Would you like me to proceed?"

6. **If user says yes:**
   - Claude calls `_execute_workflow` with workflow_id
   - Workflow executes automatically with progress
   - Claude streams progress updates to user

**User never had to know about workflows!**

### Example 2: User Creates a Measure

**User:** "Create a measure called Total Sales = SUM(Sales[Amount])"

**What happens:**

1. **Claude calls:** `04_upsert_measure` with the DAX

2. **MCP Server automatically:**
   - Intent middleware detects: "measure creation"
   - Response enricher adds next-step recommendations

3. **Claude receives:**
```json
{
  "success": true,
  "measure_created": "Total Sales",
  "_intelligence": {
    "next_steps": [
      {
        "suggestion": "Validate DAX and analyze context transitions",
        "tool": "03_dax_intelligence",
        "reason": "Best practice after creating a measure",
        "auto_params": {"expression": "[Total Sales]"}
      }
    ]
  }
}
```

4. **Claude proactively says:**
   "✅ Created measure 'Total Sales'. Let me validate the DAX for you..."

5. **Claude automatically calls:** `03_dax_intelligence`

6. **User gets:** Validated measure without having to ask!

### Example 3: User Asks Vague Question

**User:** "What's wrong with my model?"

**What happens:**

1. **Claude thinks:** "I should start by checking if we're connected"
2. **Claude calls:** `01_detect_pbi_instances`

3. **MCP Server automatically:**
   - Intent middleware detects: "troubleshooting/analysis intent"
   - Response enricher suggests comprehensive analysis

4. **Claude receives suggestion and responds:**
   "Let me run a comprehensive analysis to identify any issues..."

5. **Claude automatically executes workflow or calls:** `05_comprehensive_analysis`

6. **User gets:** Proactive analysis without having to know what tools to use!

---

## Simplified Tool List (User-Facing)

### Tools Users/Claude Actually Use:
- All existing tools (01-13 series) - no changes
- `_execute_workflow` - Internal tool Claude uses (user doesn't see)

### Tools Users DON'T Need:
- ~~20_execute_workflow~~ (Claude does this automatically)
- ~~20_list_workflow_templates~~ (Claude knows from _intelligence)
- ~~20_get_workflow_status~~ (Status embedded in responses)
- ~~20_cancel_workflow~~ (Not needed - workflows are fast)
- ~~21_analyze_intent~~ (Automatic middleware)
- ~~21_get_recommendations~~ (Automatic in responses)
- ~~21_get_learning_analytics~~ (Admin/debug only)

---

## Implementation Phases (Revised)

### Phase 1: Embedded Intelligence Middleware (Week 1-2)

**Goal:** Add automatic intelligence to all responses

**Tasks:**
1. Implement IntentMiddleware
2. Implement ResponseEnricher
3. Implement LearningLogger (background)
4. Modify main server to use middleware
5. Add _intelligence to response format

**Testing:**
- Every tool call should have _intelligence added
- Intent detection accuracy >80%
- Performance overhead <30ms per call

**Deliverables:**
- ✅ All tool responses automatically enriched
- ✅ Recommendations appear automatically
- ✅ Learning happens in background

### Phase 2: Workflow System (Week 3-4)

**Goal:** Add workflow execution capability

**Tasks:**
1. Implement WorkflowEngine
2. Create 3 workflow templates
3. Implement _execute_workflow internal tool
4. Add workflow suggestions to response enricher
5. Add progress tracking for long operations

**Testing:**
- Workflows execute successfully
- Progress updates work
- Claude can invoke workflows smoothly

**Deliverables:**
- ✅ Workflows executable via _execute_workflow
- ✅ Progress tracking embedded in responses
- ✅ 3 working workflow templates

### Phase 3: Refinement & Learning (Week 5-6)

**Goal:** Improve intelligence based on usage

**Tasks:**
1. Add analytics aggregation
2. Refine recommendation algorithms based on data
3. Improve intent detection accuracy
4. Add more workflow templates based on common patterns
5. Performance optimization

**Testing:**
- Learning system improves over time
- Recommendations become more accurate
- Analytics show usage patterns

**Deliverables:**
- ✅ Learning system improving recommendations
- ✅ 5-7 total workflow templates
- ✅ Analytics dashboard (admin only)

### Phase 4: Polish & Release (Week 7)

**Goal:** Production-ready release

**Tasks:**
1. Documentation for Claude/AI behavior
2. Performance optimization (<50ms overhead)
3. Error handling for edge cases
4. User acceptance testing

**Deliverables:**
- ✅ Production-ready system
- ✅ Documentation complete
- ✅ Performance targets met

**Total: 7 weeks** (1 week less - simpler architecture)

---

## Configuration

```json
// config/default_config.json

{
  "intelligence": {
    "enabled": true,
    "automatic_intent_analysis": true,
    "automatic_recommendations": true,
    "automatic_learning": true,
    "max_recommendations": 3,
    "workflow_suggestions_enabled": true,
    "performance": {
      "intent_analysis_timeout_ms": 10,
      "recommendation_timeout_ms": 20,
      "max_overhead_ms": 50
    }
  },

  "workflows": {
    "enabled": true,
    "progress_update_interval_seconds": 3,
    "max_workflow_duration_seconds": 600
  }
}
```

---

## Key Advantages of Embedded Approach

### ✅ Better User Experience
- User never has to learn about intelligence tools
- Everything "just works"
- Claude becomes more proactive and helpful
- No manual workflow management

### ✅ Simpler Architecture
- Fewer tools to maintain
- No workflow status/cancel tools needed
- Less complexity for users
- Intelligence is invisible but powerful

### ✅ Better Performance
- Middleware runs once per request
- No extra round trips
- Learning happens asynchronously
- Recommendations cached per session

### ✅ More Intelligent AI
- Claude gets rich context automatically
- Can make better decisions
- Proactive instead of reactive
- Learns user patterns silently

---

## Example Enhanced Response

```json
{
  "success": true,
  "tables": [
    {"name": "Sales", "rows": 1000000},
    {"name": "Products", "rows": 500},
    // ... more tables
  ],
  "count": 15,

  // AUTOMATICALLY ADDED - Claude sees this and acts on it:
  "_intelligence": {
    "detected_intent": {
      "category": "exploration",
      "confidence": 0.92,
      "entities": {"action": "model_review"}
    },
    "next_steps": [
      {
        "suggestion": "Run comprehensive best practice analysis",
        "tool": "05_comprehensive_analysis",
        "reason": "Standard next step after viewing model structure",
        "priority": "high",
        "auto_params": {"scope": "all", "depth": "balanced"}
      },
      {
        "suggestion": "Analyze table relationships",
        "tool": "03_list_relationships",
        "reason": "Understand how tables connect",
        "priority": "medium"
      }
    ],
    "workflow_suggestion": {
      "available": true,
      "workflow_id": "model_review_complete",
      "workflow_name": "Complete Model Review",
      "description": "Comprehensive analysis including BPA, relationships, and documentation",
      "estimated_duration": "5 minutes",
      "steps": [
        "List tables",
        "Run BPA analysis",
        "Analyze relationships",
        "List measures",
        "Export documentation"
      ],
      "message_to_claude": "I can run a complete model review workflow automatically. This will analyze your model comprehensively and generate documentation. Would you like me to proceed?"
    }
  },

  // Standard metadata
  "_limits_info": {
    "token_usage": {...}
  }
}
```

**Claude sees this and automatically suggests the workflow to the user!**

---

## Summary of Changes from Original Plan

### ❌ Removed (User-Facing Tools)
- `20_execute_workflow` → Now automatic via Claude
- `20_list_workflow_templates` → Embedded in suggestions
- `20_get_workflow_status` → Embedded in progress
- `20_cancel_workflow` → Not needed
- `21_analyze_intent` → Automatic middleware
- `21_get_recommendations` → Automatic in responses
- `21_get_learning_analytics` → Admin debug only

### ✅ Added (Invisible Components)
- IntentMiddleware (automatic)
- ResponseEnricher (automatic)
- LearningLogger (background)
- `_execute_workflow` (internal tool for Claude)
- `_intelligence` metadata in all responses
- Session context tracking

### 📊 Impact
- **User complexity:** Reduced by 90%
- **Intelligence power:** Increased (always active)
- **Development time:** Reduced to 7 weeks
- **Maintenance:** Simpler (fewer tools)
- **User experience:** Dramatically better

---

## Next Steps

1. ✅ Review revised approach
2. Create middleware components
3. Modify main server for embedded intelligence
4. Test with sample interactions
5. Roll out incrementally

**Ready to build invisible, embedded intelligence!** 🚀
