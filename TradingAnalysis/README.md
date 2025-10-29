# Trading Analysis Tool

A comprehensive Python-based trading analysis tool that reads CSV trading data and generates detailed performance metrics and visualizations.

## Features

### Core Analysis

-   **Performance Metrics**: Win rate, profit factor, Sharpe ratio, total return
-   **Trade Analysis**: Best/worst trades by absolute and percentage returns
-   **Symbol Performance**: Detailed breakdown by trading symbol
-   **Timeline Analysis**: P&L evolution over time
-   **Position Analysis**: Long vs short position performance

### Visualizations

-   P&L timeline charts
-   Performance dashboard with multiple metrics
-   Best trades analysis charts
-   Symbol performance comparison
-   Trade distribution histograms

## Files Structure

```
TradingAnalysis/
├── source/
│   ├── data/
│   │   └── 2025/
│   │       └── trades.csv          # Your trading data
│   ├── output/                     # Generated reports and charts
│   └── scripts/
│       ├── trading_analyzer.py     # Core analysis engine
│       ├── trading_visualizer.py   # Chart generation
│       ├── trading_analysis_main.py # Full analysis with charts
│       └── simple_trading_analysis.py # Basic analysis (no charts)
├── run_trading_analysis.bat        # Windows batch file to run analysis
└── requirements.txt               # Python dependencies
```

## Usage

### Option 1: Full Analysis with Charts (Recommended)

**Requirements**: pandas, matplotlib, seaborn, numpy

1. **Easy way**: Double-click `run_trading_analysis.bat`

    - Automatically installs dependencies and runs the analysis

2. **Manual way**:

    ```bash
    # Install dependencies
    pip install pandas matplotlib seaborn numpy

    # Run analysis
    cd source/scripts
    python trading_analysis_main.py
    ```

### Option 2: Simple Analysis (No Charts Required)

**Requirements**: Only pandas and numpy

```bash
cd source/scripts
python simple_trading_analysis.py
```

## Generated Output

### Charts (Full Analysis)

-   `pnl_timeline.png` - P&L evolution and balance over time
-   `performance_dashboard.png` - Comprehensive performance metrics
-   `best_trades_analysis.png` - Best and worst trades visualization
-   `symbol_analysis.png` - Symbol performance comparison

### Reports

-   `detailed_analysis_report.txt` - Comprehensive text report
-   `simple_analysis_report.txt` - Basic analysis summary

### CSV Exports

-   `processed_trades.csv` - Cleaned and enhanced trading data
-   `symbol_analysis.csv` - Performance metrics by symbol
-   `best_trades_absolute.csv` - Top trades by absolute P&L
-   `best_trades_percentage.csv` - Top trades by percentage return

## Key Metrics Explained

### Performance Metrics

-   **Win Rate**: Percentage of profitable trades
-   **Profit Factor**: Ratio of total wins to total losses
-   **Sharpe Ratio**: Risk-adjusted return measure
-   **Average Win/Loss**: Mean profit/loss per winning/losing trade
-   **Total Return**: Overall account performance

### Trade Analysis

-   **Best Trades**: Top performers by absolute dollar amount and percentage return
-   **Symbol Performance**: Which stocks/assets performed best
-   **Position Analysis**: Long vs short position effectiveness
-   **Trade Size Analysis**: Relationship between position size and outcomes

## CSV Data Format

The tool expects a CSV file with the following columns:

-   `Time`: Trade execution timestamp
-   `Balance Before`: Account balance before trade
-   `Balance After`: Account balance after trade
-   `Realized P&L (value)`: Profit/loss in dollars
-   `Realized P&L (currency)`: Currency denomination
-   `Action`: Detailed trade description including symbol, price, quantity

## Example Results

Based on your data, the analysis will show:

-   Total trades: 84
-   Performance across symbols like BYND, NOK, ASTS, RKLB, etc.
-   Best performing trades (e.g., NOK positions with $848 profit)
-   Win rate and profit factor analysis
-   Balance evolution from ~$10K to ~$24K

## Customization

### Modify Analysis Parameters

Edit the main scripts to change:

-   Number of top trades displayed (default: 10-15)
-   Chart styling and colors
-   Additional metrics calculations
-   Output file formats

### Add New Analysis

The modular design allows easy addition of new analysis functions:

1. Add methods to `TradingAnalyzer` class for new metrics
2. Add visualization methods to `TradingVisualizer` class
3. Update main scripts to include new analysis

## Troubleshooting

### Common Issues

1. **Module not found errors**: Install required packages using pip
2. **File not found**: Ensure trades.csv is in the correct location
3. **Empty charts**: Check that matplotlib backend is properly configured

### Dependencies Installation

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install pandas matplotlib seaborn numpy
```

### Python Version

-   Requires Python 3.7 or higher
-   Tested with Python 3.11

## Advanced Usage

### Custom Data Sources

Modify the `load_data()` method in `TradingAnalyzer` to support different CSV formats or data sources.

### Additional Visualizations

The `TradingVisualizer` class can be extended with new chart types:

-   Drawdown analysis
-   Rolling performance metrics
-   Risk-return scatter plots
-   Correlation analysis

### Batch Processing

Process multiple CSV files by modifying the main script to loop through multiple data sources.

---

**Author**: Generated for comprehensive trading analysis
**License**: Free for personal use
**Version**: 1.0
