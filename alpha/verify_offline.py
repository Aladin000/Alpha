#!/usr/bin/env python3
"""
verify_offline.py

Verification script to confirm Alpha can run completely offline
and all necessary dependencies are available locally.
"""

import sys
import sqlite3
from pathlib import Path

def check_offline_status():
    """Comprehensive offline capability check"""
    print("🔍 ALPHA OFFLINE VERIFICATION")
    print("=" * 50)
    
    checks = {
        "✅ Core Dependencies": verify_core_dependencies(),
        "✅ GUI Framework": verify_gui_framework(),
        "✅ Data Processing": verify_data_processing(),
        "✅ Visualization": verify_visualization(),
        "✅ Database": verify_database(),
        "✅ Configuration": verify_configuration(),
        "✅ Export Capabilities": verify_export(),
        "✅ Mathematical Operations": verify_math_operations(),
    }
    
    print("\nOFFLINE CAPABILITY SUMMARY:")
    print("-" * 30)
    
    all_passed = True
    for check_name, result in checks.items():
        status = "READY" if result else "ISSUE"
        print(f"{check_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 FULLY OFFLINE CAPABLE!")
        print("\nYou can now work completely offline with:")
        print("• Full GUI application")
        print("• Local database operations")
        print("• Data visualization and charts")
        print("• Financial calculations")
        print("• Excel/CSV export")
        print("• Complete application functionality")
        print("\nNo internet connection required for core features!")
    else:
        print("⚠️  Some offline capabilities may be limited")
    
    return all_passed

def verify_core_dependencies():
    """Check core Python dependencies"""
    try:
        import pandas
        import numpy
        import yaml
        from pathlib import Path
        return True
    except ImportError:
        return False

def verify_gui_framework():
    """Check GUI framework availability"""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        return True
    except ImportError:
        return False

def verify_data_processing():
    """Check data processing capabilities"""
    try:
        import pandas as pd
        import numpy as np
        
        # Test basic operations
        df = pd.DataFrame({'test': [1, 2, 3]})
        arr = np.array([1, 2, 3])
        
        # Test calculations
        result = df['test'].sum() + arr.mean()
        return result == 8.0
    except:
        return False

def verify_visualization():
    """Check visualization libraries"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pyqtgraph as pg
        import plotly.graph_objects as go
        
        # Test basic plot creation (without display)
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])
        plt.close(fig)
        
        return True
    except:
        return False

def verify_database():
    """Check database operations"""
    try:
        # Test in-memory database
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE test_finances (
                id INTEGER PRIMARY KEY,
                date TEXT,
                amount REAL,
                category TEXT
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO test_finances (date, amount, category)
            VALUES (?, ?, ?)
        ''', ('2024-01-01', 100.50, 'Income'))
        
        # Query data
        cursor.execute('SELECT * FROM test_finances')
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    except:
        return False

def verify_configuration():
    """Check configuration file access"""
    try:
        config_path = Path('config.yaml')
        if not config_path.exists():
            return False
            
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['app', 'database', 'ui', 'finance']
        return all(section in config for section in required_sections)
    except:
        return False

def verify_export():
    """Check data export capabilities"""
    try:
        import pandas as pd
        import openpyxl
        import xlsxwriter
        from io import StringIO, BytesIO
        
        # Test CSV export
        df = pd.DataFrame({'date': ['2024-01-01'], 'amount': [100.0]})
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        # Test Excel export
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, engine='openpyxl')
        
        return len(csv_buffer.getvalue()) > 0 and len(excel_buffer.getvalue()) > 0
    except:
        return False

def verify_math_operations():
    """Check mathematical and financial calculations"""
    try:
        import numpy as np
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Test financial calculations
        principal = 1000
        rate = 0.05
        time = 2
        
        # Simple interest
        simple_interest = principal * rate * time
        
        # Compound interest
        compound_interest = principal * (1 + rate) ** time - principal
        
        # P&L calculation
        entry_price = 100.0
        current_price = 105.0
        quantity = 10
        pnl = (current_price - entry_price) * quantity
        
        # Date calculations
        start_date = datetime(2024, 1, 1)
        end_date = start_date + timedelta(days=365)
        
        return all([
            simple_interest == 100.0,
            abs(compound_interest - 102.5) < 0.01,
            pnl == 50.0,
            (end_date - start_date).days == 365
        ])
    except:
        return False

if __name__ == "__main__":
    check_offline_status() 