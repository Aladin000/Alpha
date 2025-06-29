"""
visualizations_page.py

Visualizations and Simulations page UI for the Alpha application.
Handles the user interface for data visualization and financial simulations.
Integrates with utils.py visualization functions while maintaining separation of concerns.
"""

import os
import io
import base64
from typing import Optional, Dict, Any, List

# Set Qt API before importing matplotlib
os.environ['QT_API'] = 'pyside6'

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QDoubleSpinBox, QSpinBox, QTextEdit, QSplitter, QScrollArea,
    QMessageBox, QDateEdit, QCheckBox, QSlider, QProgressBar,
    QFrame
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QPixmap
import logging
from datetime import datetime, date

# Import business logic
from finance import PersonalFinance
from trading import TradingJournal  
from positions import OpenPositions
import utils

# Configure matplotlib for non-interactive use
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Configure logging
logger = logging.getLogger(__name__)


class PlotWidget(QLabel):
    """Custom widget to display matplotlib plots as images in QLabel."""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }
        """)
        self.setMinimumSize(600, 400)
        self.setText("No chart to display")
    
    def set_figure(self, fig):
        """Convert matplotlib figure to QPixmap and display."""
        try:
            # Save figure to bytes buffer
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            # Create QPixmap from bytes
            pixmap = QPixmap()
            pixmap.loadFromData(buf.getvalue())
            
            # Scale to fit widget while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.setPixmap(scaled_pixmap)
            
            # Close figure to free memory
            plt.close(fig)
            buf.close()
            
            logger.info("Chart displayed successfully")
            
        except Exception as e:
            logger.error(f"Failed to display chart: {e}")
            self.setText(f"Error displaying chart: {str(e)}")
    
    def clear_plot(self):
        """Clear the current plot."""
        self.clear()
        self.setText("No chart to display")


class ChartGeneratorThread(QThread):
    """Thread for generating charts without blocking the UI."""
    
    chart_ready = Signal(object)  # Emits matplotlib Figure
    error_occurred = Signal(str)
    
    def __init__(self, chart_type: str, data: List[Dict[str, Any]], title: str = ""):
        super().__init__()
        self.chart_type = chart_type
        self.data = data
        self.title = title
    
    def run(self):
        """Generate the chart in a separate thread."""
        try:
            if self.chart_type == "expenses":
                fig = utils.plot_expenses_over_time(self.data, title=self.title)
            elif self.chart_type == "savings":
                fig = utils.plot_savings_growth(self.data, title=self.title)
            elif self.chart_type == "pnl":
                fig = utils.plot_pnl_history(self.data, title=self.title)
            elif self.chart_type == "portfolio":
                fig = utils.plot_portfolio_allocation(self.data, title=self.title)
            else:
                raise utils.UtilsError(f"Unknown chart type: {self.chart_type}")
            
            self.chart_ready.emit(fig)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class VisualizationsPage(QWidget):
    """
    Visualizations and Simulations page.
    
    Provides UI for:
    - Financial data visualization and charts
    - Interactive financial simulations
    - Data export and analysis tools
    - Custom chart configuration
    
    Integrates with utils.py functions while maintaining
    strict separation between UI and business logic.
    """
    
    def __init__(self, personal_finance: Optional[PersonalFinance] = None,
                 trading_journal: Optional[TradingJournal] = None,
                 open_positions: Optional[OpenPositions] = None):
        """
        Initialize the Visualizations page.
        
        Args:
            personal_finance: PersonalFinance instance for business logic
            trading_journal: TradingJournal instance for business logic
            open_positions: OpenPositions instance for business logic
        """
        super().__init__()
        
        # Store business logic references
        self.personal_finance = personal_finance
        self.trading_journal = trading_journal
        self.open_positions = open_positions
        
        # Chart generation thread
        self.chart_thread = None
        
        self._setup_ui()
        logger.info("Visualizations page initialized")
    
    def set_business_logic(self, personal_finance: PersonalFinance = None,
                          trading_journal: TradingJournal = None, 
                          open_positions: OpenPositions = None):
        """Set business logic instances."""
        if personal_finance:
            self.personal_finance = personal_finance
        if trading_journal:
            self.trading_journal = trading_journal
        if open_positions:
            self.open_positions = open_positions
    
    def _setup_ui(self):
        """Set up the main UI layout and components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Page title
        title_label = QLabel("Analytics & Simulations")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tab widget for different visualization types
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Add tabs
        self._setup_charts_tab()
        self._setup_simulations_tab()
        self._setup_analysis_tab()
    
    def _setup_charts_tab(self):
        """Set up the data visualization tab."""
        charts_widget = QWidget()
        layout = QHBoxLayout(charts_widget)
        
        # Left panel for controls
        controls_frame = QFrame()
        controls_frame.setMaximumWidth(300)
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_layout = QVBoxLayout(controls_frame)
        
        # Chart type selection
        chart_group = QGroupBox("Chart Type")
        chart_form = QFormLayout(chart_group)
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems([
            "Expenses Over Time",
            "Savings Growth",
            "P&L History", 
            "Portfolio Allocation"
        ])
        chart_form.addRow("Type:", self.chart_type_combo)
        
        # Date range selection
        self.start_date = QDateEdit()
        self.start_date.setDate(date(2024, 1, 1))
        self.start_date.setCalendarPopup(True)
        chart_form.addRow("Start Date:", self.start_date)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(date.today())
        self.end_date.setCalendarPopup(True)
        chart_form.addRow("End Date:", self.end_date)
        
        # Chart options
        self.include_categories = QCheckBox("Include Categories")
        self.include_categories.setChecked(True)
        chart_form.addRow(self.include_categories)
        
        controls_layout.addWidget(chart_group)
        
        # Generate button
        self.generate_chart_btn = QPushButton("Generate Chart")
        self.generate_chart_btn.clicked.connect(self._generate_chart)
        controls_layout.addWidget(self.generate_chart_btn)
        
        # Clear button
        clear_chart_btn = QPushButton("Clear Chart")
        clear_chart_btn.clicked.connect(self._clear_chart)
        controls_layout.addWidget(clear_chart_btn)
        
        # Status
        self.chart_status = QLabel("Ready to generate charts")
        self.chart_status.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.chart_status)
        
        controls_layout.addStretch()
        
        # Right panel for chart display
        chart_display_layout = QVBoxLayout()
        
        # Chart display widget
        self.chart_widget = PlotWidget()
        chart_display_layout.addWidget(self.chart_widget)
        
        # Add to main layout
        layout.addWidget(controls_frame)
        layout.addLayout(chart_display_layout, 1)
        
        # Add to tab widget
        self.tab_widget.addTab(charts_widget, "📊 Charts")
    
    def _setup_simulations_tab(self):
        """Set up the financial simulations tab."""
        simulations_widget = QWidget()
        layout = QHBoxLayout(simulations_widget)
        
        # Left panel for simulation controls
        sim_controls_frame = QFrame()
        sim_controls_frame.setMaximumWidth(350)
        sim_controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        sim_controls_layout = QVBoxLayout(sim_controls_frame)
        
        # Simulation type selection
        sim_type_group = QGroupBox("Simulation Type")
        sim_type_layout = QVBoxLayout(sim_type_group)
        
        self.sim_type_combo = QComboBox()
        self.sim_type_combo.addItems([
            "Savings Growth",
            "Compound Interest",
            "Retirement Planning",
            "Loan Payment"
        ])
        self.sim_type_combo.currentTextChanged.connect(self._update_sim_controls)
        sim_type_layout.addWidget(self.sim_type_combo)
        
        sim_controls_layout.addWidget(sim_type_group)
        
        # Dynamic simulation parameters
        self.sim_params_group = QGroupBox("Parameters")
        self.sim_params_layout = QFormLayout(self.sim_params_group)
        sim_controls_layout.addWidget(self.sim_params_group)
        
        # Run simulation button
        self.run_sim_btn = QPushButton("Run Simulation")
        self.run_sim_btn.clicked.connect(self._run_simulation)
        sim_controls_layout.addWidget(self.run_sim_btn)
        
        # Simulation status
        self.sim_status = QLabel("Ready to run simulations")
        self.sim_status.setStyleSheet("color: #666; font-style: italic;")
        sim_controls_layout.addWidget(self.sim_status)
        
        sim_controls_layout.addStretch()
        
        # Right panel for results
        results_layout = QVBoxLayout()
        
        # Results display
        self.sim_results = QTextEdit()
        self.sim_results.setReadOnly(True)
        self.sim_results.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        self.sim_results.setText("Simulation results will appear here...")
        results_layout.addWidget(self.sim_results)
        
        # Add to main layout
        layout.addWidget(sim_controls_frame)
        layout.addLayout(results_layout, 1)
        
        # Initialize simulation controls
        self._update_sim_controls()
        
        # Add to tab widget
        self.tab_widget.addTab(simulations_widget, "🔮 Simulations")
    
    def _setup_analysis_tab(self):
        """Set up the advanced analysis tab."""
        analysis_widget = QWidget()
        layout = QVBoxLayout(analysis_widget)
        
        # Analysis section header
        header_label = QLabel("Advanced Analysis")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Analysis content
        self.analysis_content = QTextEdit()
        self.analysis_content.setReadOnly(True)
        self.analysis_content.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                font-family: monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.analysis_content)
        
        # Analysis controls
        analysis_controls = QHBoxLayout()
        
        self.analyze_expenses_btn = QPushButton("Analyze Expenses")
        self.analyze_expenses_btn.clicked.connect(self._analyze_expenses)
        analysis_controls.addWidget(self.analyze_expenses_btn)
        
        self.analyze_trading_btn = QPushButton("Analyze Trading")
        self.analyze_trading_btn.clicked.connect(self._analyze_trading)
        analysis_controls.addWidget(self.analyze_trading_btn)
        
        self.analyze_portfolio_btn = QPushButton("Analyze Portfolio")
        self.analyze_portfolio_btn.clicked.connect(self._analyze_portfolio)
        analysis_controls.addWidget(self.analyze_portfolio_btn)
        
        analysis_controls.addStretch()
        
        layout.addLayout(analysis_controls)
        
        # Add to tab widget
        self.tab_widget.addTab(analysis_widget, "🔬 Analysis")
    
    def _generate_chart(self):
        """Generate the selected chart type."""
        if not self._check_business_logic_available():
            return
        
        try:
            chart_type = self.chart_type_combo.currentText()
            self.chart_status.setText("Generating chart...")
            
            # Get data based on chart type
            data = []
            title = ""
            
            if chart_type == "Expenses Over Time":
                if not self.personal_finance:
                    QMessageBox.warning(self, "Error", "Personal Finance service not available")
                    return
                
                expenses = self.personal_finance.get_all_expenses()
                data = [
                    {
                        'date': expense['date'],
                        'amount': expense['amount'],
                        'category': expense['category']
                    }
                    for expense in expenses
                ]
                title = "Expenses Over Time"
                chart_type_key = "expenses"
                
            elif chart_type == "Savings Growth":
                if not self.personal_finance:
                    QMessageBox.warning(self, "Error", "Personal Finance service not available")
                    return
                
                savings = self.personal_finance.get_all_savings()
                data = [
                    {
                        'date': saving['date'],
                        'amount': saving['amount'],
                        'source': saving.get('source', 'Other')
                    }
                    for saving in savings
                ]
                title = "Savings Growth Over Time"
                chart_type_key = "savings"
                
            elif chart_type == "P&L History":
                if not self.trading_journal:
                    QMessageBox.warning(self, "Error", "Trading Journal service not available")
                    return
                
                trades = self.trading_journal.get_all_trades()
                data = [
                    {
                        'date': trade['entry_date'],
                        'symbol': trade['symbol'],
                        'pnl': (trade['exit_price'] - trade['entry_price']) * trade['quantity'] if trade.get('exit_price') else 0,
                        'trade_type': trade['trade_type']
                    }
                    for trade in trades
                ]
                title = "Trading P&L History"
                chart_type_key = "pnl"
                
            elif chart_type == "Portfolio Allocation":
                if not self.open_positions:
                    QMessageBox.warning(self, "Error", "Open Positions service not available")
                    return
                
                positions = self.open_positions.get_all_positions()
                data = [
                    {
                        'symbol': pos['symbol'],
                        'asset_type': pos['asset_type'],
                        'value': pos['entry_price'] * pos['quantity']
                    }
                    for pos in positions
                ]
                title = "Portfolio Allocation"
                chart_type_key = "portfolio"
            
            if not data:
                QMessageBox.information(self, "No Data", f"No data available for {chart_type}")
                self.chart_status.setText("No data available")
                return
            
            # Generate chart in thread
            self.chart_thread = ChartGeneratorThread(chart_type_key, data, title)
            self.chart_thread.chart_ready.connect(self._on_chart_ready)
            self.chart_thread.error_occurred.connect(self._on_chart_error)
            self.chart_thread.start()
            
        except Exception as e:
            error_msg = f"Failed to generate chart: {str(e)}"
            self.chart_status.setText(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            logger.error(f"Chart generation failed: {e}")
    
    def _on_chart_ready(self, fig):
        """Handle when chart is ready from thread."""
        self.chart_widget.set_figure(fig)
        self.chart_status.setText("Chart generated successfully")
    
    def _on_chart_error(self, error_msg):
        """Handle chart generation error."""
        self.chart_status.setText(f"Chart generation failed: {error_msg}")
        QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {error_msg}")
    
    def _clear_chart(self):
        """Clear the current chart."""
        self.chart_widget.clear_plot()
        self.chart_status.setText("Chart cleared")
    
    def _update_sim_controls(self):
        """Update simulation parameter controls based on selected type."""
        # Clear existing controls
        while self.sim_params_layout.count():
            child = self.sim_params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        sim_type = self.sim_type_combo.currentText()
        
        if sim_type == "Savings Growth":
            self.initial_amount = QDoubleSpinBox()
            self.initial_amount.setRange(0, 1000000)
            self.initial_amount.setValue(1000)
            self.initial_amount.setPrefix("$")
            self.sim_params_layout.addRow("Initial Amount:", self.initial_amount)
            
            self.monthly_contribution = QDoubleSpinBox()
            self.monthly_contribution.setRange(0, 10000)
            self.monthly_contribution.setValue(500)
            self.monthly_contribution.setPrefix("$")
            self.sim_params_layout.addRow("Monthly Contribution:", self.monthly_contribution)
            
            self.annual_rate = QDoubleSpinBox()
            self.annual_rate.setRange(0, 50)
            self.annual_rate.setValue(7.0)
            self.annual_rate.setSuffix("%")
            self.annual_rate.setDecimals(2)
            self.sim_params_layout.addRow("Annual Rate:", self.annual_rate)
            
            self.years = QSpinBox()
            self.years.setRange(1, 50)
            self.years.setValue(10)
            self.years.setSuffix(" years")
            self.sim_params_layout.addRow("Time Period:", self.years)
            
        elif sim_type == "Compound Interest":
            self.principal = QDoubleSpinBox()
            self.principal.setRange(1, 1000000)
            self.principal.setValue(10000)
            self.principal.setPrefix("$")
            self.sim_params_layout.addRow("Principal:", self.principal)
            
            self.interest_rate = QDoubleSpinBox()
            self.interest_rate.setRange(0, 50)
            self.interest_rate.setValue(5.0)
            self.interest_rate.setSuffix("%")
            self.interest_rate.setDecimals(2)
            self.sim_params_layout.addRow("Annual Rate:", self.interest_rate)
            
            self.compound_freq = QSpinBox()
            self.compound_freq.setRange(1, 365)
            self.compound_freq.setValue(12)
            self.compound_freq.setSuffix(" times/year")
            self.sim_params_layout.addRow("Compound Frequency:", self.compound_freq)
            
            self.time_years = QDoubleSpinBox()
            self.time_years.setRange(0.1, 50)
            self.time_years.setValue(10.0)
            self.time_years.setSuffix(" years")
            self.time_years.setDecimals(1)
            self.sim_params_layout.addRow("Time Period:", self.time_years)
            
        elif sim_type == "Retirement Planning":
            self.current_age = QSpinBox()
            self.current_age.setRange(18, 80)
            self.current_age.setValue(30)
            self.current_age.setSuffix(" years")
            self.sim_params_layout.addRow("Current Age:", self.current_age)
            
            self.retirement_age = QSpinBox()
            self.retirement_age.setRange(50, 100)
            self.retirement_age.setValue(65)
            self.retirement_age.setSuffix(" years")
            self.sim_params_layout.addRow("Retirement Age:", self.retirement_age)
            
            self.current_savings = QDoubleSpinBox()
            self.current_savings.setRange(0, 10000000)
            self.current_savings.setValue(50000)
            self.current_savings.setPrefix("$")
            self.sim_params_layout.addRow("Current Savings:", self.current_savings)
            
            self.monthly_contrib = QDoubleSpinBox()
            self.monthly_contrib.setRange(0, 10000)
            self.monthly_contrib.setValue(1000)
            self.monthly_contrib.setPrefix("$")
            self.sim_params_layout.addRow("Monthly Contribution:", self.monthly_contrib)
            
            self.return_rate = QDoubleSpinBox()
            self.return_rate.setRange(0, 20)
            self.return_rate.setValue(7.0)
            self.return_rate.setSuffix("%")
            self.return_rate.setDecimals(2)
            self.sim_params_layout.addRow("Annual Return:", self.return_rate)
            
            self.withdrawal_rate = QDoubleSpinBox()
            self.withdrawal_rate.setRange(1, 10)
            self.withdrawal_rate.setValue(4.0)
            self.withdrawal_rate.setSuffix("%")
            self.withdrawal_rate.setDecimals(2)
            self.sim_params_layout.addRow("Withdrawal Rate:", self.withdrawal_rate)
            
        elif sim_type == "Loan Payment":
            self.loan_amount = QDoubleSpinBox()
            self.loan_amount.setRange(1000, 10000000)
            self.loan_amount.setValue(300000)
            self.loan_amount.setPrefix("$")
            self.sim_params_layout.addRow("Loan Amount:", self.loan_amount)
            
            self.loan_rate = QDoubleSpinBox()
            self.loan_rate.setRange(0.1, 30)
            self.loan_rate.setValue(4.5)
            self.loan_rate.setSuffix("%")
            self.loan_rate.setDecimals(2)
            self.sim_params_layout.addRow("Annual Rate:", self.loan_rate)
            
            self.loan_years = QSpinBox()
            self.loan_years.setRange(1, 50)
            self.loan_years.setValue(30)
            self.loan_years.setSuffix(" years")
            self.sim_params_layout.addRow("Loan Term:", self.loan_years)
    
    def _run_simulation(self):
        """Run the selected simulation."""
        try:
            sim_type = self.sim_type_combo.currentText()
            self.sim_status.setText("Running simulation...")
            
            if sim_type == "Savings Growth":
                result = utils.simulate_savings_growth(
                    initial=self.initial_amount.value(),
                    monthly=self.monthly_contribution.value(),
                    annual_rate=self.annual_rate.value() / 100,
                    periods=self.years.value() * 12
                )
                
                final_amount = result[-1]
                total_contributions = self.initial_amount.value() + (self.monthly_contribution.value() * self.years.value() * 12)
                interest_earned = final_amount - total_contributions
                
                results_text = f"""SAVINGS GROWTH SIMULATION
{'=' * 40}

PARAMETERS:
• Initial Amount:        ${self.initial_amount.value():,.2f}
• Monthly Contribution:  ${self.monthly_contribution.value():,.2f}
• Annual Interest Rate:  {self.annual_rate.value():.2f}%
• Time Period:           {self.years.value()} years

RESULTS:
• Final Amount:          ${final_amount:,.2f}
• Total Contributions:   ${total_contributions:,.2f}
• Interest Earned:       ${interest_earned:,.2f}
• Return on Investment:  {(interest_earned / total_contributions * 100):,.2f}%

MONTHLY BREAKDOWN (last 12 months):
"""
                for i, amount in enumerate(result[-12:], 1):
                    month = self.years.value() * 12 - 12 + i
                    results_text += f"• Month {month:2d}: ${amount:,.2f}\n"
                
            elif sim_type == "Compound Interest":
                result = utils.simulate_compound_interest(
                    principal=self.principal.value(),
                    annual_rate=self.interest_rate.value() / 100,
                    times_per_year=self.compound_freq.value(),
                    years=self.time_years.value()
                )
                
                interest_earned = result - self.principal.value()
                
                results_text = f"""COMPOUND INTEREST SIMULATION
{'=' * 40}

PARAMETERS:
• Principal:             ${self.principal.value():,.2f}
• Annual Interest Rate:  {self.interest_rate.value():.2f}%
• Compound Frequency:    {self.compound_freq.value()} times per year
• Time Period:           {self.time_years.value():.1f} years

RESULTS:
• Final Amount:          ${result:,.2f}
• Interest Earned:       ${interest_earned:,.2f}
• Effective Annual Rate: {((result / self.principal.value()) ** (1 / self.time_years.value()) - 1) * 100:.3f}%
• Growth Multiple:       {result / self.principal.value():.2f}x
"""
                
            elif sim_type == "Retirement Planning":
                result = utils.simulate_retirement_planning(
                    current_age=self.current_age.value(),
                    retirement_age=self.retirement_age.value(),
                    current_savings=self.current_savings.value(),
                    monthly_contribution=self.monthly_contrib.value(),
                    annual_return=self.return_rate.value() / 100,
                    withdrawal_rate=self.withdrawal_rate.value() / 100
                )
                
                results_text = f"""RETIREMENT PLANNING SIMULATION
{'=' * 40}

PARAMETERS:
• Current Age:           {self.current_age.value()} years
• Retirement Age:        {self.retirement_age.value()} years
• Current Savings:       ${self.current_savings.value():,.2f}
• Monthly Contribution:  ${self.monthly_contrib.value():,.2f}
• Annual Return:         {self.return_rate.value():.2f}%
• Withdrawal Rate:       {self.withdrawal_rate.value():.2f}%

RESULTS:
• Savings at Retirement: ${result['retirement_balance']:,.2f}
• Annual Withdrawal:     ${result['annual_withdrawal']:,.2f}
• Monthly Withdrawal:    ${result['monthly_withdrawal']:,.2f}
• Total Contributions:   ${result['total_contributions']:,.2f}
• Investment Growth:     ${result['retirement_balance'] - result['total_contributions']:,.2f}
• Years to Retirement:   {result['years_to_retirement']} years

ANALYSIS:
• Income Replacement:    {(result['annual_withdrawal'] / (self.monthly_contrib.value() * 12)) * 100:.1f}%
• Nest Egg Multiple:     {result['retirement_balance'] / (self.monthly_contrib.value() * 12):.1f}x annual contribution
"""
                
            elif sim_type == "Loan Payment":
                result = utils.simulate_loan_payment(
                    loan_amount=self.loan_amount.value(),
                    annual_rate=self.loan_rate.value() / 100,
                    years=self.loan_years.value()
                )
                
                results_text = f"""LOAN PAYMENT SIMULATION
{'=' * 40}

PARAMETERS:
• Loan Amount:           ${self.loan_amount.value():,.2f}
• Annual Interest Rate:  {self.loan_rate.value():.2f}%
• Loan Term:             {self.loan_years.value()} years

RESULTS:
• Monthly Payment:       ${result['monthly_payment']:,.2f}
• Total Interest:        ${result['total_interest']:,.2f}
• Total Paid:            ${result['total_paid']:,.2f}
• Interest Percentage:   {(result['total_interest'] / self.loan_amount.value()) * 100:.1f}%

PAYMENT BREAKDOWN:
• First Payment Interest: ${result['first_payment_interest']:,.2f}
• First Payment Principal: ${result['first_payment_principal']:,.2f}
• Last Payment Interest:  ${result['last_payment_interest']:,.2f}
• Last Payment Principal: ${result['last_payment_principal']:,.2f}

EARLY PAYOFF ANALYSIS:
• Extra $100/month saves: ${result.get('extra_payment_savings', 0):,.2f}
• Time saved:            {result.get('time_saved_months', 0)} months
"""
            
            self.sim_results.setText(results_text)
            self.sim_status.setText("Simulation completed successfully")
            
        except Exception as e:
            error_msg = f"Simulation failed: {str(e)}"
            self.sim_status.setText(error_msg)
            QMessageBox.critical(self, "Simulation Error", error_msg)
            logger.error(f"Simulation failed: {e}")
    
    def _analyze_expenses(self):
        """Analyze expense patterns."""
        if not self.personal_finance:
            QMessageBox.warning(self, "Error", "Personal Finance service not available")
            return
        
        try:
            expenses = self.personal_finance.get_all_expenses()
            
            if not expenses:
                self.analysis_content.setText("No expense data available for analysis.")
                return
            
            # Perform analysis
            total_expenses = sum(exp['amount'] for exp in expenses)
            avg_expense = total_expenses / len(expenses)
            
            # Category breakdown
            categories = {}
            for exp in expenses:
                cat = exp.get('category', 'Other')
                categories[cat] = categories.get(cat, 0) + exp['amount']
            
            # Monthly trends
            monthly_totals = {}
            for exp in expenses:
                month = exp['date'][:7]  # YYYY-MM
                monthly_totals[month] = monthly_totals.get(month, 0) + exp['amount']
            
            analysis_text = f"""EXPENSE ANALYSIS
{'=' * 40}

OVERVIEW:
• Total Expenses:        ${total_expenses:,.2f}
• Number of Transactions: {len(expenses)}
• Average per Transaction: ${avg_expense:.2f}
• Date Range:            {min(exp['date'] for exp in expenses)} to {max(exp['date'] for exp in expenses)}

CATEGORY BREAKDOWN:
"""
            for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (amount / total_expenses) * 100
                analysis_text += f"• {cat:<20}: ${amount:>8,.2f} ({percentage:>5.1f}%)\n"
            
            analysis_text += f"\nMONTHLY TRENDS:\n"
            for month in sorted(monthly_totals.keys()):
                analysis_text += f"• {month}: ${monthly_totals[month]:,.2f}\n"
            
            self.analysis_content.setText(analysis_text)
            
        except Exception as e:
            error_msg = f"Expense analysis failed: {str(e)}"
            QMessageBox.critical(self, "Analysis Error", error_msg)
            logger.error(f"Expense analysis failed: {e}")
    
    def _analyze_trading(self):
        """Analyze trading performance."""
        if not self.trading_journal:
            QMessageBox.warning(self, "Error", "Trading Journal service not available")
            return
        
        try:
            trades = self.trading_journal.get_all_trades()
            
            if not trades:
                self.analysis_content.setText("No trading data available for analysis.")
                return
            
            # Calculate basic metrics
            total_trades = len(trades)
            buy_trades = [t for t in trades if t['trade_type'] in ['buy', 'cover']]
            sell_trades = [t for t in trades if t['trade_type'] in ['sell', 'short']]
            
            # Symbol analysis
            symbols = {}
            for trade in trades:
                symbol = trade['symbol']
                if symbol not in symbols:
                    symbols[symbol] = {'count': 0, 'volume': 0}
                symbols[symbol]['count'] += 1
                symbols[symbol]['volume'] += trade['entry_price'] * trade['quantity']
            
            analysis_text = f"""TRADING ANALYSIS
{'=' * 40}

OVERVIEW:
• Total Trades:          {total_trades}
• Buy/Cover Trades:      {len(buy_trades)}
• Sell/Short Trades:     {len(sell_trades)}
• Unique Symbols:        {len(symbols)}

TOP SYMBOLS BY VOLUME:
"""
            for symbol, data in sorted(symbols.items(), key=lambda x: x[1]['volume'], reverse=True)[:10]:
                analysis_text += f"• {symbol:<8}: {data['count']:>3} trades, ${data['volume']:>10,.2f} volume\n"
            
            # Asset type breakdown
            asset_types = {}
            for trade in trades:
                asset_type = trade.get('asset_type', 'Unknown')
                asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
            
            analysis_text += f"\nASSET TYPE BREAKDOWN:\n"
            for asset_type, count in sorted(asset_types.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_trades) * 100
                analysis_text += f"• {asset_type:<12}: {count:>3} trades ({percentage:>5.1f}%)\n"
            
            self.analysis_content.setText(analysis_text)
            
        except Exception as e:
            error_msg = f"Trading analysis failed: {str(e)}"
            QMessageBox.critical(self, "Analysis Error", error_msg)
            logger.error(f"Trading analysis failed: {e}")
    
    def _analyze_portfolio(self):
        """Analyze portfolio composition."""
        if not self.open_positions:
            QMessageBox.warning(self, "Error", "Open Positions service not available")
            return
        
        try:
            positions = self.open_positions.get_all_positions()
            
            if not positions:
                self.analysis_content.setText("No portfolio data available for analysis.")
                return
            
            # Calculate portfolio metrics
            total_value = sum(pos['entry_price'] * pos['quantity'] for pos in positions)
            
            # Asset allocation
            allocations = {}
            for pos in positions:
                asset_type = pos['asset_type']
                value = pos['entry_price'] * pos['quantity']
                allocations[asset_type] = allocations.get(asset_type, 0) + value
            
            # Position sizes
            position_values = []
            for pos in positions:
                value = pos['entry_price'] * pos['quantity']
                position_values.append({
                    'symbol': pos['symbol'],
                    'value': value,
                    'percentage': (value / total_value) * 100
                })
            
            position_values.sort(key=lambda x: x['value'], reverse=True)
            
            analysis_text = f"""PORTFOLIO ANALYSIS
{'=' * 40}

OVERVIEW:
• Total Positions:       {len(positions)}
• Total Portfolio Value: ${total_value:,.2f}
• Average Position Size: ${total_value / len(positions):,.2f}

ASSET ALLOCATION:
"""
            for asset_type, value in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
                percentage = (value / total_value) * 100
                analysis_text += f"• {asset_type.upper():<12}: ${value:>10,.2f} ({percentage:>5.1f}%)\n"
            
            analysis_text += f"\nTOP POSITIONS:\n"
            for pos in position_values[:10]:
                analysis_text += f"• {pos['symbol']:<8}: ${pos['value']:>10,.2f} ({pos['percentage']:>5.1f}%)\n"
            
            # Concentration analysis
            top_5_percentage = sum(pos['percentage'] for pos in position_values[:5])
            analysis_text += f"\nCONCENTRATION ANALYSIS:\n"
            analysis_text += f"• Top 5 positions:       {top_5_percentage:.1f}% of portfolio\n"
            analysis_text += f"• Diversification score: {100 - top_5_percentage:.1f}/100\n"
            
            self.analysis_content.setText(analysis_text)
            
        except Exception as e:
            error_msg = f"Portfolio analysis failed: {str(e)}"
            QMessageBox.critical(self, "Analysis Error", error_msg)
            logger.error(f"Portfolio analysis failed: {e}")
    
    def _check_business_logic_available(self):
        """Check if required business logic services are available."""
        if not any([self.personal_finance, self.trading_journal, self.open_positions]):
            QMessageBox.warning(
                self, 
                "Services Unavailable", 
                "No business logic services are available. Please ensure the application is properly initialized."
            )
            return False
        return True
    
    def refresh_data(self):
        """Refresh all visualization data."""
        # Clear current displays
        self._clear_chart()
        self.sim_results.clear()
        self.analysis_content.clear()
        
        logger.info("Visualizations page data refreshed") 