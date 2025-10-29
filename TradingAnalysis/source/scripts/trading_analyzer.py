"""
Trading Analysis Tool
Analyzes trading performance from CSV data and generates comprehensive charts.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
from datetime import datetime
import os
from pathlib import Path

class TradingAnalyzer:
    def __init__(self, csv_path):
        """Initialize the analyzer with trading data from CSV file."""
        self.csv_path = csv_path
        self.df = None
        self.processed_df = None
        self.output_dir = Path(__file__).parent.parent.parent / "source" / "output"
        self.output_dir.mkdir(exist_ok=True)

    def load_data(self):
        """Load and perform initial cleaning of the trading data."""
        print("Loading trading data...")
        self.df = pd.read_csv(self.csv_path)

        # Convert Time column to datetime
        self.df['Time'] = pd.to_datetime(self.df['Time'])

        # Sort by time (oldest first for cumulative analysis)
        self.df = self.df.sort_values('Time').reset_index(drop=True)

        print(f"Loaded {len(self.df)} trades from {self.df['Time'].min().date()} to {self.df['Time'].max().date()}")
        return self.df

    def parse_action_details(self):
        """Parse the Action column to extract detailed trade information."""
        print("Parsing trade details...")

        # Initialize columns
        self.df['Position_Type'] = ''
        self.df['Symbol'] = ''
        self.df['Price'] = 0.0
        self.df['Quantity'] = 0
        self.df['Avg_Price'] = 0.0
        self.df['Exchange'] = ''

        for idx, action in enumerate(self.df['Action']):
            # Extract position type (long/short)
            if 'Close long' in action:
                self.df.at[idx, 'Position_Type'] = 'Long'
            elif 'Close short' in action:
                self.df.at[idx, 'Position_Type'] = 'Short'

            # Extract symbol using regex
            symbol_match = re.search(r'symbol ([A-Z]+:[A-Z]+)', action)
            if symbol_match:
                full_symbol = symbol_match.group(1)
                exchange, symbol = full_symbol.split(':')
                self.df.at[idx, 'Symbol'] = symbol
                self.df.at[idx, 'Exchange'] = exchange

            # Extract price
            price_match = re.search(r'at price ([0-9]+\.?[0-9]*)', action)
            if price_match:
                self.df.at[idx, 'Price'] = float(price_match.group(1))

            # Extract quantity
            quantity_match = re.search(r'for ([0-9]+) units', action)
            if quantity_match:
                self.df.at[idx, 'Quantity'] = int(quantity_match.group(1))

            # Extract average price
            avg_price_match = re.search(r'AVG Price was ([0-9]+\.?[0-9]*)', action)
            if avg_price_match:
                self.df.at[idx, 'Avg_Price'] = float(avg_price_match.group(1))

        # Calculate additional metrics
        self.df['Trade_Value'] = self.df['Price'] * self.df['Quantity']
        self.df['P&L_Per_Share'] = self.df['Realized P&L (value)'] / self.df['Quantity']
        self.df['P&L_Percentage'] = (self.df['Realized P&L (value)'] /
                                    (self.df['Avg_Price'] * self.df['Quantity'])) * 100

        # Add date components for analysis
        self.df['Date'] = self.df['Time'].dt.date
        self.df['Month'] = self.df['Time'].dt.to_period('M')
        self.df['Week'] = self.df['Time'].dt.to_period('W')

        # Create win/loss flag
        self.df['Is_Winner'] = self.df['Realized P&L (value)'] > 0

        self.processed_df = self.df.copy()
        print("Trade details parsed successfully!")
        return self.processed_df

    def calculate_performance_metrics(self):
        """Calculate key trading performance metrics."""
        if self.processed_df is None:
            raise ValueError("Data must be processed first. Call parse_action_details().")

        df = self.processed_df

        metrics = {
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
            'avg_trade_size': df['Trade_Value'].mean(),
            'starting_balance': df['Balance Before'].iloc[0],
            'ending_balance': df['Balance After'].iloc[-1],
            'total_return': df['Balance After'].iloc[-1] - df['Balance Before'].iloc[0],
            'return_percentage': ((df['Balance After'].iloc[-1] / df['Balance Before'].iloc[0]) - 1) * 100
        }

        # Calculate Sharpe ratio (simplified version using daily returns)
        daily_returns = df.groupby('Date')['Realized P&L (value)'].sum()
        if len(daily_returns) > 1:
            metrics['sharpe_ratio'] = daily_returns.mean() / daily_returns.std() if daily_returns.std() != 0 else 0
        else:
            metrics['sharpe_ratio'] = 0

        return metrics

    def get_best_trades(self, top_n=10):
        """Identify and return the best performing trades."""
        if self.processed_df is None:
            raise ValueError("Data must be processed first. Call parse_action_details().")

        df = self.processed_df

        # Best trades by absolute P&L
        best_absolute = df.nlargest(top_n, 'Realized P&L (value)')[
            ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Avg_Price',
             'Realized P&L (value)', 'P&L_Percentage', 'Trade_Value']
        ]

        # Best trades by percentage return
        best_percentage = df.nlargest(top_n, 'P&L_Percentage')[
            ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Avg_Price',
             'Realized P&L (value)', 'P&L_Percentage', 'Trade_Value']
        ]

        # Worst trades for reference
        worst_trades = df.nsmallest(top_n, 'Realized P&L (value)')[
            ['Time', 'Symbol', 'Position_Type', 'Quantity', 'Price', 'Avg_Price',
             'Realized P&L (value)', 'P&L_Percentage', 'Trade_Value']
        ]

        return {
            'best_absolute': best_absolute,
            'best_percentage': best_percentage,
            'worst_trades': worst_trades
        }

    def analyze_by_symbol(self):
        """Analyze performance by trading symbol."""
        if self.processed_df is None:
            raise ValueError("Data must be processed first. Call parse_action_details().")

        df = self.processed_df

        symbol_analysis = df.groupby('Symbol').agg({
            'Realized P&L (value)': ['count', 'sum', 'mean', 'std'],
            'Trade_Value': 'mean',
            'Is_Winner': 'mean',
            'Quantity': 'sum'
        }).round(2)

        # Flatten column names
        symbol_analysis.columns = ['Trade_Count', 'Total_PnL', 'Avg_PnL', 'PnL_StdDev',
                                 'Avg_Trade_Value', 'Win_Rate', 'Total_Shares']

        # Sort by total P&L
        symbol_analysis = symbol_analysis.sort_values('Total_PnL', ascending=False)

        return symbol_analysis

    def print_summary(self):
        """Print a comprehensive trading summary."""
        metrics = self.calculate_performance_metrics()

        print("\n" + "="*60)
        print("TRADING PERFORMANCE SUMMARY")
        print("="*60)

        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Winning Trades: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)")
        print(f"Losing Trades: {metrics['losing_trades']}")
        print(f"")
        print(f"Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"Average Win: ${metrics['avg_win']:,.2f}")
        print(f"Average Loss: ${metrics['avg_loss']:,.2f}")
        print(f"Largest Win: ${metrics['largest_win']:,.2f}")
        print(f"Largest Loss: ${metrics['largest_loss']:,.2f}")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"")
        print(f"Starting Balance: ${metrics['starting_balance']:,.2f}")
        print(f"Ending Balance: ${metrics['ending_balance']:,.2f}")
        print(f"Total Return: ${metrics['total_return']:,.2f} ({metrics['return_percentage']:.2f}%)")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"Average Trade Size: ${metrics['avg_trade_size']:,.2f}")

        print("\n" + "="*60)
        print("TOP PERFORMING SYMBOLS")
        print("="*60)
        symbol_analysis = self.analyze_by_symbol()
        print(symbol_analysis.head(10))

        print("\n" + "="*60)
        print("BEST TRADES BY ABSOLUTE P&L")
        print("="*60)
        best_trades = self.get_best_trades()
        print(best_trades['best_absolute'].head())