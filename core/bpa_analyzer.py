"""
Best Practice Analyzer for Semantic Models
Analyzes TMSL models against a comprehensive set of best practice rules
"""

import json
import re
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import IntEnum
import logging

logger = logging.getLogger(__name__)

class BPASeverity(IntEnum):
    """BPA Rule Severity Levels"""
    INFO = 1
    WARNING = 2
    ERROR = 3

@dataclass
class BPAViolation:
    """Represents a Best Practice Analyzer rule violation"""
    rule_id: str
    rule_name: str
    category: str
    severity: BPASeverity
    description: str
    object_type: str
    object_name: str
    table_name: Optional[str] = None
    fix_expression: Optional[str] = None
    details: Optional[str] = None

@dataclass
class BPARule:
    """Represents a Best Practice Analyzer rule"""
    id: str
    name: str
    category: str
    description: str
    severity: BPASeverity
    scope: List[str]
    expression: str
    fix_expression: Optional[str] = None
    compatibility_level: int = 1200

class BPAAnalyzer:
    """
    Best Practice Analyzer for Semantic Models
    Analyzes TMSL models against best practice rules
    """
    
    def __init__(self, rules_file_path: Optional[str] = None):
        """
        Initialize the BPA Analyzer
        
        Args:
            rules_file_path: Path to the BPA rules JSON file
        """
        self.rules: List[BPARule] = []
        self.violations: List[BPAViolation] = []
        self._eval_depth = 0  # Track recursion depth
        self._max_depth = 50  # Prevent stack overflow
        
        if rules_file_path:
            self.load_rules(rules_file_path)
    
    def load_rules(self, rules_file_path: str) -> None:
        """Load BPA rules from JSON file"""
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            self.rules = []
            for rule_data in rules_data.get('rules', []):
                rule = BPARule(
                    id=rule_data.get('ID', ''),
                    name=rule_data.get('Name', ''),
                    category=rule_data.get('Category', ''),
                    description=rule_data.get('Description', ''),
                    severity=BPASeverity(rule_data.get('Severity', 1)),
                    scope=rule_data.get('Scope', '').split(', '),
                    expression=rule_data.get('Expression', ''),
                    fix_expression=rule_data.get('FixExpression'),
                    compatibility_level=rule_data.get('CompatibilityLevel', 1200)
                )
                self.rules.append(rule)
                
            logger.info(f"Loaded {len(self.rules)} BPA rules")
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading BPA rules: {str(e)}")
            raise

    def validate_rules_file(self, rules_file_path: str) -> bool:
        """Validate BPA rules file schema"""
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            for rule in rules_data.get('rules', []):
                required = ['ID', 'Name', 'Category', 'Description', 'Severity', 'Scope', 'Expression']
                for key in required:
                    if key not in rule:
                        logger.error(f"Missing key {key} in rule {rule.get('ID')}")
                        return False
            return True
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return False

    def evaluate_expression(self, expression: str, context: Dict) -> Union[bool, int, float, str]:
        """Recursive evaluator for rule expressions with depth protection"""
        # Depth check to prevent stack overflow
        self._eval_depth += 1
        if self._eval_depth > self._max_depth:
            self._eval_depth -= 1
            logger.warning(f"Max evaluation depth reached for expression: {expression[:50]}")
            return False
        
        try:
            # Safety checks
            if not expression or not isinstance(expression, str):
                return False
            
            expression = re.sub(r'\s+', ' ', expression).strip()

            # Handle parentheses first (recursive)
            paren_count = 0
            while paren_count < 10:  # Limit iterations
                match = re.search(r'\(([^()]*)\)', expression)
                if not match:
                    break
                inner = match.group(1)
                inner_result = self.evaluate_expression(inner, context)
                expression = expression.replace(match.group(0), str(inner_result), 1)
                paren_count += 1

            # Handle logical OR
            if ' or ' in expression or ' || ' in expression:
                delimiter = ' or ' if ' or ' in expression else ' || '
                parts = expression.split(delimiter)
                result = any(self.evaluate_expression(p.strip(), context) for p in parts)
                self._eval_depth -= 1
                return result

            # Handle logical AND
            if ' and ' in expression or ' && ' in expression:
                delimiter = ' and ' if ' and ' in expression else ' && '
                parts = expression.split(delimiter)
                result = all(self.evaluate_expression(p.strip(), context) for p in parts)
                self._eval_depth -= 1
                return result

            # Handle NOT
            if expression.startswith('not ') or expression.startswith('!'):
                result = not self.evaluate_expression(expression.lstrip('not !').strip(), context)
                self._eval_depth -= 1
                return result

            # Handle .Any(condition)
            any_match = re.match(r'([A-Za-z0-9_.]+)\.Any\((.*)\)', expression)
            if any_match:
                collection_path = any_match.group(1)
                inner_expr = any_match.group(2)
                collection = self._get_by_path(context, collection_path)
                if not isinstance(collection, list):
                    self._eval_depth -= 1
                    return False
                for item in collection:
                    item_context = {**context, 'it': item, 'current': item}
                    if self.evaluate_expression(inner_expr, item_context):
                        self._eval_depth -= 1
                        return True
                self._eval_depth -= 1
                return False

            # Handle .Count() or .Count
            count_match = re.match(r'([A-Za-z0-9_.]+)\.Count(\(\))?', expression)
            if count_match:
                collection_path = count_match.group(1)
                collection = self._get_by_path(context, collection_path)
                result = len(collection) if isinstance(collection, list) else 0
                self._eval_depth -= 1
                return result

            # Handle .Where(condition).Count()
            where_count_match = re.match(r'([A-Za-z0-9_.]+)\.Where\((.*)\)\.Count\(\)', expression)
            if where_count_match:
                collection_path = where_count_match.group(1)
                inner_expr = where_count_match.group(2)
                collection = self._get_by_path(context, collection_path)
                if not isinstance(collection, list):
                    self._eval_depth -= 1
                    return 0
                filtered = []
                for item in collection:
                    if self.evaluate_expression(inner_expr, {**context, 'it': item, 'current': item}):
                        filtered.append(item)
                self._eval_depth -= 1
                return len(filtered)

            # Handle RegEx.IsMatch(field, pattern)
            regex_match = re.match(r'RegEx\.IsMatch\(([^,]+),\s*"([^"]+)"(,.*)?\)', expression)
            if regex_match:
                field = regex_match.group(1).strip()
                pattern = regex_match.group(2)
                value = self.evaluate_expression(field, context)
                flags = re.IGNORECASE if '(?i)' in pattern else 0
                pattern = pattern.replace('(?i)', '')
                try:
                    result = bool(re.search(pattern, str(value) if value else '', flags))
                    self._eval_depth -= 1
                    return result
                except re.error as e:
                    logger.warning(f"Regex error: {e} in pattern: {pattern}")
                    self._eval_depth -= 1
                    return False

            # Handle string.IsNullOrWhitespace(field)
            null_match = re.match(r'string\.IsNullOrWhite?[Ss]pace\((.+)\)', expression)
            if null_match:
                field = null_match.group(1)
                value = self.evaluate_expression(field, context)
                result = not str(value).strip() if value is not None else True
                self._eval_depth -= 1
                return result

            # Handle Name.ToUpper().Contains("str")
            contains_match = re.match(r'Name\.ToUpper\(\)\.Contains\("([^"]+)"\)', expression)
            if contains_match:
                substring = contains_match.group(1)
                name = context.get('obj', {}).get('name', '')
                result = substring.upper() in str(name).upper()
                self._eval_depth -= 1
                return result

            # Handle Convert.ToInt64(expr) op value
            convert_match = re.match(r'Convert\.ToInt64\((.+)\)\s*([><]=?|==|!=)\s*(\d+)', expression)
            if convert_match:
                inner = convert_match.group(1)
                operator = convert_match.group(2)
                value = int(convert_match.group(3))
                inner_val = self.evaluate_expression(inner, context)
                try:
                    int_val = int(inner_val) if inner_val else 0
                except (ValueError, TypeError):
                    int_val = 0
                
                if operator == '>':
                    result = int_val > value
                elif operator == '<':
                    result = int_val < value
                elif operator == '>=':
                    result = int_val >= value
                elif operator == '<=':
                    result = int_val <= value
                elif operator == '==':
                    result = int_val == value
                elif operator == '!=':
                    result = int_val != value
                else:
                    result = False
                self._eval_depth -= 1
                return result

            # Handle GetAnnotation("name")
            ann_match = re.match(r'GetAnnotation\("([^"]+)"\)', expression)
            if ann_match:
                ann_name = ann_match.group(1)
                result = self.get_annotation(context.get('obj', {}), ann_name)
                self._eval_depth -= 1
                return result if result is not None else ""

            # Handle simple property == value
            prop_match = re.match(r'([A-Za-z0-9_]+)\s*(==|<>|!=)\s*("([^"]+)"|null|true|false|\d+)', expression)
            if prop_match:
                prop = prop_match.group(1)
                operator = prop_match.group(2)
                value_str = prop_match.group(3).strip('"')
                if value_str == 'true':
                    value = True
                elif value_str == 'false':
                    value = False
                elif value_str == 'null':
                    value = None
                else:
                    value = value_str
                    
                prop_value = self.evaluate_expression(prop, context)
                if operator in ['<>', '!=']:
                    result = prop_value != value
                else:
                    result = prop_value == value
                self._eval_depth -= 1
                return result

            # Handle math expressions like (a + b) / Math.Max(c,d) > e
            math_match = re.match(r'\((.+)\)\s*/\s*Math\.Max\((.+),(\d+)\)\s*>\s*(\d+\.?\d*)', expression)
            if math_match:
                numerator_expr = math_match.group(1)
                max_expr = math_match.group(2)
                min_val = int(math_match.group(3))
                threshold = float(math_match.group(4))
                try:
                    numerator = float(self.evaluate_expression(numerator_expr, context) or 0)
                    max_val_result = float(self.evaluate_expression(max_expr, context) or 0)
                    max_val = max(max_val_result, min_val)
                    result = (numerator / max_val) > threshold if max_val > 0 else False
                except (ValueError, TypeError, ZeroDivisionError):
                    result = False
                self._eval_depth -= 1
                return result

            # Handle addition
            if '+' in expression:
                parts = expression.split('+')
                try:
                    result = sum(float(self.evaluate_expression(p.strip(), context) or 0) for p in parts if p.strip())
                except (ValueError, TypeError):
                    result = 0
                self._eval_depth -= 1
                return result

            # Handle property access
            if re.match(r'^[A-Za-z0-9_]+$', expression):
                result = self._get_by_path(context, expression)
                self._eval_depth -= 1
                return result

            # If unhandled, log and return False
            logger.debug(f"Unhandled expression: {expression[:100]}")
            self._eval_depth -= 1
            return False
            
        except Exception as e:
            logger.warning(f"Expression evaluation error: {e} for: {expression[:100]}")
            self._eval_depth -= 1
            return False

    def _get_by_path(self, context: Dict, path: str) -> Any:
        """Get value by dot path"""
        if not path:
            return None
            
        parts = path.split('.')
        
        # Start with appropriate root
        if parts[0] == 'Model':
            current = context.get('model', {})
        else:
            current = context.get(parts[0].lower(), context.get('table', context.get('obj', {})))
        
        # Navigate path
        for part in parts[1:]:
            if part == 'AllColumns':
                all_columns = []
                for t in context.get('model', {}).get('tables', []):
                    all_columns.extend(t.get('columns', []))
                current = all_columns
            elif part == 'AllMeasures':
                all_measures = []
                for t in context.get('model', {}).get('tables', []):
                    all_measures.extend(t.get('measures', []))
                current = all_measures
            elif part == 'AllCalculationItems':
                all_items = []
                for t in context.get('model', {}).get('tables', []):
                    if t.get('calculationGroup'):
                        all_items.extend(t['calculationGroup'].get('calculationItems', []))
                current = all_items
            elif part == 'RowLevelSecurity':
                current = context.get('table', {}).get('roles', [])
            else:
                if isinstance(current, dict):
                    current = current.get(part, current.get(part.lower(), None))
                else:
                    current = None
                    
        return current if current is not None else []

    def get_annotation(self, obj: Dict, name: str) -> Optional[str]:
        """Get annotation value from object"""
        if not obj or not isinstance(obj, dict):
            return None
        annotations = obj.get('annotations', [])
        for a in annotations:
            if isinstance(a, dict) and a.get('name') == name:
                return a.get('value')
        return None

    def check_required_annotations(self, model: Dict) -> List[str]:
        """Check for missing required annotations"""
        required = set()
        for rule in self.rules:
            if 'GetAnnotation' in rule.expression:
                matches = re.findall(r'GetAnnotation\("([^"]+)"\)', rule.expression)
                required.update(matches)
        
        missing = []
        for table in model.get('tables', []):
            for column in table.get('columns', []):
                annotations = {a.get('name') for a in column.get('annotations', []) if isinstance(a, dict)}
                for req in required:
                    if req not in annotations:
                        missing.append(f"{req} missing in {table.get('name', 'unknown')}.{column.get('name', 'unknown')}")
        return list(set(missing))[:10]  # Limit to first 10

    def analyze_model(self, tmsl_json: Union[str, Dict]) -> List[BPAViolation]:
        """Analyze model against BPA rules"""
        # Reset violations at the start of each analysis run
        self.violations = []

        if isinstance(tmsl_json, str):
            try:
                tmsl_model = json.loads(tmsl_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid TMSL JSON: {e}")
                return []
        else:
            tmsl_model = tmsl_json
            
        # Resolve model from common shapes:
        # - create.database.model
        # - { model: {...} }
        # - model object at root (has 'tables' etc.)
        model = (
            tmsl_model.get('create', {}).get('database', {}).get('model', {})
            or tmsl_model.get('model', {})
        )
        if not model and isinstance(tmsl_model, dict) and (
            'tables' in tmsl_model or 'measures' in tmsl_model or 'relationships' in tmsl_model
        ):
            model = tmsl_model
        
        if not model:
            logger.warning("No model found in TMSL structure")
            return []
        
        # Check for missing annotations
        missing_ann = self.check_required_annotations(model)
        if missing_ann:
            logger.warning(f"Missing annotations detected: {len(missing_ann)} items")
            self.violations.append(BPAViolation(
                rule_id="MISSING_ANNOTATIONS",
                rule_name="Missing required annotations",
                category="Error Prevention",
                severity=BPASeverity.WARNING,
                description="Some rules require Vertipaq annotations. Run the Vertipaq script to add them.",
                object_type="Model",
                object_name="Model",
                details=", ".join(missing_ann[:5])  # Show first 5
            ))

        for rule in self.rules:
            try:
                self._eval_depth = 0  # Reset depth counter for each rule
                self._analyze_rule(rule, model)
            except Exception as e:
                logger.error(f"Rule {rule.id} evaluation failed: {str(e)}")
                # Don't add error violations for failed rules - just skip them

        return self.violations

    def analyze_model_fast(self, tmsl_json: Union[str, Dict], cfg: Optional[Dict[str, Any]] = None) -> List[BPAViolation]:
        """Faster analysis with configurable sampling/filters.

        cfg keys (optional):
          - max_rules: int (limit number of rules evaluated)
          - severity_at_least: 'INFO'|'WARNING'|'ERROR' (filter rules below threshold)
          - include_categories: list[str] (only evaluate these categories)
          - max_tables: int (limit number of tables processed)
        """
        if isinstance(tmsl_json, str):
            try:
                tmsl_model = json.loads(tmsl_json)
            except json.JSONDecodeError:
                return []
        else:
            tmsl_model = tmsl_json

        model = (
            tmsl_model.get('create', {}).get('database', {}).get('model', {})
            or tmsl_model.get('model', {})
        )
        if not model and isinstance(tmsl_model, dict) and (
            'tables' in tmsl_model or 'measures' in tmsl_model or 'relationships' in tmsl_model
        ):
            model = tmsl_model
        if not model:
            return []

        cfg = cfg or {}
        # Prepare filtered rules list
        rules = list(self.rules)
        # severity filter
        sev = str(cfg.get('severity_at_least', '')).upper()
        level = {'INFO': 1, 'WARNING': 2, 'ERROR': 3}.get(sev)
        if level:
            rules = [r for r in rules if int(r.severity) >= level]
        # category filter
        cats = cfg.get('include_categories') or []
        if isinstance(cats, list) and cats:
            lc = set(str(c).lower() for c in cats)
            rules = [r for r in rules if str(r.category).lower() in lc]
        # limit number of rules
        try:
            mr_val = cfg.get('max_rules')
            mr = int(mr_val) if mr_val is not None and str(mr_val).strip() != '' else None
        except Exception:
            mr = None
        if mr and mr > 0 and len(rules) > mr:
            rules = rules[:mr]

        # Optionally limit number of tables (lightweight sampling)
        try:
            mt_val = cfg.get('max_tables')
            mt = int(mt_val) if mt_val is not None and str(mt_val).strip() != '' else None
        except Exception:
            mt = None
        if mt and mt > 0 and isinstance(model.get('tables'), list) and len(model['tables']) > mt:
            model = dict(model)
            model['tables'] = model['tables'][:mt]

        # Evaluate filtered/limited rule set
        self.violations = []
        for rule in rules:
            try:
                self._eval_depth = 0
                self._analyze_rule(rule, model)
            except Exception:
                pass
        return self.violations

    def get_violations_summary(self) -> Dict[str, int]:
        """Return a summary of violations by severity and category"""
        summary = {
            "total": len(self.violations),
            "by_severity": {"INFO": 0, "WARNING": 0, "ERROR": 0},
            "by_category": {}
        }
        for violation in self.violations:
            severity = BPASeverity(violation.severity).name
            summary["by_severity"][severity] += 1
            category = violation.category
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        return summary

    def _analyze_rule(self, rule: BPARule, model: Dict) -> None:
        """Analyze a single rule against the model"""
        if "Table" in rule.scope or "CalculatedTable" in rule.scope:
            self._check_table_rule(rule, model)
        if any(s in rule.scope for s in ["DataColumn", "CalculatedColumn", "CalculatedTableColumn"]):
            self._check_column_rule(rule, model, rule.scope)
        if "Measure" in rule.scope:
            self._check_measure_rule(rule, model)
        if "Model" in rule.scope:
            self._check_model_rule(rule, model)
        if "Hierarchy" in rule.scope:
            self._check_hierarchy_rule(rule, model)
        if "CalculationGroup" in rule.scope:
            self._check_calculation_group_rule(rule, model)
        if "Relationship" in rule.scope:
            self._check_relationship_rule(rule, model)
        if "Partition" in rule.scope:
            self._check_partition_rule(rule, model)

    def _check_table_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against tables"""
        tables = model.get('tables', [])
        for table in tables:
            is_calc = table.get('partitions', [{}])[0].get('source', {}).get('type') == 'calculated'
            if ("Table" in rule.scope and not is_calc) or ("CalculatedTable" in rule.scope and is_calc):
                context = {'obj': table, 'table': table, 'model': model, 'current': table, 'outerIt': table}
                try:
                    if self.evaluate_expression(rule.expression, context):
                        self.violations.append(BPAViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            description=rule.description,
                            object_type="CalculatedTable" if is_calc else "Table",
                            object_name=table.get('name', 'unknown')
                        ))
                except Exception as e:
                    logger.debug(f"Error checking table rule {rule.id}: {e}")

    def _check_column_rule(self, rule: BPARule, model: Dict, scope: List[str]) -> None:
        """Check rule against columns"""
        tables = model.get('tables', [])
        for table in tables:
            columns = table.get('columns', [])
            for column in columns:
                column_type = column.get('type', 'DataColumn')
                if column_type in scope or 'DataColumn' in scope:
                    context = {'obj': column, 'table': table, 'model': model, 'current': column, 'outerIt': column}
                    try:
                        if self.evaluate_expression(rule.expression, context):
                            self.violations.append(BPAViolation(
                                rule_id=rule.id,
                                rule_name=rule.name,
                                category=rule.category,
                                severity=rule.severity,
                                description=rule.description,
                                object_type=column_type,
                                object_name=column.get('name', 'unknown'),
                                table_name=table.get('name', 'unknown'),
                                fix_expression=rule.fix_expression
                            ))
                    except Exception as e:
                        logger.debug(f"Error checking column rule {rule.id}: {e}")

    def _check_measure_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against measures"""
        tables = model.get('tables', [])
        for table in tables:
            measures = table.get('measures', [])
            for measure in measures:
                context = {'obj': measure, 'table': table, 'model': model, 'current': measure, 'outerIt': measure}
                try:
                    if self.evaluate_expression(rule.expression, context):
                        self.violations.append(BPAViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            description=rule.description,
                            object_type="Measure",
                            object_name=measure.get('name', 'unknown'),
                            table_name=table.get('name', 'unknown'),
                            fix_expression=rule.fix_expression
                        ))
                except Exception as e:
                    logger.debug(f"Error checking measure rule {rule.id}: {e}")

    def _check_model_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against model"""
        context = {'obj': model, 'model': model, 'current': model, 'outerIt': model}
        try:
            if self.evaluate_expression(rule.expression, context):
                self.violations.append(BPAViolation(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    category=rule.category,
                    severity=rule.severity,
                    description=rule.description,
                    object_type="Model",
                    object_name="Model"
                ))
        except Exception as e:
            logger.debug(f"Error checking model rule {rule.id}: {e}")

    def _check_hierarchy_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against hierarchies"""
        tables = model.get('tables', [])
        for table in tables:
            hierarchies = table.get('hierarchies', [])
            for hierarchy in hierarchies:
                context = {'obj': hierarchy, 'table': table, 'model': model, 'current': hierarchy, 'outerIt': hierarchy}
                try:
                    if self.evaluate_expression(rule.expression, context):
                        self.violations.append(BPAViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            description=rule.description,
                            object_type="Hierarchy",
                            object_name=hierarchy.get('name', 'unknown'),
                            table_name=table.get('name', 'unknown')
                        ))
                except Exception as e:
                    logger.debug(f"Error checking hierarchy rule {rule.id}: {e}")

    def _check_calculation_group_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against calculation groups"""
        tables = model.get('tables', [])
        for table in tables:
            calc_group = table.get('calculationGroup', {})
            if calc_group:
                context = {'obj': calc_group, 'table': table, 'model': model, 'current': calc_group, 'outerIt': calc_group}
                try:
                    if self.evaluate_expression(rule.expression, context):
                        self.violations.append(BPAViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            description=rule.description,
                            object_type="CalculationGroup",
                            object_name=calc_group.get('name', 'unknown'),
                            table_name=table.get('name', 'unknown')
                        ))
                except Exception as e:
                    logger.debug(f"Error checking calc group rule {rule.id}: {e}")

    def _check_relationship_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against relationships"""
        relationships = model.get('relationships', [])
        for relationship in relationships:
            context = {'obj': relationship, 'model': model, 'current': relationship, 'outerIt': relationship}
            try:
                if self.evaluate_expression(rule.expression, context):
                    self.violations.append(BPAViolation(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        description=rule.description,
                        object_type="Relationship",
                        object_name=f"{relationship.get('fromTable', 'unknown')}.{relationship.get('fromColumn', 'unknown')}"
                    ))
            except Exception as e:
                logger.debug(f"Error checking relationship rule {rule.id}: {e}")

    def _check_partition_rule(self, rule: BPARule, model: Dict) -> None:
        """Check rule against partitions"""
        tables = model.get('tables', [])
        for table in tables:
            partitions = table.get('partitions', [])
            for partition in partitions:
                context = {'obj': partition, 'table': table, 'model': model, 'current': partition, 'outerIt': partition}
                try:
                    if self.evaluate_expression(rule.expression, context):
                        self.violations.append(BPAViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            category=rule.category,
                            severity=rule.severity,
                            description=rule.description,
                            object_type="Partition",
                            object_name=partition.get('name', 'unknown'),
                            table_name=table.get('name', 'unknown')
                        ))
                except Exception as e:
                    logger.debug(f"Error checking partition rule {rule.id}: {e}")