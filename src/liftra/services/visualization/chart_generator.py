"""
Chart generator for Liftra visualizations.

Generates various financial charts using matplotlib.
"""

import io
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import ListedColormap
import numpy as np

from liftra.services.visualization.chart_types import ChartType, ChartConfig


class ChartGenerationError(Exception):
    """Exception raised during chart generation."""
    pass


class ChartGenerator:
    """
    Generates financial charts using matplotlib.
    
    Supports various chart types with customizable styling and export options.
    """
    
    # Default color palette
    DEFAULT_COLORS = [
        "#3498db", "#e74c3c", "#2ecc71", "#f39c12",
        "#9b59b6", "#1abc9c", "#d35400", "#34495e",
    ]
    
    # Modern style
    MODERN_STYLE = {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.facecolor": "#f8f9fa",
        "axes.edgecolor": "#e9ecef",
        "axes.grid": True,
        "grid.color": "#dee2e6",
        "grid.alpha": 0.5,
        "axes.labelcolor": "#495057",
        "xtick.color": "#495057",
        "ytick.color": "#495057",
        "figure.facecolor": "white",
        "figure.edgecolor": "white",
    }
    
    def __init__(self) -> None:
        """Initialize the chart generator."""
        # Set default style
        plt.style.use("seaborn-v0_8")
        plt.rcParams.update(self.MODERN_STYLE)
    
    def generate_chart(
        self,
        data: dict[str, Any],
        chart_type: ChartType | str = ChartType.LINE,
        config: ChartConfig | None = None,
        output_path: str | Path | None = None,
        output_format: str = "png",
    ) -> bytes | None:
        """
        Generate a chart from data.
        
        Args:
            data: Chart data dictionary
            chart_type: Type of chart to generate
            config: Chart configuration (optional)
            output_path: Path to save chart (None to return bytes)
            output_format: Output format (png, svg, pdf, jpg)
            
        Returns:
            Chart image as bytes if output_path is None, otherwise None
            
        Raises:
            ChartGenerationError: If chart generation fails
        """
        if isinstance(chart_type, str):
            chart_type = ChartType(chart_type)
        
        if config is None:
            config = ChartConfig(chart_type)
        
        try:
            # Dispatch to specific chart generator
            if chart_type == ChartType.LINE:
                fig = self._generate_line_chart(data, config)
            elif chart_type == ChartType.BAR:
                fig = self._generate_bar_chart(data, config)
            elif chart_type == ChartType.PIE:
                fig = self._generate_pie_chart(data, config)
            elif chart_type == ChartType.STACKED_BAR:
                fig = self._generate_stacked_bar_chart(data, config)
            elif chart_type == ChartType.STACKED_LINE:
                fig = self._generate_stacked_line_chart(data, config)
            elif chart_type == ChartType.SCATTER:
                fig = self._generate_scatter_plot(data, config)
            elif chart_type == ChartType.HEATMAP:
                fig = self._generate_heatmap(data, config)
            elif chart_type == ChartType.TREEMAP:
                fig = self._generate_treemap(data, config)
            elif chart_type == ChartType.GAUGE:
                fig = self._generate_gauge(data, config)
            else:
                raise ChartGenerationError(f"Unsupported chart type: {chart_type}")
            
            # Save or return
            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(path, format=output_format, dpi=300, bbox_inches="tight")
                plt.close(fig)
                return None
            else:
                buffer = io.BytesIO()
                fig.savefig(buffer, format=output_format, dpi=300, bbox_inches="tight")
                plt.close(fig)
                buffer.seek(0)
                return buffer.getvalue()
                
        except Exception as e:
            raise ChartGenerationError(f"Failed to generate chart: {e}")
    
    def _generate_line_chart(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a line chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        labels = data.get("labels", [])
        series = data.get("series", [])
        
        if not series:
            raise ChartGenerationError("No series data provided for line chart")
        
        # Plot each series
        for i, (series_name, series_data) in enumerate(series):
            color = config.colors[i % len(config.colors)]
            ax.plot(
                labels,
                series_data,
                label=series_name,
                color=color,
                linewidth=2,
                marker="o" if len(labels) <= 20 else None,
                markersize=4,
            )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.set_xlabel(config.x_label)
        ax.set_ylabel(config.y_label)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        if config.show_legend and len(series) > 1:
            ax.legend(loc="best")
        
        # Rotate x-axis labels if they're dates
        if labels and isinstance(labels[0], (date, datetime)):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        plt.tight_layout()
        return fig
    
    def _generate_bar_chart(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a bar chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not values:
            raise ChartGenerationError("No values provided for bar chart")
        
        # Plot bars
        bars = ax.bar(
            labels,
            values,
            color=config.colors[:len(values)],
            alpha=0.8,
        )
        
        # Add value labels on top of bars if not too many
        if len(values) <= 20:
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{height:,.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.set_xlabel(config.x_label)
        ax.set_ylabel(config.y_label)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3, axis="y")
        
        if config.show_legend and data.get("legend_labels"):
            ax.legend(data["legend_labels"])
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        return fig
    
    def _generate_pie_chart(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a pie chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not values:
            raise ChartGenerationError("No values provided for pie chart")
        
        # Normalize values to positive (pie charts don't support negative)
        values = [abs(v) for v in values]
        
        # Plot pie
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=config.colors[:len(values)],
            autopct="%1.1f%%" if len(values) <= 10 else None,
            startangle=90,
            textprops={"fontsize": 9},
        )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        
        # Equal aspect ratio ensures pie is drawn as a circle
        ax.axis("equal")
        
        plt.tight_layout()
        return fig
    
    def _generate_stacked_bar_chart(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a stacked bar chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        labels = data.get("labels", [])
        series = data.get("series", [])
        
        if not series:
            raise ChartGenerationError("No series data provided for stacked bar chart")
        
        # Plot stacked bars
        bottom = np.zeros(len(labels))
        
        for i, (series_name, series_data) in enumerate(series):
            color = config.colors[i % len(config.colors)]
            ax.bar(
                labels,
                series_data,
                bottom=bottom,
                label=series_name,
                color=color,
                alpha=0.8,
            )
            bottom += series_data
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.set_xlabel(config.x_label)
        ax.set_ylabel(config.y_label)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3, axis="y")
        
        if config.show_legend:
            ax.legend(loc="upper right")
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        plt.tight_layout()
        return fig
    
    def _generate_stacked_line_chart(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a stacked line chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        labels = data.get("labels", [])
        series = data.get("series", [])
        
        if not series:
            raise ChartGenerationError("No series data provided for stacked line chart")
        
        # Plot stacked lines
        for i, (series_name, series_data) in enumerate(series):
            color = config.colors[i % len(config.colors)]
            ax.plot(
                labels,
                series_data,
                label=series_name,
                color=color,
                linewidth=2,
            )
        
        # Fill between for stacking effect
        if len(series) > 1:
            cumulative = np.zeros(len(labels))
            for i, (series_name, series_data) in enumerate(series):
                cumulative += series_data
                ax.fill_between(
                    labels,
                    cumulative - series_data,
                    cumulative,
                    color=config.colors[i % len(config.colors)],
                    alpha=0.3,
                )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.set_xlabel(config.x_label)
        ax.set_ylabel(config.y_label)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        if config.show_legend:
            ax.legend(loc="upper left")
        
        # Rotate x-axis labels if they're dates
        if labels and isinstance(labels[0], (date, datetime)):
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        plt.tight_layout()
        return fig
    
    def _generate_scatter_plot(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a scatter plot."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        x_values = data.get("x_values", [])
        y_values = data.get("y_values", [])
        
        if not x_values or not y_values:
            raise ChartGenerationError("No x or y values provided for scatter plot")
        
        # Plot scatter
        scatter = ax.scatter(
            x_values,
            y_values,
            c=data.get("colors"),
            s=data.get("sizes", 50),
            alpha=0.6,
            cmap="viridis" if data.get("colors") else None,
        )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.set_xlabel(config.x_label)
        ax.set_ylabel(config.y_label)
        
        if config.show_grid:
            ax.grid(True, alpha=0.3)
        
        if config.show_legend and data.get("legend_labels"):
            ax.legend(data["legend_labels"])
        
        plt.tight_layout()
        return fig
    
    def _generate_heatmap(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a heatmap."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        matrix = data.get("matrix", [])
        x_labels = data.get("x_labels", [])
        y_labels = data.get("y_labels", [])
        
        if not matrix:
            raise ChartGenerationError("No matrix data provided for heatmap")
        
        # Plot heatmap
        im = ax.imshow(
            matrix,
            cmap="YlOrRd",
            aspect="auto",
        )
        
        # Add colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label(config.y_label if config.y_label else "Value")
        
        # Add labels
        ax.set_xticks(range(len(x_labels)))
        ax.set_yticks(range(len(y_labels)))
        ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticklabels(y_labels, fontsize=8)
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        
        plt.tight_layout()
        return fig
    
    def _generate_treemap(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a treemap (using squarify as fallback)."""
        try:
            import squarify
        except ImportError:
            # Fall back to pie chart if squarify is not available
            return self._generate_pie_chart(data, config)
        
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        sizes = data.get("sizes", [])
        labels = data.get("labels", [])
        colors = data.get("colors", config.colors[:len(sizes)])
        
        if not sizes:
            raise ChartGenerationError("No sizes provided for treemap")
        
        # Normalize sizes to positive
        sizes = [abs(s) for s in sizes]
        
        # Plot treemap
        squarify.plot(
            sizes=sizes,
            label=labels,
            color=colors,
            alpha=0.7,
            ax=ax,
            text_kwargs={"fontsize": 8},
        )
        
        # Customize
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.axis("off")
        
        plt.tight_layout()
        return fig
    
    def _generate_gauge(
        self,
        data: dict[str, Any],
        config: ChartConfig,
    ) -> plt.Figure:
        """Generate a gauge chart."""
        fig, ax = plt.subplots(figsize=(config.width / 100, config.height / 100))
        
        # Extract data
        value = data.get("value", 0)
        max_value = data.get("max_value", 100)
        min_value = data.get("min_value", 0)
        label = data.get("label", "")
        
        # Calculate angle
        angle = (value - min_value) / (max_value - min_value) * 180
        
        # Draw gauge
        ax.barh(
            [0],
            [value],
            left=[min_value],
            color=config.colors[0],
            height=0.5,
        )
        
        # Add value text
        ax.text(
            (min_value + max_value) / 2,
            0,
            f"{value:,.2f}",
            ha="center",
            va="center",
            fontsize=14,
            fontweight="bold",
        )
        
        # Customize
        ax.set_xlim(min_value, max_value)
        ax.set_ylim(-0.5, 0.5)
        ax.set_xticks([min_value, max_value])
        ax.set_yticks([])
        ax.set_title(config.title, fontsize=14, fontweight="bold")
        ax.axis("off")
        
        plt.tight_layout()
        return fig
    
    def generate_chart_from_report(
        self,
        report_data: dict[str, Any],
        chart_type: ChartType | str | None = None,
        config: ChartConfig | None = None,
        output_path: str | Path | None = None,
        output_format: str = "png",
    ) -> bytes | None:
        """
        Generate a chart from report data.
        
        Args:
            report_data: Report data dictionary
            chart_type: Type of chart (auto-detected if None)
            config: Chart configuration
            output_path: Path to save chart
            output_format: Output format
            
        Returns:
            Chart image as bytes or None
        """
        # Auto-detect chart type from report type
        if chart_type is None:
            report_type = report_data.get("report_type", "")
            chart_type = self._suggest_chart_type(report_type)
        
        # Convert report data to chart data
        chart_data = self._convert_report_to_chart_data(report_data, chart_type)
        
        return self.generate_chart(
            chart_data,
            chart_type=chart_type,
            config=config,
            output_path=output_path,
            output_format=output_format,
        )
    
    def _suggest_chart_type(self, report_type: str) -> ChartType:
        """Suggest a chart type based on report type."""
        suggestions = {
            "account_statement": ChartType.LINE,
            "spending_by_category": ChartType.PIE,
            "spending_by_payee": ChartType.BAR,
            "budget_vs_actual": ChartType.BAR,
            "net_worth": ChartType.PIE,
            "transaction_history": ChartType.LINE,
        }
        return suggestions.get(report_type, ChartType.LINE)
    
    def _convert_report_to_chart_data(
        self,
        report_data: dict[str, Any],
        chart_type: ChartType,
    ) -> dict[str, Any]:
        """Convert report data to chart data format."""
        report_type = report_data.get("report_type", "")
        
        if report_type == "spending_by_category":
            categories = report_data.get("categories", [])
            return {
                "labels": [c.get("category_id", "Unknown") for c in categories],
                "values": [float(c.get("amount", 0)) for c in categories],
            }
        elif report_type == "spending_by_payee":
            payees = report_data.get("payees", [])
            return {
                "labels": [p.get("payee_id", "Unknown") for p in payees],
                "values": [float(p.get("amount", 0)) for p in payees],
            }
        elif report_type == "budget_vs_actual":
            comparison = report_data.get("comparison", [])
            return {
                "labels": [c.get("category_id", "Unknown") for c in comparison],
                "series": [
                    ("Budgeted", [float(c.get("budgeted", 0)) for c in comparison]),
                    ("Actual", [float(c.get("actual", 0)) for c in comparison]),
                ],
            }
        elif report_type == "net_worth":
            by_type = report_data.get("by_account_type", [])
            return {
                "labels": [t.get("account_type", "Unknown") for t in by_type],
                "values": [float(t.get("balance", 0)) for t in by_type],
            }
        elif report_type == "account_statement":
            transactions = report_data.get("transactions", [])
            # Group by date for line chart
            dates = []
            balances = []
            current_balance = 0
            
            for t in sorted(transactions, key=lambda x: x.get("dates", [{}])[0].get("date_value", "")):
                date_str = t.get("dates", [{}])[0].get("date_value", "")
                amount = float(t.get("amount", 0))
                
                if t.get("transaction_type") in ["income", "transfer"]:
                    current_balance += amount
                else:
                    current_balance -= amount
                
                dates.append(date_str)
                balances.append(current_balance)
            
            return {
                "labels": dates,
                "series": [("Balance", balances)],
            }
        else:
            # Default: try to extract labels and values
            return {
                "labels": list(report_data.keys())[:10],
                "values": list(report_data.values())[:10],
            }
