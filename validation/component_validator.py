"""
Component Validator
Validates generated HTML mockups against the Power BI component library metadata.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from bs4 import BeautifulSoup, Tag


@dataclass
class ValidationResult:
    violations: List[str]
    warnings: List[str]
    score: int


class ComponentValidator:
    """Validates mockup HTML against metadata driven guardrails."""

    def __init__(self, html_content: str, component_metadata_path: Path) -> None:
        self.html = html_content
        self.soup = BeautifulSoup(html_content, "html.parser")
        metadata_raw = json.loads(component_metadata_path.read_text(encoding="utf-8"))
        # Flatten metadata by id for easy lookup
        self.metadata_by_id: Dict[str, Dict[str, Any]] = {
            comp["id"]: comp for comp in metadata_raw.get("components", [])
        }
        self.component_groups = metadata_raw.get("component_groups", [])
        self.icon_library = metadata_raw.get("icon_library", "lucide")
        self.violations: List[str] = []
        self.warnings: List[str] = []
        self.component_nodes: Dict[str, List[Tag]] = self._index_components()

    def _index_components(self) -> Dict[str, List[Tag]]:
        index: Dict[str, List[Tag]] = {}
        for element in self.soup.find_all(attrs={"data-component": True}):
            comp_id = str(element.get("data-component", "")).strip()
            if not comp_id:
                continue
            index.setdefault(comp_id, []).append(element)
        return index

    # ------------------------------------------------------------------
    # Primary validation routines
    # ------------------------------------------------------------------
    def validate_all(self) -> ValidationResult:
        self.validate_component_ids()
        self.validate_theme()
        self.validate_icons()
        self.validate_spacing()
        self.validate_kpi_cards()
        self.validate_charts()
        self.validate_accessibility()
        self.validate_css_tokens()
        score = self._calculate_score()
        return ValidationResult(self.violations, self.warnings, score)

    def validate_component_ids(self) -> None:
        """Ensure every declared component maps to metadata."""
        for comp_id in self.component_nodes:
            if comp_id not in self.metadata_by_id:
                self.violations.append(
                    f"Unknown component id '{comp_id}' (no entry in component_metadata.json)."
                )

    def validate_css_tokens(self) -> None:
        """Surface soft alerts when recommended tokens are missing."""
        for comp_id, nodes in self.component_nodes.items():
            meta = self.metadata_by_id.get(comp_id)
            if not meta:
                continue
            expected_tokens: Iterable[str] = meta.get("css_tokens", [])
            if not expected_tokens:
                continue
            for token in expected_tokens:
                if not any(self._element_has_token(node, token) for node in nodes):
                    self.warnings.append(
                        f"Component '{comp_id}' missing recommended CSS token '{token}'."
                    )

    def validate_theme(self) -> None:
        """Confirm the base template enforces the dark theme requirements."""
        base_css_link = self.soup.find("link", href=re.compile(r"dashboard_base\.css"))
        if not base_css_link and "color-scheme: dark" not in self.html and "color-scheme:dark" not in self.html:
            self.warnings.append(
                "Theme does not declare 'color-scheme: dark'; inherit from dashboard_base.css."
            )
        if not base_css_link and "--surface-0" not in self.html and "--surface-0" not in self._collect_styles():
            self.warnings.append(
                "Surface tokens (--surface-*) not found; ensure dashboard_base.css is applied."
            )

    def validate_icons(self) -> None:
        """Verify icon library is loaded and placeholders are not present."""
        text_content = self.soup.get_text(separator=" ").lower()
        placeholder_patterns = [
            r"\[icon\]",
            r"\{icon\}",
            r"icon-placeholder",
            r"replace-icon",
        ]
        for pattern in placeholder_patterns:
            if re.search(pattern, text_content):
                self.violations.append(
                    "Placeholder icon marker detected; replace with a Lucide icon."
                )

        if self.icon_library.lower() == "lucide":
            lucide_script = self.soup.find("script", src=re.compile(r"lucide", re.IGNORECASE))
            lucide_icons = self.soup.find_all(attrs={"data-lucide": True})
            if lucide_icons and lucide_script is None:
                self.violations.append(
                    "Lucide icons referenced via data-lucide but lucide script tag missing."
                )

    def validate_spacing(self) -> None:
        """Ensure spacing values stay on the established 4px grid (8px preferred)."""
        styles = self._collect_styles()
        spacing_pattern = re.compile(r"(padding|margin|gap)\s*:\s*([0-9]+)px", re.IGNORECASE)
        for prop, value in spacing_pattern.findall(styles):
            pixel = int(value)
            if pixel == 0:
                continue
            if pixel % 4 != 0:
                self.warnings.append(
                    f"{prop} uses {pixel}px; align spacing to the 4px grid (ideally multiples of 8)."
                )

    def validate_kpi_cards(self) -> None:
        """Check KPI cards include core elements like meta labels and value text."""
        for comp_id, nodes in self._iter_category("kpi_cards"):
            meta_labels_missing = 0
            for node in nodes:
                if not node.find(class_="meta-label"):
                    meta_labels_missing += 1
                if not re.search(r"\d", node.get_text()):
                    self.warnings.append(
                        f"KPI card '{comp_id}' contains no numeric metric; confirm data binding."
                    )
            if meta_labels_missing:
                self.violations.append(
                    f"{meta_labels_missing} instance(s) of '{comp_id}' missing .meta-label element."
                )

    def validate_charts(self) -> None:
        """Require accessible labelling for chart components."""
        for comp_id, nodes in self._iter_category("chart_visuals"):
            for node in nodes:
                has_aria = bool(node.find(attrs={"aria-label": True}))
                has_role_img = bool(node.find(attrs={"role": "img"}))
                if not (has_aria or has_role_img):
                    self.violations.append(
                        f"Chart component '{comp_id}' missing aria-label or role='img' for assistive tech."
                    )

    def validate_accessibility(self) -> None:
        """General accessibility checks across the document."""
        for button in self.soup.find_all("button"):
            if not button.get("aria-label") and not button.get_text(strip=True):
                self.warnings.append("Button detected without text or aria-label.")
        if not self.soup.find("main"):
            self.warnings.append("No <main> element present; include semantic layout landmarks.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _collect_styles(self) -> str:
        collected: List[str] = []
        for style_tag in self.soup.find_all("style"):
            if style_tag.string:
                collected.append(style_tag.string)
        return " ".join(collected)

    def _iter_category(self, category_id: str) -> Iterable[Tuple[str, List[Tag]]]:
        for comp_id, nodes in self.component_nodes.items():
            meta = self.metadata_by_id.get(comp_id)
            if meta and meta.get("category") == category_id:
                yield comp_id, nodes

    @staticmethod
    def _element_has_token(node: Tag, token: str) -> bool:
        class_list = node.get("class") or []
        if token in class_list:
            return True
        # Search descendants
        return bool(node.find(class_=token))

    def _calculate_score(self) -> int:
        deductions = len(self.violations) * 12 + len(self.warnings) * 4
        return max(100 - deductions, 10)


def run_validator(html_path: Path, metadata_path: Path) -> ValidationResult:
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    validator = ComponentValidator(html_path.read_text(encoding="utf-8"), metadata_path)
    return validator.validate_all()


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate dashboard HTML against the component library.")
    parser.add_argument("html", type=Path, help="Path to the generated HTML mockup.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("docs/component_metadata.json"),
        help="Path to component_metadata.json.",
    )
    args = parser.parse_args()

    result = run_validator(args.html, args.metadata)
    print(f"Validation Score: {result.score}/100")
    print(f"\nViolations ({len(result.violations)}):")
    for item in result.violations:
        print(f"  - {item}")
    print(f"\nWarnings ({len(result.warnings)}):")
    for item in result.warnings:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
