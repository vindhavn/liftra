"""
Chart types and configurations for Liftra visualizations.
"""

from enum import Enum
from typing import Any


class ChartType(str, Enum):
    """Types of charts available in Liftra."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    STACKED_BAR = "stacked_bar"
    STACKED_LINE = "stacked_line"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    GAUGE = "gauge"


# Chart configurations
CHART_CONFIG = {
    ChartType.LINE: {
        "name": "Line Chart",
        "description": "Trends over time (spending, balances, etc.)",
        "supports_3d": False,
        "supports_stacking": False,
        "best_for": ["time_series", "trends"],
    },
    ChartType.BAR: {
        "name": "Bar Chart",
        "description": "Comparisons (spending by category, etc.)",
        "supports_3d": True,
        "supports_stacking": False,
        "best_for": ["comparisons", "categorical_data"],
    },
    ChartType.PIE: {
        "name": "Pie Chart",
        "description": "Proportions (budget allocation, etc.)",
        "supports_3d": True,
        "supports_stacking": False,
        "best_for": ["proportions", "percentages"],
    },
    ChartType.STACKED_BAR: {
        "name": "Stacked Bar Chart",
        "description": "Cumulative data across categories",
        "supports_3d": True,
        "supports_stacking": True,
        "best_for": ["cumulative_data", "composition"],
    },
    ChartType.STACKED_LINE: {
        "name": "Stacked Line Chart",
        "description": "Cumulative trends over time",
        "supports_3d": False,
        "supports_stacking": True,
        "best_for": ["cumulative_trends", "time_series_composition"],
    },
    ChartType.SCATTER: {
        "name": "Scatter Plot",
        "description": "Correlations (spending vs. income, etc.)",
        "supports_3d": True,
        "supports_stacking": False,
        "best_for": ["correlations", "relationships"],
    },
    ChartType.HEATMAP: {
        "name": "Heatmap",
        "description": "Calendar view of transactions",
        "supports_3d": False,
        "supports_stacking": False,
        "best_for": ["calendar_data", "density"],
    },
    ChartType.TREEMAP: {
        "name": "Treemap",
        "description": "Hierarchical data (category breakdowns)",
        "supports_3d": False,
        "supports_stacking": False,
        "best_for": ["hierarchical_data", "nested_categories"],
    },
    ChartType.GAUGE: {
        "name": "Gauge",
        "description": "Budget progress, etc.",
        "supports_3d": False,
        "supports_stacking": False,
        "best_for": ["progress", "kpi"],
    },
}


class ChartConfig:
    """Configuration for a specific chart."""
    
    def __init__(
        self,
        chart_type: ChartType,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        width: int = 800,
        height: int = 600,
        show_legend: bool = True,
        show_grid: bool = True,
        colors: list[str] | None = None,
        style: str = "default",
        **kwargs: Any,
    ) -> None:
        """
        Initialize chart configuration.
        
        Args:
            chart_type: Type of chart to generate
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            width: Chart width in pixels
            height: Chart height in pixels
            show_legend: Whether to show legend
            show_grid: Whether to show grid
            colors: Custom color palette
            style: Chart style (default, modern, minimal, etc.)
            **kwargs: Additional chart-specific options
        """
        self.chart_type = chart_type
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.width = width
        self.height = height
        self.show_legend = show_legend
        self.show_grid = show_grid
        self.colors = colors or [
            "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
            "#9b59b6", "#1abc9c", "#d35400", "#34495e",
        ]
        self.style = style
        self.options = kwargs
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "chart_type": self.chart_type.value,
            "title": self.title,
            "x_label": self.x_label,
            "y_label": self.y_label,
            "width": self.width,
            "height": self.height,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "colors": self.colors,
            "style": self.style,
            "options": self.options,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChartConfig":
        """Create configuration from dictionary."""
        return cls(
            chart_type=ChartType(data.get("chart_type", "line")),
            title=data.get("title", ""),
            x_label=data.get("x_label", ""),
            y_label=data.get("y_label", ""),
            width=data.get("width", 800),
            height=data.get("height", 600),
            show_legend=data.get("show_legend", True),
            show_grid=data.get("show_grid", True),
            colors=data.get("colors"),
            style=data.get("style", "default"),
            **data.get("options", {}),
        )
