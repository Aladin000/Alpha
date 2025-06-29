"""
utils.py

This module contains miscellaneous helper functions for the alpha application.
Includes data visualization functions, financial simulation logic, and shared utilities.
Provides modular, reusable functions for charts and financial calculations.
"""

import logging
import math
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class UtilsError(Exception):
    """Custom exception for utility operations."""
    pass


# ==================== VISUALIZATION FUNCTIONS ====================

def plot_expenses_over_time(data: List[Dict[str, Any]], 
                           save_path: Optional[str] = None,
                           title: str = "Expenses Over Time") -> Figure:
    """
    Plot expenses over time as a line chart with optional category breakdown.
    
    Args:
        data (list): List of expense dictionaries with 'date', 'amount', and 'category' keys
        save_path (str, optional): Path to save the plot image
        title (str): Chart title
        
    Returns:
        Figure: Matplotlib figure object
        
    Raises:
        UtilsError: If data is invalid or plotting fails
    """
    if not data:
        raise UtilsError("Expense data cannot be empty")
    
    try:
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Parse dates and amounts
        dates = []
        amounts = []
        categories = {}
        
        for expense in data:
            if 'date' not in expense or 'amount' not in expense:
                continue
                
            try:
                date = datetime.strptime(expense['date'], '%Y-%m-%d')
                amount = float(expense['amount'])
                category = expense.get('category', 'Other')
                
                dates.append(date)
                amounts.append(amount)
                
                # Group by category for breakdown
                if category not in categories:
                    categories[category] = {'dates': [], 'amounts': []}
                categories[category]['dates'].append(date)
                categories[category]['amounts'].append(amount)
                
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid expense data: {e}")
                continue
        
        if not dates:
            raise UtilsError("No valid expense data found")
        
        # Sort by date
        sorted_data = sorted(zip(dates, amounts))
        dates, amounts = zip(*sorted_data)
        
        # Plot main line
        ax.plot(dates, amounts, marker='o', linewidth=2, markersize=4, 
                color='#e74c3c', label='Daily Expenses')
        
        # Add category breakdown if multiple categories
        if len(categories) > 1:
            colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
            for i, (category, cat_data) in enumerate(categories.items()):
                if len(cat_data['dates']) > 1:
                    sorted_cat = sorted(zip(cat_data['dates'], cat_data['amounts']))
                    cat_dates, cat_amounts = zip(*sorted_cat)
                    ax.plot(cat_dates, cat_amounts, marker='s', linewidth=1, 
                           markersize=3, alpha=0.7, color=colors[i], label=category)
        
        # Formatting
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Amount ($)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Format x-axis dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add summary stats
        total = sum(amounts)
        avg = total / len(amounts)
        ax.text(0.02, 0.98, f'Total: ${total:.2f}\nAverage: ${avg:.2f}', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Expense chart saved to {save_path}")
        
        return fig
        
    except Exception as e:
        raise UtilsError(f"Failed to create expense chart: {str(e)}")


def plot_savings_growth(data: List[Dict[str, Any]], 
                       save_path: Optional[str] = None,
                       title: str = "Savings Growth Over Time") -> Figure:
    """
    Plot cumulative savings growth over time.
    
    Args:
        data (list): List of savings dictionaries with 'date' and 'amount' keys
        save_path (str, optional): Path to save the plot image
        title (str): Chart title
        
    Returns:
        Figure: Matplotlib figure object
        
    Raises:
        UtilsError: If data is invalid or plotting fails
    """
    if not data:
        raise UtilsError("Savings data cannot be empty")
    
    try:
        # Create figure and axis
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Parse and sort data
        parsed_data = []
        for savings in data:
            if 'date' not in savings or 'amount' not in savings:
                continue
                
            try:
                date = datetime.strptime(savings['date'], '%Y-%m-%d')
                amount = float(savings['amount'])
                source = savings.get('source', 'Other')
                parsed_data.append((date, amount, source))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid savings data: {e}")
                continue
        
        if not parsed_data:
            raise UtilsError("No valid savings data found")
        
        # Sort by date
        parsed_data.sort()
        
        # Calculate cumulative savings
        dates = [item[0] for item in parsed_data]
        amounts = [item[1] for item in parsed_data]
        sources = [item[2] for item in parsed_data]
        
        cumulative = []
        running_total = 0
        for amount in amounts:
            running_total += amount
            cumulative.append(running_total)
        
        # Plot 1: Cumulative savings
        ax1.plot(dates, cumulative, marker='o', linewidth=3, markersize=5, 
                color='#27ae60', label='Cumulative Savings')
        ax1.fill_between(dates, cumulative, alpha=0.3, color='#27ae60')
        
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative Amount ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add growth rate annotation
        if len(cumulative) > 1:
            total_growth = cumulative[-1] - cumulative[0]
            days_diff = (dates[-1] - dates[0]).days
            if days_diff > 0:
                daily_rate = total_growth / days_diff
                ax1.text(0.02, 0.98, f'Total Growth: ${total_growth:.2f}\nDaily Rate: ${daily_rate:.2f}',
                        transform=ax1.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
        
        # Plot 2: Monthly savings breakdown
        ax2.bar(dates, amounts, color='#3498db', alpha=0.7, label='Monthly Savings')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Amount ($)', fontsize=12)
        ax2.set_title('Monthly Savings Contributions', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # Format x-axis dates for both plots
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Savings growth chart saved to {save_path}")
        
        return fig
        
    except Exception as e:
        raise UtilsError(f"Failed to create savings growth chart: {str(e)}")


def plot_pnl_history(data: List[Dict[str, Any]], 
                     save_path: Optional[str] = None,
                     title: str = "P&L History") -> Figure:
    """
    Plot profit and loss history over time with performance metrics.
    
    Args:
        data (list): List of P&L dictionaries with 'date', 'pnl', and 'symbol' keys
        save_path (str, optional): Path to save the plot image
        title (str): Chart title
        
    Returns:
        Figure: Matplotlib figure object
        
    Raises:
        UtilsError: If data is invalid or plotting fails
    """
    if not data:
        raise UtilsError("P&L data cannot be empty")
    
    try:
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Parse data
        parsed_data = []
        symbols = set()
        
        for pnl_entry in data:
            if 'date' not in pnl_entry or 'pnl' not in pnl_entry:
                continue
                
            try:
                date = datetime.strptime(pnl_entry['date'], '%Y-%m-%d')
                pnl = float(pnl_entry['pnl'])
                symbol = pnl_entry.get('symbol', 'Portfolio')
                symbols.add(symbol)
                parsed_data.append((date, pnl, symbol))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping invalid P&L data: {e}")
                continue
        
        if not parsed_data:
            raise UtilsError("No valid P&L data found")
        
        # Sort by date
        parsed_data.sort()
        
        # Plot 1: Cumulative P&L
        dates = [item[0] for item in parsed_data]
        pnls = [item[1] for item in parsed_data]
        
        cumulative_pnl = []
        running_total = 0
        for pnl in pnls:
            running_total += pnl
            cumulative_pnl.append(running_total)
        
        # Color based on performance
        colors = ['#27ae60' if p >= 0 else '#e74c3c' for p in cumulative_pnl]
        
        ax1.plot(dates, cumulative_pnl, linewidth=3, color='#2980b9', label='Cumulative P&L')
        ax1.fill_between(dates, cumulative_pnl, 0, alpha=0.3, 
                        where=[p >= 0 for p in cumulative_pnl], color='#27ae60', label='Profit')
        ax1.fill_between(dates, cumulative_pnl, 0, alpha=0.3,
                        where=[p < 0 for p in cumulative_pnl], color='#e74c3c', label='Loss')
        
        ax1.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax1.set_title(title, fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative P&L ($)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Add performance stats
        total_pnl = cumulative_pnl[-1] if cumulative_pnl else 0
        winning_days = sum(1 for p in pnls if p > 0)
        total_days = len(pnls)
        win_rate = (winning_days / total_days * 100) if total_days > 0 else 0
        
        stats_text = f'Total P&L: ${total_pnl:.2f}\nWin Rate: {win_rate:.1f}%\nWinning Days: {winning_days}/{total_days}'
        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # Plot 2: Daily P&L
        colors_daily = ['#27ae60' if p >= 0 else '#e74c3c' for p in pnls]
        ax2.bar(dates, pnls, color=colors_daily, alpha=0.7, label='Daily P&L')
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.8)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Daily P&L ($)', fontsize=12)
        ax2.set_title('Daily P&L Breakdown', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis dates
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"P&L history chart saved to {save_path}")
        
        return fig
        
    except Exception as e:
        raise UtilsError(f"Failed to create P&L history chart: {str(e)}")


def plot_portfolio_allocation(data: List[Dict[str, Any]], 
                            save_path: Optional[str] = None,
                            title: str = "Portfolio Allocation") -> Figure:
    """
    Plot portfolio allocation as a pie chart.
    
    Args:
        data (list): List of position dictionaries with 'symbol' and 'current_value' keys
        save_path (str, optional): Path to save the plot image
        title (str): Chart title
        
    Returns:
        Figure: Matplotlib figure object
        
    Raises:
        UtilsError: If data is invalid or plotting fails
    """
    if not data:
        raise UtilsError("Portfolio data cannot be empty")
    
    try:
        # Create figure
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # Parse data by symbol
        symbols = {}
        asset_types = {}
        
        for position in data:
            if 'symbol' not in position or 'current_value' not in position:
                continue
                
            symbol = position['symbol']
            value = float(position.get('current_value', 0))
            asset_type = position.get('asset_type', 'Unknown')
            
            if value > 0:
                symbols[symbol] = symbols.get(symbol, 0) + value
                asset_types[asset_type] = asset_types.get(asset_type, 0) + value
        
        if not symbols:
            raise UtilsError("No valid portfolio data found")
        
        # Plot 1: By Symbol
        labels1 = list(symbols.keys())
        sizes1 = list(symbols.values())
        colors1 = plt.cm.Set3(np.linspace(0, 1, len(labels1)))
        
        wedges1, texts1, autotexts1 = ax1.pie(sizes1, labels=labels1, colors=colors1, autopct='%1.1f%%',
                                             startangle=90, textprops={'fontsize': 10})
        ax1.set_title(f'{title} - By Symbol', fontsize=12, fontweight='bold')
        
        # Plot 2: By Asset Type
        labels2 = list(asset_types.keys())
        sizes2 = list(asset_types.values())
        colors2 = plt.cm.Pastel1(np.linspace(0, 1, len(labels2)))
        
        wedges2, texts2, autotexts2 = ax2.pie(sizes2, labels=labels2, colors=colors2, autopct='%1.1f%%',
                                             startangle=90, textprops={'fontsize': 10})
        ax2.set_title(f'{title} - By Asset Type', fontsize=12, fontweight='bold')
        
        # Add total value
        total_value = sum(sizes1)
        fig.suptitle(f'Total Portfolio Value: ${total_value:,.2f}', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            fig.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Portfolio allocation chart saved to {save_path}")
        
        return fig
        
    except Exception as e:
        raise UtilsError(f"Failed to create portfolio allocation chart: {str(e)}")


# ==================== SIMULATION FUNCTIONS ====================

def simulate_savings_growth(initial: float, monthly: float, annual_rate: float, 
                          periods: int) -> List[float]:
    """
    Simulate savings growth over time with compound interest.
    
    Args:
        initial (float): Initial savings amount
        monthly (float): Monthly contribution
        annual_rate (float): Annual interest rate (as decimal, e.g., 0.05 for 5%)
        periods (int): Number of periods (months)
        
    Returns:
        list: List of savings values over time
        
    Raises:
        UtilsError: If parameters are invalid
    """
    if initial < 0:
        raise UtilsError("Initial amount cannot be negative")
    if monthly < 0:
        raise UtilsError("Monthly contribution cannot be negative")
    if annual_rate < 0:
        raise UtilsError("Interest rate cannot be negative")
    if periods <= 0:
        raise UtilsError("Periods must be positive")
    
    try:
        monthly_rate = annual_rate / 12  # Convert annual rate to monthly
        values = [initial]
        current_value = initial
        
        for period in range(1, periods + 1):
            # Add monthly contribution
            current_value += monthly
            # Apply monthly interest
            current_value *= (1 + monthly_rate)
            values.append(current_value)
        
        logger.info(f"Simulated {periods} periods: ${initial:.2f} → ${values[-1]:.2f}")
        return values
        
    except Exception as e:
        raise UtilsError(f"Failed to simulate savings growth: {str(e)}")


def simulate_compound_interest(principal: float, annual_rate: float, 
                             times_per_year: int, years: float) -> float:
    """
    Calculate compound interest over time.
    
    Args:
        principal (float): Initial principal amount
        annual_rate (float): Annual interest rate (as decimal)
        times_per_year (int): Number of compounding periods per year
        years (float): Number of years
        
    Returns:
        float: Final amount after compound interest
        
    Raises:
        UtilsError: If parameters are invalid
    """
    if principal < 0:
        raise UtilsError("Principal cannot be negative")
    if annual_rate < 0:
        raise UtilsError("Interest rate cannot be negative")
    if times_per_year <= 0:
        raise UtilsError("Compounding frequency must be positive")
    if years < 0:
        raise UtilsError("Years cannot be negative")
    
    try:
        # Compound interest formula: A = P(1 + r/n)^(nt)
        amount = principal * (1 + annual_rate / times_per_year) ** (times_per_year * years)
        
        logger.info(f"Compound interest: ${principal:.2f} → ${amount:.2f} over {years} years")
        return amount
        
    except Exception as e:
        raise UtilsError(f"Failed to calculate compound interest: {str(e)}")


def simulate_retirement_planning(current_age: int, retirement_age: int, 
                               current_savings: float, monthly_contribution: float,
                               annual_return: float, withdrawal_rate: float) -> Dict[str, Any]:
    """
    Simulate retirement planning with savings growth and withdrawal phase.
    
    Args:
        current_age (int): Current age
        retirement_age (int): Target retirement age
        current_savings (float): Current savings amount
        monthly_contribution (float): Monthly contribution until retirement
        annual_return (float): Expected annual return (as decimal)
        withdrawal_rate (float): Annual withdrawal rate in retirement (as decimal)
        
    Returns:
        dict: Retirement planning analysis
        
    Raises:
        UtilsError: If parameters are invalid
    """
    if current_age >= retirement_age:
        raise UtilsError("Retirement age must be greater than current age")
    if current_savings < 0:
        raise UtilsError("Current savings cannot be negative")
    if monthly_contribution < 0:
        raise UtilsError("Monthly contribution cannot be negative")
    if annual_return < 0:
        raise UtilsError("Annual return cannot be negative")
    if withdrawal_rate <= 0 or withdrawal_rate > 1:
        raise UtilsError("Withdrawal rate must be between 0 and 1")
    
    try:
        # Savings phase
        years_to_retirement = retirement_age - current_age
        months_to_retirement = years_to_retirement * 12
        
        savings_growth = simulate_savings_growth(
            current_savings, monthly_contribution, annual_return, months_to_retirement
        )
        
        retirement_balance = savings_growth[-1]
        
        # Withdrawal phase calculation
        annual_withdrawal = retirement_balance * withdrawal_rate
        monthly_withdrawal = annual_withdrawal / 12
        
        # Estimate how long money will last
        balance = retirement_balance
        years_lasting = 0
        monthly_return = annual_return / 12
        
        while balance > 0 and years_lasting < 50:  # Cap at 50 years
            balance = balance * (1 + monthly_return) - monthly_withdrawal
            years_lasting += 1/12
        
        result = {
            'years_to_retirement': years_to_retirement,
            'total_contributions': monthly_contribution * months_to_retirement,
            'retirement_balance': retirement_balance,
            'annual_withdrawal': annual_withdrawal,
            'monthly_withdrawal': monthly_withdrawal,
            'estimated_years_lasting': years_lasting,
            'savings_timeline': savings_growth
        }
        
        logger.info(f"Retirement simulation: ${retirement_balance:,.2f} at age {retirement_age}")
        return result
        
    except Exception as e:
        raise UtilsError(f"Failed to simulate retirement planning: {str(e)}")


def simulate_loan_payment(loan_amount: float, annual_rate: float, years: int) -> Dict[str, Any]:
    """
    Calculate loan payment schedule and total interest.
    
    Args:
        loan_amount (float): Principal loan amount
        annual_rate (float): Annual interest rate (as decimal)
        years (int): Loan term in years
        
    Returns:
        dict: Loan payment analysis
        
    Raises:
        UtilsError: If parameters are invalid
    """
    if loan_amount <= 0:
        raise UtilsError("Loan amount must be positive")
    if annual_rate < 0:
        raise UtilsError("Interest rate cannot be negative")
    if years <= 0:
        raise UtilsError("Loan term must be positive")
    
    try:
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            # No interest case
            monthly_payment = loan_amount / num_payments
            total_interest = 0
        else:
            # Standard loan payment formula
            monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
                            ((1 + monthly_rate) ** num_payments - 1)
            total_interest = (monthly_payment * num_payments) - loan_amount
        
        total_paid = loan_amount + total_interest
        
        result = {
            'loan_amount': loan_amount,
            'monthly_payment': monthly_payment,
            'total_interest': total_interest,
            'total_paid': total_paid,
            'num_payments': num_payments,
            'interest_rate_annual': annual_rate,
            'interest_rate_monthly': monthly_rate
        }
        
        logger.info(f"Loan calculation: ${loan_amount:,.2f} → ${monthly_payment:.2f}/month")
        return result
        
    except Exception as e:
        raise UtilsError(f"Failed to calculate loan payment: {str(e)}")


# ==================== UTILITY HELPER FUNCTIONS ====================

def generate_sample_data(data_type: str, num_records: int = 30) -> List[Dict[str, Any]]:
    """
    Generate sample data for testing visualization functions.
    
    Args:
        data_type (str): Type of data ('expenses', 'savings', 'pnl', 'positions')
        num_records (int): Number of records to generate
        
    Returns:
        list: Sample data in the appropriate format
        
    Raises:
        UtilsError: If data type is unsupported
    """
    if num_records <= 0:
        raise UtilsError("Number of records must be positive")
    
    try:
        import random
        
        base_date = datetime.now() - timedelta(days=num_records)
        sample_data = []
        
        if data_type == 'expenses':
            categories = ['Food & Dining', 'Transportation', 'Shopping', 'Bills', 'Entertainment']
            for i in range(num_records):
                date = base_date + timedelta(days=i)
                sample_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': round(random.uniform(10, 200), 2),
                    'category': random.choice(categories)
                })
        
        elif data_type == 'savings':
            sources = ['Salary', 'Freelance', 'Investment', 'Bonus']
            for i in range(num_records):
                date = base_date + timedelta(days=i * 7)  # Weekly savings
                sample_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'amount': round(random.uniform(100, 1000), 2),
                    'source': random.choice(sources)
                })
        
        elif data_type == 'pnl':
            symbols = ['AAPL', 'MSFT', 'BTC', 'SPY', 'TSLA']
            for i in range(num_records):
                date = base_date + timedelta(days=i)
                sample_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'pnl': round(random.uniform(-100, 150), 2),
                    'symbol': random.choice(symbols)
                })
        
        elif data_type == 'positions':
            positions = [
                ('AAPL', 'stock', 5000),
                ('BTC', 'crypto', 8000),
                ('SPY', 'etf', 3000),
                ('MSFT', 'stock', 4000),
                ('ETH', 'crypto', 2500)
            ]
            for symbol, asset_type, base_value in positions:
                sample_data.append({
                    'symbol': symbol,
                    'asset_type': asset_type,
                    'current_value': base_value + random.uniform(-500, 1000)
                })
        
        else:
            raise UtilsError(f"Unsupported data type: {data_type}")
        
        logger.info(f"Generated {len(sample_data)} sample {data_type} records")
        return sample_data
        
    except Exception as e:
        raise UtilsError(f"Failed to generate sample data: {str(e)}")


