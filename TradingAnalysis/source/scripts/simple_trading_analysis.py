#!/usr/bin/env python3
"""
Simple Trading Analysis (No Visualization Dependencies)
Basic analysis and reporting of trading performance data without matplotlib/seaborn.

Usage:
    python simple_trading_analysis.py
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path

class SimpleTradingAnalyzer:
    def __init__(self, csv_path):
        """Initialize the analyzer with trading data from CSV file."""
        self.csv_path = csv_path
        self.df = None
        self.processed_df = None
        self.output_dir = Path(__file__).parent.parent / "output"
        self.output_dir.mkdir(exist_ok=True)

    def load_and_process_data(self):
        """Load and process the trading data."""
        print("Loading and processing trading data...")

        # Load data
        self.df = pd.read_csv(self.csv_path)
        self.df['Time'] = pd.to_datetime(self.df['Time'])
        self.df = self.df.sort_values('Time').reset_index(drop=True)

        # Parse action details
        self.df['Position_Type'] = ''
        self.df['Symbol'] = ''
        self.df['Price'] = 0.0
        self.df['Quantity'] = 0
        self.df['Avg_Price'] = 0.0
        self.df['Exchange'] = ''

        for idx, action in enumerate(self.df['Action']):
            # Extract position type
            if 'Close long' in action:
                self.df.at[idx, 'Position_Type'] = 'Long'
            elif 'Close short' in action:
                self.df.at[idx, 'Position_Type'] = 'Short'

            # Extract symbol
            symbol_match = re.search(r'symbol ([A-Z]+:[A-Z]+)', action)
            if symbol_match:
                exchange, symbol = symbol_match.group(1).split(':')
                self.df.at[idx, 'Symbol'] = symbol
                self.df.at[idx, 'Exchange'] = exchange

            # Extract price and quantity
            price_match = re.search(r'at price ([0-9]+\.?[0-9]*)', action)
            if price_match:
                self.df.at[idx, 'Price'] = float(price_match.group(1))

            quantity_match = re.search(r'for ([0-9]+) units', action)
            if quantity_match:
                self.df.at[idx, 'Quantity'] = int(quantity_match.group(1))

            avg_price_match = re.search(r'AVG Price was ([0-9]+\.?[0-9]*)', action)
            if avg_price_match:
                self.df.at[idx, 'Avg_Price'] = float(avg_price_match.group(1))

        # Calculate metrics
        self.df['Trade_Value'] = self.df['Price'] * self.df['Quantity']
        self.df['P&L_Percentage'] = (self.df['Realized P&L (value)'] /
                                    (self.df['Avg_Price'] * self.df['Quantity'])) * 100
        self.df['Date'] = self.df['Time'].dt.date
        self.df['Is_Winner'] = self.df['Realized P&L (value)'] > 0

        self.processed_df = self.df.copy()
        print(f"Processed {len(self.df)} trades")

    def calculate_metrics(self):
        """Calculate trading performance metrics."""
        df = self.processed_df

        return {
            'total_trades': len(df),
            'winning_trades': len(df[df['Is_Winner']]),
            'losing_trades': len(df[~df['Is_Winner']]),
            'win_rate': len(df[df['Is_Winner']]) / len(df) * 100,
            'total_pnl': df['Realized P&L (value)'].sum(),
            'avg_win': df[df['Is_Winner']]['Realized P&L (value)'].mean() if len(df[df['Is_Winner']]) > 0 else 0,
            'avg_loss': df[~df['Is_Winner']]['Realized P&L (value)'].mean() if len(df[~df['Is_Winner']]) > 0 else 0,
            'largest_win': df['Realized P&L (value)'].max(),
            'largest_loss': df['Realized P&L (value)'].min(),
            'profit_factor': (df[df['Is_Winner']]['Realized P&L (value)'].sum() /
                            abs(df[~df['Is_Winner']]['Realized P&L (value)'].sum())) if len(df[~df['Is_Winner']]) > 0 else float('inf'),
            'starting_balance': df['Balance Before'].iloc[0],
            'ending_balance': df['Balance After'].iloc[-1],
            'total_return': df['Balance After'].iloc[-1] - df['Balance Before'].iloc[0],
            'return_percentage': ((df['Balance After'].iloc[-1] / df['Balance Before'].iloc[0]) - 1) * 100
        }

    def get_best_trades(self, top_n=10):
        """Get best performing trades."""
        df = self.processed_df

        return {
            'best_absolute': df.nlargest(top_n, 'Realized P&L (value)')[
                ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Realized P&L (value)', 'P&L_Percentage']
            ],
            'best_percentage': df.nlargest(top_n, 'P&L_Percentage')[
                ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Realized P&L (value)', 'P&L_Percentage']
            ],
            'worst_trades': df.nsmallest(top_n, 'Realized P&L (value)')[
                ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Realized P&L (value)', 'P&L_Percentage']
            ]
        }

    def analyze_by_symbol(self):
        """Analyze performance by symbol."""
        df = self.processed_df

        symbol_analysis = df.groupby('Symbol').agg({
            'Realized P&L (value)': ['count', 'sum', 'mean'],
            'Is_Winner': 'mean',
            'Quantity': 'sum'
        }).round(2)

        symbol_analysis.columns = ['Trade_Count', 'Total_PnL', 'Avg_PnL', 'Win_Rate', 'Total_Shares']
        return symbol_analysis.sort_values('Total_PnL', ascending=False)

    def generate_report(self):
        """Generate comprehensive text report."""
        metrics = self.calculate_metrics()
        best_trades = self.get_best_trades()
        symbol_analysis = self.analyze_by_symbol()

        # Console output
        print("\n" + "="*60)
        print("TRADING PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Winning Trades: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
        print(f"Losing Trades: {metrics['losing_trades']}")
        print()
        print(f"Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"Average Win: ${metrics['avg_win']:,.2f}")
        print(f"Average Loss: ${metrics['avg_loss']:,.2f}")
        print(f"Largest Win: ${metrics['largest_win']:,.2f}")
        print(f"Largest Loss: ${metrics['largest_loss']:,.2f}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print()
        print(f"Starting Balance: ${metrics['starting_balance']:,.2f}")
        print(f"Ending Balance: ${metrics['ending_balance']:,.2f}")
        print(f"Total Return: ${metrics['total_return']:,.2f} ({metrics['return_percentage']:.2f}%)")

        print("\n" + "="*60)
        print("TOP PERFORMING SYMBOLS")
        print("="*60)
        print(symbol_analysis.head(10))

        print("\n" + "="*60)
        print("BEST TRADES BY ABSOLUTE P&L")
        print("="*60)
        print(best_trades['best_absolute'])

        # Save detailed report
        report_file = self.output_dir / "simple_analysis_report.txt"
        with open(report_file, 'w') as f:
            f.write("SIMPLE TRADING ANALYSIS REPORT\n")
            f.write("="*60 + "\n\n")

            f.write("PERFORMANCE METRICS\n")
            f.write("-"*30 + "\n")
            for key, value in metrics.items():
                if isinstance(value, float):
                    f.write(f"{key}: {value:,.2f}\n")
                else:
                    f.write(f"{key}: {value:,}\n")

            f.write(f"\n\nSYMBOL ANALYSIS\n")
            f.write("-"*30 + "\n")
            f.write(symbol_analysis.to_string())

            f.write(f"\n\nBEST TRADES (Absolute P&L)\n")
            f.write("-"*30 + "\n")
            f.write(best_trades['best_absolute'].to_string())

            f.write(f"\n\nBEST TRADES (Percentage)\n")
            f.write("-"*30 + "\n")
            f.write(best_trades['best_percentage'].to_string())

            f.write(f"\n\nWORST TRADES\n")
            f.write("-"*30 + "\n")
            f.write(best_trades['worst_trades'].to_string())

        print(f"\n\nDetailed report saved to: {report_file}")

        # Save CSV exports
        csv_dir = self.output_dir / "csv_exports"
        csv_dir.mkdir(exist_ok=True)

        symbol_analysis.to_csv(csv_dir / "symbol_analysis.csv")
        best_trades['best_absolute'].to_csv(csv_dir / "best_trades_absolute.csv", index=False)
        best_trades['best_percentage'].to_csv(csv_dir / "best_trades_percentage.csv", index=False)
        self.processed_df.to_csv(csv_dir / "processed_trades.csv", index=False)

        print(f"CSV exports saved to: {csv_dir}")

def main():
    """Main execution function."""
    csv_path = Path(__file__).parent.parent / "data" / "2025" / "trades.csv"

    print("Simple Trading Analysis Tool")
    print("="*40)

    try:
        analyzer = SimpleTradingAnalyzer(csv_path)
        analyzer.load_and_process_data()
        analyzer.generate_report()

        print("\nAnalysis complete!")

    except FileNotFoundError:
        print(f"ERROR: Could not find {csv_path}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()