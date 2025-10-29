#!/usr/bin/env python3
"""
Trading Analysis Main Script
Comprehensive analysis and visualization of trading performance data.

Usage:
    python trading_analysis_main.py

This script will:
1. Load and analyze trading data from CSV
2. Calculate performance metrics
3. Generate comprehensive charts and visualizations
4. Save analysis results and charts to the output directory
"""

import sys
from pathlib import Path

# Add the current directory to the path to import our modules
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from trading_analyzer import TradingAnalyzer
from trading_visualizer import TradingVisualizer

def main():
    """Main execution function."""

    # File paths
    csv_path = current_dir.parent / "data" / "2025" / "trades.csv"

    print("="*60)
    print("COMPREHENSIVE TRADING ANALYSIS")
    print("="*60)

    try:
        # Initialize analyzer
        print(f"Initializing analysis for: {csv_path}")
        analyzer = TradingAnalyzer(csv_path)

        # Load and process data
        analyzer.load_data()
        analyzer.parse_action_details()

        # Print summary statistics
        analyzer.print_summary()

        # Create visualizations
        print(f"\n{'='*60}")
        print("GENERATING VISUALIZATIONS")
        print("="*60)

        visualizer = TradingVisualizer(analyzer)
        visualizer.create_all_charts()

        # Save detailed analysis to text file
        save_detailed_analysis(analyzer)

        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE!")
        print("="*60)
        print(f"Check the output directory for all generated files:")
        print(f"Location: {analyzer.output_dir}")

    except FileNotFoundError:
        print(f"ERROR: Could not find trades data file at {csv_path}")
        print("Please ensure the trades.csv file exists in the correct location.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        print("Make sure all required packages are installed:")
        print("pip install pandas matplotlib seaborn numpy")

def save_detailed_analysis(analyzer):
    """Save detailed analysis results to text file."""
    output_file = analyzer.output_dir / "detailed_analysis_report.txt"

    with open(output_file, 'w') as f:
        f.write("COMPREHENSIVE TRADING ANALYSIS REPORT\n")
        f.write("="*60 + "\n\n")

        # Performance metrics
        metrics = analyzer.calculate_performance_metrics()
        f.write("PERFORMANCE METRICS\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Trades: {metrics['total_trades']}\n")
        f.write(f"Winning Trades: {metrics['winning_trades']} ({metrics['win_rate']:.1f}%)\n")
        f.write(f"Losing Trades: {metrics['losing_trades']}\n\n")

        f.write(f"Total P&L: ${metrics['total_pnl']:,.2f}\n")
        f.write(f"Average Win: ${metrics['avg_win']:,.2f}\n")
        f.write(f"Average Loss: ${metrics['avg_loss']:,.2f}\n")
        f.write(f"Largest Win: ${metrics['largest_win']:,.2f}\n")
        f.write(f"Largest Loss: ${metrics['largest_loss']:,.2f}\n")
        f.write(f"Profit Factor: {metrics['profit_factor']:.2f}\n\n")

        f.write(f"Starting Balance: ${metrics['starting_balance']:,.2f}\n")
        f.write(f"Ending Balance: ${metrics['ending_balance']:,.2f}\n")
        f.write(f"Total Return: ${metrics['total_return']:,.2f} ({metrics['return_percentage']:.2f}%)\n")
        f.write(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}\n")
        f.write(f"Average Trade Size: ${metrics['avg_trade_size']:,.2f}\n\n")

        # Symbol analysis
        f.write("SYMBOL PERFORMANCE ANALYSIS\n")
        f.write("-" * 30 + "\n")
        symbol_analysis = analyzer.analyze_by_symbol()
        f.write(symbol_analysis.to_string())
        f.write("\n\n")

        # Best trades analysis
        f.write("BEST TRADES ANALYSIS\n")
        f.write("-" * 30 + "\n")
        best_trades = analyzer.get_best_trades(10)

        f.write("TOP 10 TRADES BY ABSOLUTE P&L:\n")
        f.write(best_trades['best_absolute'].to_string(index=False))
        f.write("\n\n")

        f.write("TOP 10 TRADES BY PERCENTAGE RETURN:\n")
        f.write(best_trades['best_percentage'].to_string(index=False))
        f.write("\n\n")

        f.write("WORST 10 TRADES:\n")
        f.write(best_trades['worst_trades'].to_string(index=False))
        f.write("\n\n")

        # Monthly breakdown
        f.write("MONTHLY PERFORMANCE BREAKDOWN\n")
        f.write("-" * 30 + "\n")
        monthly_analysis = analyzer.processed_df.groupby('Month').agg({
            'Realized P&L (value)': ['count', 'sum', 'mean'],
            'Is_Winner': 'mean',
            'Trade_Value': 'mean'
        }).round(2)
        monthly_analysis.columns = ['Trades', 'Total_PnL', 'Avg_PnL', 'Win_Rate', 'Avg_Trade_Size']
        f.write(monthly_analysis.to_string())

    print(f"Detailed analysis report saved to: {output_file}")

def create_requirements_file():
    """Create a requirements.txt file with necessary dependencies."""
    requirements_content = """pandas>=1.3.0
matplotlib>=3.3.0
seaborn>=0.11.0
numpy>=1.20.0
"""

    req_file = Path(__file__).parent.parent.parent / "requirements.txt"
    with open(req_file, 'w') as f:
        f.write(requirements_content)

    print(f"Requirements file created at: {req_file}")

if __name__ == "__main__":
    # Create requirements file for easy installation
    create_requirements_file()

    # Run the main analysis
    main()