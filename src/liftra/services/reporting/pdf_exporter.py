"""
PDF exporter for Liftra reports.

Exports financial reports to PDF format using WeasyPrint.
"""

import io
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from liftra.services.reporting.report_types import ReportType


class PDFExportError(Exception):
    """Exception raised during PDF export."""
    pass


class PDFExporter:
    """
    Exports financial reports to PDF format.
    
    Uses WeasyPrint for HTML to PDF conversion with custom styling.
    """
    
    # Default CSS styles for PDF
    DEFAULT_CSS = """
    @page {
        size: A4;
        margin: 1cm;
        font-family: DejaVu Sans, sans-serif;
    }
    
    body {
        font-family: DejaVu Sans, sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #333;
    }
    
    h1 {
        font-size: 18pt;
        font-weight: bold;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    h2 {
        font-size: 14pt;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    h3 {
        font-size: 12pt;
        font-weight: bold;
        color: #34495e;
        margin-top: 15px;
        margin-bottom: 8px;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
    }
    
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #3498db;
        color: white;
        font-weight: bold;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    tr:hover {
        background-color: #e9ecef;
    }
    
    .total-row {
        font-weight: bold;
        background-color: #e8f4fc !important;
    }
    
    .amount {
        text-align: right;
    }
    
    .positive {
        color: #28a745;
    }
    
    .negative {
        color: #dc3545;
    }
    
    .metadata {
        font-size: 8pt;
        color: #6c757d;
        margin-top: 20px;
        border-top: 1px solid #ddd;
        padding-top: 10px;
    }
    
    .chart-container {
        margin: 20px 0;
        text-align: center;
    }
    
    .chart-container img {
        max-width: 100%;
        height: auto;
    }
    """
    
    def __init__(self) -> None:
        """Initialize the PDF exporter."""
        # Configure font configuration for WeasyPrint
        self.font_config = FontConfiguration()
    
    def export_report(
        self,
        report_data: dict[str, Any],
        output_path: str | Path | None = None,
        include_charts: bool = True,
    ) -> bytes | None:
        """
        Export a report to PDF.
        
        Args:
            report_data: Report data dictionary
            output_path: Path to save PDF (None to return bytes)
            include_charts: Whether to include charts in PDF
            
        Returns:
            PDF content as bytes if output_path is None, otherwise None
            
        Raises:
            PDFExportError: If export fails
        """
        try:
            # Generate HTML
            html_content = self._generate_html(report_data, include_charts)
            
            # Create CSS
            css = CSS(string=self.DEFAULT_CSS)
            
            # Create HTML object
            html = HTML(string=html_content)
            
            # Generate PDF
            pdf_content = html.write_pdf(
                font_config=self.font_config,
                stylesheets=[css],
            )
            
            # Save to file or return bytes
            if output_path:
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(path, "wb") as f:
                    f.write(pdf_content)
                return None
            else:
                return pdf_content
                
        except Exception as e:
            raise PDFExportError(f"Failed to export PDF: {e}")
    
    def _generate_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """
        Generate HTML content for a report.
        
        Args:
            report_data: Report data dictionary
            include_charts: Whether to include charts
            
        Returns:
            HTML content as string
        """
        report_type = report_data.get("report_type", "unknown")
        
        # Dispatch to specific HTML generator
        if report_type == ReportType.ACCOUNT_STATEMENT.value:
            return self._generate_account_statement_html(report_data, include_charts)
        elif report_type == ReportType.SPENDING_BY_CATEGORY.value:
            return self._generate_spending_by_category_html(report_data, include_charts)
        elif report_type == ReportType.SPENDING_BY_PAYEE.value:
            return self._generate_spending_by_payee_html(report_data, include_charts)
        elif report_type == ReportType.BUDGET_VS_ACTUAL.value:
            return self._generate_budget_vs_actual_html(report_data, include_charts)
        elif report_type == ReportType.NET_WORTH.value:
            return self._generate_net_worth_html(report_data, include_charts)
        elif report_type == ReportType.TRANSACTION_HISTORY.value:
            return self._generate_transaction_history_html(report_data, include_charts)
        else:
            return self._generate_generic_report_html(report_data, include_charts)
    
    def _generate_account_statement_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for account statement report."""
        account = report_data.get("account")
        transactions = report_data.get("transactions", [])
        totals = report_data.get("totals", {})
        period = report_data.get("period", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Account Statement')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Account Statement')}</h1>
            
            <p><strong>Account:</strong> {account.get('name', 'All Accounts') if account else 'All Accounts'}</p>
            <p><strong>Period:</strong> {period.get('start_date', '')} to {period.get('end_date', '')}</p>
            
            <h2>Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th class="amount">Amount</th>
                        <th>Category</th>
                        <th>Payee</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for transaction in transactions:
            date_str = self._format_date(transaction.get("dates"))
            description = transaction.get("description", "")
            trans_type = transaction.get("transaction_type", "")
            amount = transaction.get("amount", Decimal(0))
            category = transaction.get("category_id", "")
            payee = transaction.get("payee_id", "")
            
            amount_class = "positive" if amount >= 0 else "negative"
            
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{description}</td>
                        <td>{trans_type}</td>
                        <td class="amount {amount_class}">{self._format_currency(amount, transaction.get('currency_code', 'GBP'))}</td>
                        <td>{category}</td>
                        <td>{payee}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td colspan="3"><strong>Totals:</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_income', Decimal(0)), 'GBP')}</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_expense', Decimal(0)), 'GBP')}</strong></td>
                        <td></td>
                    </tr>
                    <tr class="total-row">
                        <td colspan="4"><strong>Net:</strong></td>
                        <td class="amount" colspan="2"><strong>{self._format_currency(totals.get('net', Decimal(0)), 'GBP')}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            <p><strong>Transaction Count:</strong> {totals.get('transaction_count', 0)}</p>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_spending_by_category_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for spending by category report."""
        categories = report_data.get("categories", [])
        totals = report_data.get("totals", {})
        period = report_data.get("period", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Spending by Category')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Spending by Category')}</h1>
            
            <p><strong>Period:</strong> {period.get('start_date', '')} to {period.get('end_date', '')}</p>
            
            <h2>Spending Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th class="amount">Amount</th>
                        <th class="amount">Percentage</th>
                        <th>Transactions</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total_spending = totals.get("total_spending", Decimal(0))
        
        for category in categories:
            amount = category.get("amount", Decimal(0))
            percentage = (amount / total_spending * 100) if total_spending != 0 else 0
            count = category.get("transaction_count", 0)
            
            html += f"""
                    <tr>
                        <td>{category.get('category_id', 'Unknown')}</td>
                        <td class="amount negative">{self._format_currency(amount, 'GBP')}</td>
                        <td class="amount">{percentage:.2f}%</td>
                        <td>{count}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        <td class="amount"><strong>{self._format_currency(total_spending, 'GBP')}</strong></td>
                        <td class="amount"><strong>100%</strong></td>
                        <td><strong>{totals.get('category_count', 0)}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_spending_by_payee_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for spending by payee report."""
        payees = report_data.get("payees", [])
        totals = report_data.get("totals", {})
        period = report_data.get("period", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Spending by Payee')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Spending by Payee')}</h1>
            
            <p><strong>Period:</strong> {period.get('start_date', '')} to {period.get('end_date', '')}</p>
            
            <h2>Spending by Payee</h2>
            <table>
                <thead>
                    <tr>
                        <th>Payee</th>
                        <th class="amount">Amount</th>
                        <th class="amount">Percentage</th>
                        <th>Transactions</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total_spending = totals.get("total_spending", Decimal(0))
        
        for payee in payees:
            amount = payee.get("amount", Decimal(0))
            percentage = (amount / total_spending * 100) if total_spending != 0 else 0
            count = payee.get("transaction_count", 0)
            
            html += f"""
                    <tr>
                        <td>{payee.get('payee_id', 'Unknown')}</td>
                        <td class="amount negative">{self._format_currency(amount, 'GBP')}</td>
                        <td class="amount">{percentage:.2f}%</td>
                        <td>{count}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        <td class="amount"><strong>{self._format_currency(total_spending, 'GBP')}</strong></td>
                        <td class="amount"><strong>100%</strong></td>
                        <td><strong>{totals.get('payee_count', 0)}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_budget_vs_actual_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for budget vs. actual report."""
        comparison = report_data.get("comparison", [])
        totals = report_data.get("totals", {})
        period = report_data.get("period", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Budget vs. Actual')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Budget vs. Actual')}</h1>
            
            <p><strong>Period:</strong> {period.get('start_date', '')} to {period.get('end_date', '')}</p>
            
            <h2>Budget vs. Actual Spending</h2>
            <table>
                <thead>
                    <tr>
                        <th>Category</th>
                        <th class="amount">Budgeted</th>
                        <th class="amount">Actual</th>
                        <th class="amount">Variance</th>
                        <th class="amount">Variance %</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in comparison:
            budgeted = item.get("budgeted", Decimal(0))
            actual = item.get("actual", Decimal(0))
            variance = item.get("variance", Decimal(0))
            variance_pct = item.get("variance_percentage", 0)
            
            variance_class = "positive" if variance >= 0 else "negative"
            
            html += f"""
                    <tr>
                        <td>{item.get('category_id', 'Unknown')}</td>
                        <td class="amount">{self._format_currency(budgeted, 'GBP')}</td>
                        <td class="amount">{self._format_currency(actual, 'GBP')}</td>
                        <td class="amount {variance_class}">{self._format_currency(variance, 'GBP')}</td>
                        <td class="amount {variance_class}">{variance_pct:.2f}%</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_budgeted', Decimal(0)), 'GBP')}</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_actual', Decimal(0)), 'GBP')}</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_variance', Decimal(0)), 'GBP')}</strong></td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_net_worth_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for net worth report."""
        by_type = report_data.get("by_account_type", [])
        totals = report_data.get("totals", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Net Worth')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Net Worth')}</h1>
            
            <h2>Net Worth by Account Type</h2>
            <table>
                <thead>
                    <tr>
                        <th>Account Type</th>
                        <th>Balance</th>
                        <th>Accounts</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in by_type:
            balance = item.get("balance", Decimal(0))
            count = item.get("account_count", 0)
            
            amount_class = "positive" if balance >= 0 else "negative"
            
            html += f"""
                    <tr>
                        <td>{item.get('account_type', 'Unknown')}</td>
                        <td class="amount {amount_class}">{self._format_currency(balance, 'GBP')}</td>
                        <td>{count}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td><strong>Total Net Worth</strong></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('total_net_worth', Decimal(0)), 'GBP')}</strong></td>
                        <td><strong>{totals.get('account_count', 0)}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_transaction_history_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate HTML for transaction history report."""
        transactions = report_data.get("transactions", [])
        totals = report_data.get("totals", {})
        period = report_data.get("period", {})
        filters = report_data.get("filters", {})
        
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Transaction History')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Transaction History')}</h1>
            
            <p><strong>Period:</strong> {period.get('start_date', '')} to {period.get('end_date', '')}</p>
        """
        
        if filters.get("account_id"):
            html += f'<p><strong>Account:</strong> {filters["account_id"]}</p>'
        if filters.get("category_id"):
            html += f'<p><strong>Category:</strong> {filters["category_id"]}</p>'
        if filters.get("payee_id"):
            html += f'<p><strong>Payee:</strong> {filters["payee_id"]}</p>'
        
        html += """
            <h2>Transactions</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Description</th>
                        <th>Type</th>
                        <th class="amount">Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for transaction in transactions:
            date_str = self._format_date(transaction.get("dates"))
            description = transaction.get("description", "")
            trans_type = transaction.get("transaction_type", "")
            amount = transaction.get("amount", Decimal(0))
            
            amount_class = "positive" if amount >= 0 else "negative"
            
            html += f"""
                    <tr>
                        <td>{date_str}</td>
                        <td>{description}</td>
                        <td>{trans_type}</td>
                        <td class="amount {amount_class}">{self._format_currency(amount, transaction.get('currency_code', 'GBP'))}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
                <tfoot>
                    <tr class="total-row">
                        <td colspan="3"><strong>Totals:</strong></td>
                        <td></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Income:</strong></td>
                        <td colspan="2"></td>
                        <td class="amount positive"><strong>{self._format_currency(totals.get('total_income', Decimal(0)), 'GBP')}</strong></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Expenses:</strong></td>
                        <td colspan="2"></td>
                        <td class="amount negative"><strong>{self._format_currency(totals.get('total_expense', Decimal(0)), 'GBP')}</strong></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Net:</strong></td>
                        <td colspan="2"></td>
                        <td class="amount"><strong>{self._format_currency(totals.get('net', Decimal(0)), 'GBP')}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            <p><strong>Transaction Count:</strong> {totals.get('transaction_count', 0)}</p>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        
        return html
    
    def _generate_generic_report_html(
        self,
        report_data: dict[str, Any],
        include_charts: bool = True,
    ) -> str:
        """Generate generic HTML for unknown report types."""
        html = f"""
        <html>
        <head><title>{report_data.get('title', 'Report')}</title></head>
        <body>
            <h1>{report_data.get('title', 'Report')}</h1>
            
            <pre>{report_data}</pre>
            
            {self._generate_metadata_html(report_data)}
        </body>
        </html>
        """
        return html
    
    def _generate_metadata_html(self, report_data: dict[str, Any]) -> str:
        """Generate metadata HTML for report footer."""
        generated_at = report_data.get("generated_at", "")
        return f"""
        <div class="metadata">
            Generated: {generated_at if generated_at else datetime.utcnow().isoformat()}<br>
            Report Type: {report_data.get('report_type', 'unknown')}
        </div>
        """
    
    def _format_date(self, dates: list[dict[str, Any]] | None) -> str:
        """Format dates for display."""
        if not dates:
            return ""
        
        for date_info in dates:
            if isinstance(date_info, dict) and date_info.get("is_primary"):
                return date_info.get("date_value", "")
        
        return dates[0].get("date_value", "") if dates else ""
    
    def _format_currency(self, amount: Decimal | float | int | str, currency: str = "GBP") -> str:
        """Format currency amount for display."""
        if isinstance(amount, str):
            try:
                amount = Decimal(amount)
            except Exception:
                return str(amount)
        
        if isinstance(amount, (float, int)):
            amount = Decimal(str(amount))
        
        # Format with 2 decimal places
        formatted = f"{amount:,.2f}"
        return f"{currency} {formatted}"
