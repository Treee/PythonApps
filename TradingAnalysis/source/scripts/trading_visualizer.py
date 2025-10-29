"""
Trading Visualization Module
Creates comprehensive charts and graphs for trading analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path

class TradingVisualizer:
    def __init__(self, analyzer):
        """Initialize with a TradingAnalyzer instance."""
        self.analyzer = analyzer
        self.output_dir = analyzer.output_dir

        # Set style for better looking plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def create_pnl_timeline(self, save=True):
        """Create a timeline chart showing P&L and balance evolution."""
        df = self.analyzer.processed_df

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))

        # Cumulative P&L over time
        df['Cumulative_PnL'] = df['Realized P&L (value)'].cumsum()
        ax1.plot(df['Time'], df['Cumulative_PnL'], linewidth=2, color='blue')
        ax1.fill_between(df['Time'], df['Cumulative_PnL'], alpha=0.3, color='blue')
        ax1.set_title('Cumulative P&L Over Time', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Cumulative P&L ($)')
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7)

        # Balance evolution
        ax2.plot(df['Time'], df['Balance After'], linewidth=2, color='green', label='Balance')
        ax2.set_title('Account Balance Over Time', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Balance ($)')
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Daily P&L distribution
        daily_pnl = df.groupby('Date')['Realized P&L (value)'].sum()
        colors = ['green' if x > 0 else 'red' for x in daily_pnl.values]
        ax3.bar(range(len(daily_pnl)), daily_pnl.values, color=colors, alpha=0.7)
        ax3.set_title('Daily P&L Distribution', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Daily P&L ($)')
        ax3.set_xlabel('Trading Days')
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'pnl_timeline.png', dpi=300, bbox_inches='tight')
            print(f"Saved P&L timeline chart to {self.output_dir / 'pnl_timeline.png'}")

        return fig

    def create_performance_dashboard(self, save=True):
        """Create a comprehensive performance dashboard."""
        df = self.analyzer.processed_df
        metrics = self.analyzer.calculate_performance_metrics()

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Trading Performance Dashboard', fontsize=16, fontweight='bold')

        # 1. Win/Loss Distribution (Pie Chart)
        win_loss_data = [metrics['winning_trades'], metrics['losing_trades']]
        win_loss_labels = ['Winners', 'Losers']
        colors = ['green', 'red']
        axes[0,0].pie(win_loss_data, labels=win_loss_labels, colors=colors, autopct='%1.1f%%', startangle=90)
        axes[0,0].set_title(f'Win Rate: {metrics["win_rate"]:.1f}%')

        # 2. P&L Distribution Histogram
        axes[0,1].hist(df['Realized P&L (value)'], bins=30, alpha=0.7, color='blue', edgecolor='black')
        axes[0,1].axvline(df['Realized P&L (value)'].mean(), color='red', linestyle='--', linewidth=2, label='Mean')
        axes[0,1].set_title('P&L Distribution')
        axes[0,1].set_xlabel('P&L ($)')
        axes[0,1].set_ylabel('Frequency')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)

        # 3. Trade Size Distribution
        axes[0,2].hist(df['Trade_Value'], bins=30, alpha=0.7, color='orange', edgecolor='black')
        axes[0,2].set_title('Trade Size Distribution')
        axes[0,2].set_xlabel('Trade Value ($)')
        axes[0,2].set_ylabel('Frequency')
        axes[0,2].grid(True, alpha=0.3)

        # 4. Monthly P&L
        monthly_pnl = df.groupby('Month')['Realized P&L (value)'].sum()
        colors = ['green' if x > 0 else 'red' for x in monthly_pnl.values]
        axes[1,0].bar(range(len(monthly_pnl)), monthly_pnl.values, color=colors, alpha=0.7)
        axes[1,0].set_title('Monthly P&L')
        axes[1,0].set_ylabel('P&L ($)')
        axes[1,0].set_xlabel('Month')
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].axhline(y=0, color='black', linestyle='-', alpha=0.5)

        # 5. Position Type Performance
        position_pnl = df.groupby('Position_Type')['Realized P&L (value)'].agg(['sum', 'mean', 'count'])
        position_pnl['sum'].plot(kind='bar', ax=axes[1,1], color=['blue', 'red'], alpha=0.7)
        axes[1,1].set_title('P&L by Position Type')
        axes[1,1].set_ylabel('Total P&L ($)')
        axes[1,1].tick_params(axis='x', rotation=45)
        axes[1,1].grid(True, alpha=0.3)

        # 6. Top Symbols Performance
        symbol_pnl = df.groupby('Symbol')['Realized P&L (value)'].sum().sort_values(ascending=False).head(10)
        colors = ['green' if x > 0 else 'red' for x in symbol_pnl.values]
        axes[1,2].bar(range(len(symbol_pnl)), symbol_pnl.values, color=colors, alpha=0.7)
        axes[1,2].set_title('Top 10 Symbols by P&L')
        axes[1,2].set_ylabel('Total P&L ($)')
        axes[1,2].set_xlabel('Symbol')
        axes[1,2].set_xticks(range(len(symbol_pnl)))
        axes[1,2].set_xticklabels(symbol_pnl.index, rotation=45)
        axes[1,2].grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'performance_dashboard.png', dpi=300, bbox_inches='tight')
            print(f"Saved performance dashboard to {self.output_dir / 'performance_dashboard.png'}")

        return fig

    def create_best_trades_chart(self, top_n=15, save=True):
        """Create visualization of best and worst trades."""
        best_trades = self.analyzer.get_best_trades(top_n)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'Top {top_n} Best and Worst Trades Analysis', fontsize=16, fontweight='bold')

        # Best trades by absolute P&L
        best_abs = best_trades['best_absolute']
        axes[0,0].barh(range(len(best_abs)), best_abs['Realized P&L (value)'], color='green', alpha=0.7)
        axes[0,0].set_title('Best Trades by Absolute P&L')
        axes[0,0].set_xlabel('P&L ($)')
        axes[0,0].set_yticks(range(len(best_abs)))
        axes[0,0].set_yticklabels([f"{row['Symbol']} ({row['Time'].strftime('%m/%d')})"
                                  for _, row in best_abs.iterrows()])
        axes[0,0].grid(True, alpha=0.3)

        # Best trades by percentage
        best_pct = best_trades['best_percentage']
        axes[0,1].barh(range(len(best_pct)), best_pct['P&L_Percentage'], color='blue', alpha=0.7)
        axes[0,1].set_title('Best Trades by Percentage Return')
        axes[0,1].set_xlabel('Return (%)')
        axes[0,1].set_yticks(range(len(best_pct)))
        axes[0,1].set_yticklabels([f"{row['Symbol']} ({row['Time'].strftime('%m/%d')})"
                                  for _, row in best_pct.iterrows()])
        axes[0,1].grid(True, alpha=0.3)

        # Worst trades
        worst = best_trades['worst_trades']
        axes[1,0].barh(range(len(worst)), worst['Realized P&L (value)'], color='red', alpha=0.7)
        axes[1,0].set_title('Worst Trades by Absolute P&L')
        axes[1,0].set_xlabel('P&L ($)')
        axes[1,0].set_yticks(range(len(worst)))
        axes[1,0].set_yticklabels([f"{row['Symbol']} ({row['Time'].strftime('%m/%d')})"
                                  for _, row in worst.iterrows()])
        axes[1,0].grid(True, alpha=0.3)

        # Trade size vs P&L scatter
        df = self.analyzer.processed_df
        colors = ['green' if x > 0 else 'red' for x in df['Realized P&L (value)']]
        axes[1,1].scatter(df['Trade_Value'], df['Realized P&L (value)'],
                         c=colors, alpha=0.6, s=30)
        axes[1,1].set_title('Trade Size vs P&L')
        axes[1,1].set_xlabel('Trade Value ($)')
        axes[1,1].set_ylabel('P&L ($)')
        axes[1,1].grid(True, alpha=0.3)
        axes[1,1].axhline(y=0, color='black', linestyle='--', alpha=0.5)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'best_trades_analysis.png', dpi=300, bbox_inches='tight')
            print(f"Saved best trades analysis to {self.output_dir / 'best_trades_analysis.png'}")

        return fig

    def create_symbol_analysis_chart(self, save=True):
        """Create detailed analysis charts for symbol performance."""
        df = self.analyzer.processed_df
        symbol_analysis = self.analyzer.analyze_by_symbol()

        # Get top 10 most traded symbols
        top_symbols = symbol_analysis.head(10)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Symbol Performance Analysis', fontsize=16, fontweight='bold')

        # Symbol P&L
        colors = ['green' if x > 0 else 'red' for x in top_symbols['Total_PnL']]
        axes[0,0].bar(range(len(top_symbols)), top_symbols['Total_PnL'],
                     color=colors, alpha=0.7)
        axes[0,0].set_title('Total P&L by Symbol')
        axes[0,0].set_ylabel('Total P&L ($)')
        axes[0,0].set_xticks(range(len(top_symbols)))
        axes[0,0].set_xticklabels(top_symbols.index, rotation=45)
        axes[0,0].grid(True, alpha=0.3)

        # Trade count by symbol
        axes[0,1].bar(range(len(top_symbols)), top_symbols['Trade_Count'],
                     color='blue', alpha=0.7)
        axes[0,1].set_title('Number of Trades by Symbol')
        axes[0,1].set_ylabel('Trade Count')
        axes[0,1].set_xticks(range(len(top_symbols)))
        axes[0,1].set_xticklabels(top_symbols.index, rotation=45)
        axes[0,1].grid(True, alpha=0.3)

        # Win rate by symbol
        axes[1,0].bar(range(len(top_symbols)), top_symbols['Win_Rate'] * 100,
                     color='orange', alpha=0.7)
        axes[1,0].set_title('Win Rate by Symbol')
        axes[1,0].set_ylabel('Win Rate (%)')
        axes[1,0].set_xticks(range(len(top_symbols)))
        axes[1,0].set_xticklabels(top_symbols.index, rotation=45)
        axes[1,0].grid(True, alpha=0.3)
        axes[1,0].axhline(y=50, color='red', linestyle='--', alpha=0.7, label='50%')
        axes[1,0].legend()

        # Average trade value by symbol
        axes[1,1].bar(range(len(top_symbols)), top_symbols['Avg_Trade_Value'],
                     color='purple', alpha=0.7)
        axes[1,1].set_title('Average Trade Value by Symbol')
        axes[1,1].set_ylabel('Avg Trade Value ($)')
        axes[1,1].set_xticks(range(len(top_symbols)))
        axes[1,1].set_xticklabels(top_symbols.index, rotation=45)
        axes[1,1].grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'symbol_analysis.png', dpi=300, bbox_inches='tight')
            print(f"Saved symbol analysis to {self.output_dir / 'symbol_analysis.png'}")

        return fig

    def create_all_charts(self):
        """Generate all analysis charts."""
        print("Generating comprehensive trading analysis charts...")

        try:
            self.create_pnl_timeline()
            self.create_performance_dashboard()
            self.create_best_trades_chart()
            self.create_symbol_analysis_chart()

            print(f"\nAll charts have been saved to: {self.output_dir}")
            print("Generated charts:")
            print("- pnl_timeline.png")
            print("- performance_dashboard.png")
            print("- best_trades_analysis.png")
            print("- symbol_analysis.png")

        except Exception as e:
            print(f"Error generating charts: {str(e)}")
            print("Make sure matplotlib and seaborn are installed: pip install matplotlib seaborn")