"""
Visualization Tool
Creates charts from CSV data files
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


def create_visualization(
    csv_filepath: str,
    x_column: str,
    y_columns: list,
    chart_type: str = "auto",
    title: str = None,
    output_filename: str = "visualization.png"
) -> dict:
    """
    Create visualization from CSV data

    Args:
        csv_filepath: Path to CSV file to visualize
        x_column: Column name for x-axis
        y_columns: List of column names for y-axis
        chart_type: Type of chart (line, bar, auto)
        title: Chart title
        output_filename: Name of output PNG file

    Returns:
        dict: Result dictionary with success status, message, and file path
    """

    try:
        # Check if CSV file exists
        csv_path = Path(csv_filepath)
        if not csv_path.exists():
            # Try in outputs directory
            csv_path = Config.OUTPUT_DIR / csv_filepath
            if not csv_path.exists():
                return {
                    "success": False,
                    "message": f"CSV file not found: {csv_filepath}. Please run a query first to create the data file.",
                    "file_path": None
                }

        # Load CSV data
        df = pd.read_csv(csv_path)

        # Validate columns exist
        if x_column not in df.columns:
            return {
                "success": False,
                "message": f"Column '{x_column}' not found in CSV. Available columns: {', '.join(df.columns)}",
                "file_path": None
            }

        for y_col in y_columns:
            if y_col not in df.columns:
                return {
                    "success": False,
                    "message": f"Column '{y_col}' not found in CSV. Available columns: {', '.join(df.columns)}",
                    "file_path": None
                }

        # Auto-detect chart type if needed
        if chart_type.lower() == "auto":
            # If x-column contains 'date', use line chart
            if 'date' in x_column.lower() or pd.api.types.is_datetime64_any_dtype(df[x_column]):
                chart_type = "line"
            else:
                # Check if x-column is categorical
                if df[x_column].dtype == 'object' or df[x_column].nunique() < 20:
                    chart_type = "bar"
                else:
                    chart_type = "line"

        # Convert date column if needed
        if 'date' in x_column.lower():
            df[x_column] = pd.to_datetime(df[x_column])

        # Create figure
        plt.figure(figsize=(12, 6))

        # Create chart based on type
        if chart_type.lower() == "line":
            for y_col in y_columns:
                plt.plot(df[x_column], df[y_col], marker='o', label=y_col, linewidth=2)
        elif chart_type.lower() == "bar":
            if len(y_columns) == 1:
                plt.bar(df[x_column], df[y_columns[0]], label=y_columns[0])
            else:
                # Multiple bars side by side
                x_pos = range(len(df))
                width = 0.8 / len(y_columns)
                for i, y_col in enumerate(y_columns):
                    offset = (i - len(y_columns)/2) * width + width/2
                    plt.bar([x + offset for x in x_pos], df[y_col], width=width, label=y_col)
                plt.xticks(x_pos, df[x_column])
        else:
            return {
                "success": False,
                "message": f"Invalid chart type: {chart_type}. Valid types: line, bar, auto",
                "file_path": None
            }

        # Formatting
        plt.xlabel(x_column.replace('_', ' ').title(), fontsize=12)
        plt.ylabel('Value', fontsize=12)
        plt.title(title or f"{', '.join(y_columns)} vs {x_column}", fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()

        # Rotate x-labels if needed
        if chart_type.lower() == "bar" or len(df) > 10:
            plt.xticks(rotation=45, ha='right')

        plt.tight_layout()

        # Save figure
        output_path = Config.OUTPUT_DIR / output_filename
        plt.savefig(output_path, dpi=100, bbox_inches='tight')
        plt.close()

        return {
            "success": True,
            "message": f"Visualization created successfully. Saved to {output_filename}",
            "file_path": str(output_path),
            "chart_type": chart_type
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error creating visualization: {str(e)}",
            "file_path": None
        }


# Test function
if __name__ == "__main__":
    print("Testing Visualization Tool...")

    # Create sample data for testing
    import pandas as pd
    sample_data = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=7),
        'temp': [45, 47, 50, 48, 46, 49, 52],
        'prcp': [0.1, 0.0, 0.3, 0.2, 0.0, 0.1, 0.0]
    })
    sample_data.to_csv(Config.OUTPUT_DIR / 'test_data.csv', index=False)

    result = create_visualization(
        csv_filepath='test_data.csv',
        x_column='date',
        y_columns=['temp'],
        title='Temperature Test',
        output_filename='test_viz.png'
    )

    print(f"\nResult: {result}")