if __name__ == "__main__":
    """
    Demonstration of the utils functionality.
    This runs when the module is executed directly.
    """
    print("=" * 60)
    print("UTILS MODULE DEMONSTRATION")
    print("=" * 60)
    
    try:
        # Test data generation
        print("\n📊 GENERATING SAMPLE DATA")
        print("-" * 40)
        
        expense_data = generate_sample_data('expenses', 20)
        savings_data = generate_sample_data('savings', 15)
        pnl_data = generate_sample_data('pnl', 25)
        portfolio_data = generate_sample_data('positions', 5)
        
        print(f"✅ Generated {len(expense_data)} expense records")
        print(f"✅ Generated {len(savings_data)} savings records") 
        print(f"✅ Generated {len(pnl_data)} P&L records")
        print(f"✅ Generated {len(portfolio_data)} position records")
        
        # Test visualization functions
        print("\n📈 CREATING VISUALIZATIONS")
        print("-" * 40)
        
        # Create expense chart
        print("📊 Creating expense chart...")
        expense_fig = plot_expenses_over_time(expense_data, 'expense_chart.png')
        print("✅ Expense chart created and saved")
        
        # Create savings growth chart  
        print("💰 Creating savings growth chart...")
        savings_fig = plot_savings_growth(savings_data, 'savings_chart.png')
        print("✅ Savings growth chart created and saved")
        
        # Create P&L history chart
        print("📉 Creating P&L history chart...")
        pnl_fig = plot_pnl_history(pnl_data, 'pnl_chart.png')
        print("✅ P&L history chart created and saved")
        
        # Create portfolio allocation chart
        print("🥧 Creating portfolio allocation chart...")
        portfolio_fig = plot_portfolio_allocation(portfolio_data, 'portfolio_chart.png')
        print("✅ Portfolio allocation chart created and saved")
        
        # Test simulation functions
        print("\n🔮 RUNNING FINANCIAL SIMULATIONS")
        print("-" * 40)
        
        # Savings growth simulation
        print("💵 Savings Growth Simulation:")
        savings_projection = simulate_savings_growth(
            initial=10000,
            monthly=500, 
            annual_rate=0.07,
            periods=120  # 10 years
        )
        print(f"  Initial: $10,000")
        print(f"  Monthly: $500")
        print(f"  Rate: 7% annually")
        print(f"  After 10 years: ${savings_projection[-1]:,.2f}")
        
        # Compound interest simulation
        print("\n🏦 Compound Interest Simulation:")
        compound_result = simulate_compound_interest(
            principal=5000,
            annual_rate=0.06,
            times_per_year=12,
            years=15
        )
        print(f"  Principal: $5,000")
        print(f"  Rate: 6% annually (monthly compounding)")
        print(f"  After 15 years: ${compound_result:,.2f}")
        
        # Retirement planning simulation
        print("\n🏖️ Retirement Planning Simulation:")
        retirement_plan = simulate_retirement_planning(
            current_age=30,
            retirement_age=65,
            current_savings=25000,
            monthly_contribution=1000,
            annual_return=0.08,
            withdrawal_rate=0.04
        )
        print(f"  Current age: 30, Retirement age: 65")
        print(f"  Current savings: $25,000")
        print(f"  Monthly contribution: $1,000")
        print(f"  Expected return: 8%")
        print(f"  Retirement balance: ${retirement_plan['retirement_balance']:,.2f}")
        print(f"  Annual withdrawal: ${retirement_plan['annual_withdrawal']:,.2f}")
        print(f"  Money lasts: {retirement_plan['estimated_years_lasting']:.1f} years")
        
        # Loan payment simulation
        print("\n🏠 Loan Payment Simulation:")
        loan_analysis = simulate_loan_payment(
            loan_amount=300000,
            annual_rate=0.045,
            years=30
        )
        print(f"  Loan amount: $300,000")
        print(f"  Interest rate: 4.5%")
        print(f"  Term: 30 years")
        print(f"  Monthly payment: ${loan_analysis['monthly_payment']:.2f}")
        print(f"  Total interest: ${loan_analysis['total_interest']:,.2f}")
        print(f"  Total paid: ${loan_analysis['total_paid']:,.2f}")
        
        # Summary
        print("\n📋 SUMMARY")
        print("-" * 40)
        print("✅ All visualization functions working")
        print("✅ All simulation functions working")
        print("✅ Charts saved to disk")
        print("✅ Financial calculations completed")
        
        # Close figures to free memory
        plt.close('all')
        
    except Exception as e:
        print(f"❌ Error in demonstration: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Utils module demonstration completed!")
    print("The visualization and simulation functions are ready for use.")
    print("=" * 60) 