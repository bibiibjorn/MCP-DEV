"""
Screenshot Analyzer
Extracts theme, palette, grid hints, and component suggestions from dashboard screenshots.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from PIL import Image, ImageStat


@dataclass
class ScreenshotAnalysis:
    theme: str
    dimensions: Tuple[int, int]
    color_palette: List[str]
    semantic_colors: Dict[str, List[str]]
    grid_structure: Dict[str, Any]
    detected_components: Dict[str, int]
    recommended_max_width: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
            "color_palette": self.color_palette,
            "semantic_colors": self.semantic_colors,
            "grid_structure": self.grid_structure,
            "detected_components": self.detected_components,
            "recommended_max_width": self.recommended_max_width,
        }


class ScreenshotAnalyzer:
    def __init__(self, image_path: Path) -> None:
        self.image_path = image_path
        with Image.open(image_path) as img:
            self.image = img.convert("RGB")
        self.width, self.height = self.image.size
        self.pixels = np.asarray(self.image)

    # ------------------------------------------------------------------
    # Core analysis steps
    # ------------------------------------------------------------------
    def analyze(self) -> ScreenshotAnalysis:
        theme = self._detect_theme()
        palette = self._extract_palette()
        semantic = self._categorize_colors(palette)
        grid = self._detect_grid_structure()
        components = self._infer_components(grid, semantic)
        max_width = self._recommend_max_width()
        return ScreenshotAnalysis(theme, (self.width, self.height), palette, semantic, grid, components, max_width)

    # Theme detection ---------------------------------------------------
    def _detect_theme(self) -> str:
        stat = ImageStat.Stat(self.image.convert("L"))
        avg_brightness = stat.mean[0]
        if avg_brightness > 200:
            return "light"
        if avg_brightness < 90:
            return "dark"
        return "mixed"

    # Palette extraction ------------------------------------------------
    def _extract_palette(self, n_colors: int = 10) -> List[str]:
        pixels_2d = self.pixels.reshape(-1, 3)
        # Drop pure black or white noise
        mask = ~np.all(pixels_2d <= 10, axis=1) & ~np.all(pixels_2d >= 245, axis=1)
        filtered = pixels_2d[mask]
        if filtered.size == 0:
            filtered = pixels_2d
        # Quantize to reduce similar tones
        quantized = (filtered // 16) * 16
        unique, counts = np.unique(quantized, axis=0, return_counts=True)
        order = np.argsort(counts)[::-1]
        top_colors = unique[order][:n_colors]
        return [f"#{r:02x}{g:02x}{b:02x}" for r, g, b in top_colors]

    # Semantic color grouping ------------------------------------------
    def _categorize_colors(self, palette: List[str]) -> Dict[str, List[str]]:
        groups: Dict[str, List[str]] = {
            "background": [],
            "text": [],
            "primary": [],
            "success": [],
            "danger": [],
            "warning": [],
            "neutral": [],
        }
        for hex_color in palette:
            r = int(hex_color[1:3], 16) / 255
            g = int(hex_color[3:5], 16) / 255
            b = int(hex_color[5:7], 16) / 255
            max_val, min_val = max(r, g, b), min(r, g, b)
            chroma = max_val - min_val
            brightness = (max_val + min_val) / 2
            if brightness > 0.8 and chroma < 0.15:
                groups["background"].append(hex_color)
            elif brightness < 0.25:
                groups["text"].append(hex_color)
            elif chroma < 0.1:
                groups["neutral"].append(hex_color)
            else:
                hue = self._rgb_to_hue(r, g, b)
                if 100 <= hue <= 170:
                    groups["success"].append(hex_color)
                elif hue >= 330 or hue <= 20:
                    groups["danger"].append(hex_color)
                elif 20 < hue <= 60:
                    groups["warning"].append(hex_color)
                else:
                    groups["primary"].append(hex_color)
        return groups

    @staticmethod
    def _rgb_to_hue(r: float, g: float, b: float) -> float:
        max_val, min_val = max(r, g, b), min(r, g, b)
        chroma = max_val - min_val
        if chroma == 0:
            return 0.0
        if max_val == r:
            hue = ((g - b) / chroma) % 6
        elif max_val == g:
            hue = ((b - r) / chroma) + 2
        else:
            hue = ((r - g) / chroma) + 4
        return hue * 60

    # Grid detection ----------------------------------------------------
    def _detect_grid_structure(self) -> Dict[str, Any]:
        gray = np.mean(self.pixels, axis=2)
        horizontal_edges = np.abs(np.diff(gray, axis=0))
        vertical_edges = np.abs(np.diff(gray, axis=1))

        h_threshold = np.percentile(horizontal_edges, 95)
        v_threshold = np.percentile(vertical_edges, 95)

        h_gaps = np.where(horizontal_edges.mean(axis=1) > h_threshold)[0]
        v_gaps = np.where(vertical_edges.mean(axis=0) > v_threshold)[0]

        h_spacing = np.diff(h_gaps) if h_gaps.size > 1 else np.array([])
        v_spacing = np.diff(v_gaps) if v_gaps.size > 1 else np.array([])

        return {
            "horizontal_divisions": int(h_gaps.size),
            "vertical_divisions": int(v_gaps.size),
            "avg_h_spacing": float(h_spacing.mean()) if h_spacing.size else 0.0,
            "avg_v_spacing": float(v_spacing.mean()) if v_spacing.size else 0.0,
            "grid_estimate": self._estimate_columns(v_spacing),
        }

    @staticmethod
    def _estimate_columns(v_spacing: np.ndarray) -> int:
        if v_spacing.size == 0:
            return 1
        # Stabilise by rounding to the nearest 10 pixels
        rounded = (v_spacing // 10) * 10
        values, counts = np.unique(rounded, return_counts=True)
        dominant = values[np.argmax(counts)]
        columns = int(round(1080 / max(dominant, 1)))
        return max(min(columns, 12), 1)

    # Component inference -----------------------------------------------
    def _infer_components(self, grid_info: Dict[str, Any], semantic_colors: Dict[str, List[str]]) -> Dict[str, int]:
        detected = {
            "kpi_cards": 0,
            "tables": 0,
            "charts": 0,
            "sidebars": 0,
        }

        # Sidebar heuristic: detect dark strip in left 18% width
        left_slice = self.pixels[:, : max(int(self.width * 0.18), 1), :]
        right_slice = self.pixels[:, int(self.width * 0.18) :, :]
        left_brightness = np.mean(left_slice)
        right_brightness = np.mean(right_slice) if right_slice.size else left_brightness
        if left_brightness + 30 < right_brightness:
            detected["sidebars"] = 1

        # KPI heuristic: strong horizontal divisions near top
        if grid_info["horizontal_divisions"] >= 3:
            detected["kpi_cards"] = min(4, grid_info["horizontal_divisions"])
        elif grid_info["grid_estimate"] >= 3:
            detected["kpi_cards"] = 3

        # Chart heuristic: presence of vibrant colors and rounded bars
        if len(semantic_colors.get("primary", [])) >= 2:
            detected["charts"] = max(1, grid_info["grid_estimate"] // 2)

        # Table heuristic: neutral palette with repeated lines
        neutral_count = len(semantic_colors.get("neutral", []))
        background_count = len(semantic_colors.get("background", []))
        if neutral_count >= 2 and background_count >= 1:
            detected["tables"] = max(1, grid_info["horizontal_divisions"] // 2)

        return detected

    # Layout recommendation ---------------------------------------------
    def _recommend_max_width(self) -> str:
        if self.width >= 3440:
            return "2400px"
        if self.width >= 2560:
            return "1800px"
        if self.width >= 1920:
            return "1400px"
        if self.width >= 1440:
            return "1200px"
        return "1000px"

    # ------------------------------------------------------------------
    # Component suggestions
    # ------------------------------------------------------------------
    def suggest_components(self, metadata_path: Path) -> List[str]:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        catalog = {comp["id"]: comp for comp in metadata.get("components", [])}
        analysis = self.analyze()
        suggestions: List[str] = []

        if analysis.detected_components["sidebars"]:
            suggestions.append("nav_dark_sidebar")

        if analysis.detected_components["kpi_cards"] >= 3:
            suggestions.append("kpi_standard")
            suggestions.append("layout_kpi_strip")

        if analysis.detected_components["tables"]:
            suggestions.append("table_kpi_matrix")

        if analysis.detected_components["charts"]:
            suggestions.append("chart_column_combo")

        # Ensure suggestions exist in catalog and keep unique order
        unique: List[str] = []
        for comp_id in suggestions:
            if comp_id in catalog and comp_id not in unique:
                unique.append(comp_id)
        return unique


def analyze_screenshot(image_path: Path, metadata_path: Path) -> Dict[str, Any]:
    analyzer = ScreenshotAnalyzer(image_path)
    analysis = analyzer.analyze().to_dict()
    analysis["suggested_components"] = analyzer.suggest_components(metadata_path)
    analysis["source_image"] = str(image_path)
    return analysis


def analyze_folder(folder: Path, metadata_path: Path) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for image_path in sorted(folder.glob("*.png")) + sorted(folder.glob("*.jpg")) + sorted(folder.glob("*.jpeg")):
        results.append(analyze_screenshot(image_path, metadata_path))
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze mockup screenshots.")
    parser.add_argument("path", type=Path, help="Image file or folder containing screenshots.")
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("docs/component_metadata.json"),
        help="Path to component_metadata.json for component suggestions.",
    )
    args = parser.parse_args()

    if args.path.is_dir():
        analyses = analyze_folder(args.path, args.metadata)
        print(json.dumps(analyses, indent=2))
    else:
        result = analyze_screenshot(args.path, args.metadata)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
