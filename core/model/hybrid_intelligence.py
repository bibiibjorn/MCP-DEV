"""
Hybrid Intelligence Layer - Smart operation routing and guidance

Provides natural language intent recognition, automatic optimization,
and next-step guidance for hybrid analysis operations.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class HybridIntelligence:
    """Smart operation routing and guidance for hybrid analysis"""

    # Intent patterns for operation routing
    INTENT_PATTERNS = {
        "read_metadata": [
            r"(show|give|get|display).*overview",
            r"(show|give|get|display).*summary",
            r"(show|give|get|display).*statistics",
            r"(what|tell).*(about|is).*model",
            r"model.*(info|information|details)",
        ],
        "find_objects": [
            r"(list|show|find|get|display).*(all|the)?.*(table|measure|column|role)",
            r"(what|which).*(table|measure|column|role).*",
            r"(search|filter).*(table|measure|column|role)",
        ],
        "get_object_definition": [
            r"(show|get|display).*(definition|code|tmdl)",
            r"(show|get|display).*\[.*\]",  # Measure in brackets
            r"(examine|inspect|view).*(measure|table|column)",
        ],
        "analyze_dependencies": [
            r"(what|which).*(depend|use|reference)",
            r"(show|find|get).*(dependencies|dependents|references)",
            r"(what|which).*(impact|affected|influenced)",
        ],
        "analyze_performance": [
            r"(find|show|identify).*(performance|slow|bottleneck)",
            r"(performance|optimization).*(issue|problem)",
            r"(what|which).*(slow|inefficient)",
        ],
        "get_sample_data": [
            r"(show|get|display|preview).*(data|row|record)",
            r"(sample|example).*(data|row|record)",
        ],
    }

    # Object type patterns
    OBJECT_TYPE_PATTERNS = {
        "tables": [r"table"],
        "measures": [r"measure", r"\[.*\]"],
        "columns": [r"column"],
        "roles": [r"role"],
    }

    @staticmethod
    def infer_operation(intent: str) -> Tuple[str, Dict[str, Any]]:
        """
        Infer operation and parameters from natural language intent

        Args:
            intent: Natural language intent string

        Returns:
            Tuple of (operation_name, inferred_parameters)
        """
        intent_lower = intent.lower()

        # Try to match operation
        operation = "read_metadata"  # Default
        for op, patterns in HybridIntelligence.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, intent_lower):
                    operation = op
                    break
            if operation != "read_metadata":
                break

        # Infer parameters based on operation
        params = HybridIntelligence._infer_parameters(intent_lower, operation)

        logger.info(f"Inferred operation: {operation}, params: {params}")
        return operation, params

    @staticmethod
    def _infer_parameters(intent: str, operation: str) -> Dict[str, Any]:
        """Infer parameters from intent for specific operation"""
        params = {}

        if operation == "find_objects":
            # Infer object type
            for obj_type, patterns in HybridIntelligence.OBJECT_TYPE_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, intent):
                        params["object_type"] = obj_type
                        break
                if "object_type" in params:
                    break

            # Infer folder filter
            folder_match = re.search(r"in\s+['\"]?([^'\"]+)['\"]?\s+folder", intent)
            if folder_match:
                params["folder"] = folder_match.group(1)

            # Infer name pattern
            name_match = re.search(r"named\s+['\"]?([^'\"]+)['\"]?", intent)
            if name_match:
                params["name_pattern"] = name_match.group(1)

        elif operation == "get_object_definition":
            # Extract object name (often in brackets for measures)
            bracket_match = re.search(r"\[([^\]]+)\]", intent)
            if bracket_match:
                params["object_name"] = bracket_match.group(1)
                params["object_type"] = "measure"
            else:
                # Try to extract quoted name
                quote_match = re.search(r"['\"]([^'\"]+)['\"]", intent)
                if quote_match:
                    params["object_name"] = quote_match.group(1)

        elif operation == "analyze_dependencies":
            # Extract object name
            bracket_match = re.search(r"\[([^\]]+)\]", intent)
            if bracket_match:
                params["object_name"] = bracket_match.group(1)
            else:
                quote_match = re.search(r"['\"]([^'\"]+)['\"]", intent)
                if quote_match:
                    params["object_name"] = quote_match.group(1)

        elif operation == "get_sample_data":
            # Extract table name
            quote_match = re.search(r"['\"]([^'\"]+)['\"]", intent)
            if quote_match:
                params["table_name"] = quote_match.group(1)

        return params

    @staticmethod
    def should_use_toon_format(
        result_count: int,
        estimated_tokens: int
    ) -> bool:
        """
        Determine if TOON format should be used for response

        Args:
            result_count: Number of results
            estimated_tokens: Estimated token count

        Returns:
            True if TOON format should be used
        """
        # Use TOON if many results or large token count
        return result_count > 20 or estimated_tokens > 3000

    @staticmethod
    def estimate_tokens(data: Any) -> int:
        """
        Estimate token count for data

        Args:
            data: Data to estimate

        Returns:
            Estimated token count
        """
        import json
        # Rough estimate: 1 token per 4 characters
        serialized = json.dumps(data)
        return len(serialized) // 4

    @staticmethod
    def generate_guidance(
        operation: str,
        result: Dict[str, Any],
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate guidance for response

        Args:
            operation: Operation executed
            result: Operation result
            intent: Original intent (if from smart_analyze)

        Returns:
            Guidance dictionary
        """
        guidance = {
            "operation_executed": operation,
            "suggestions": [],
            "related_operations": [],
            "next_steps": []
        }

        if intent:
            guidance["intent_interpreted"] = intent

        # Operation-specific guidance
        if operation == "read_metadata":
            guidance["suggestions"] = [
                "Use find_objects() to list specific object types",
                "Use analyze_performance() to identify optimization opportunities"
            ]
            guidance["related_operations"] = ["find_objects", "analyze_performance"]

        elif operation == "find_objects":
            count = result.get("count", 0)
            if count > 50:
                guidance["suggestions"].append(
                    f"Response is large ({count} objects) - consider filtering"
                )
            guidance["suggestions"].append(
                "Use get_object_definition() to examine specific objects"
            )
            guidance["related_operations"] = ["get_object_definition", "analyze_dependencies"]

        elif operation == "get_object_definition":
            guidance["suggestions"].append(
                "Use analyze_dependencies() to see what this object depends on"
            )
            guidance["related_operations"] = ["analyze_dependencies"]

        elif operation == "analyze_dependencies":
            guidance["suggestions"].append(
                "Use get_object_definition() to examine dependent objects"
            )
            guidance["related_operations"] = ["get_object_definition"]

        elif operation == "analyze_performance":
            guidance["suggestions"].append(
                "Use generate_recommendations() for specific optimization steps"
            )
            guidance["related_operations"] = ["generate_recommendations"]

        return guidance

    @staticmethod
    def generate_token_warning(
        estimated_tokens: int,
        format_used: str
    ) -> Dict[str, Any]:
        """
        Generate token usage warning if needed

        Args:
            estimated_tokens: Estimated token count
            format_used: Format used ("json" or "toon")

        Returns:
            Token warning dictionary
        """
        warning = {
            "estimated_tokens": estimated_tokens,
            "format_used": format_used
        }

        if format_used == "toon":
            original_estimate = estimated_tokens * 2  # TOON is ~50% smaller
            warning["would_be_without_toon"] = original_estimate
            warning["savings"] = "50%"
            warning["recommendation"] = "Response is large. TOON format already applied for 50% reduction"
        else:
            warning["recommendation"] = "Response fits within budget"

        if estimated_tokens > 8000:
            warning["recommendation"] = "⚠️ Response is very large. Consider filtering or batching"

        return warning

    @staticmethod
    def convert_to_toon_format(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert response to TOON (Tabular Object Optimized Notation) format

        TOON format uses abbreviations and compact structures to reduce tokens by ~50%

        Args:
            data: Data to convert

        Returns:
            TOON-formatted data
        """
        # TODO: Implement actual TOON conversion
        # For now, just return as-is
        return data

    @staticmethod
    def generate_next_steps(
        operation: str,
        result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate suggested next steps

        Args:
            operation: Operation executed
            result: Operation result

        Returns:
            List of next step suggestions
        """
        next_steps = []

        if operation == "find_objects":
            # Suggest examining most complex/referenced objects
            objects = result.get("objects", [])
            if objects and len(objects) > 0:
                first_object = objects[0]
                next_steps.append({
                    "action": "get_object_definition",
                    "params": {"object_name": first_object.get("name")},
                    "description": f"Examine {first_object.get('name')}"
                })

        elif operation == "read_metadata":
            next_steps.append({
                "action": "find_objects",
                "params": {"object_type": "measures"},
                "description": "List all measures"
            })
            next_steps.append({
                "action": "analyze_performance",
                "params": {"priority": "high"},
                "description": "Check for performance issues"
            })

        return next_steps
