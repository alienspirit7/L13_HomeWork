"""
BigQuery Query Tool
Queries NOAA weather data from BigQuery and exports to CSV
"""

from google.cloud import bigquery
from pathlib import Path
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config


def execute_bigquery_query(
    start_date: str,
    end_date: str,
    metrics: list,
    country: str = None,
    state: str = None,
    station_id: str = None,
    aggregation: str = "none",
    output_filename: str = "weather_data.csv"
) -> dict:
    """
    Execute BigQuery query against NOAA GSOD 2024 dataset

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        metrics: List of metrics to retrieve (temp, max, min, prcp, wdsp, dewp, slp, sndp)
        country: Two-letter country code (optional)
        state: Two-letter state code (optional)
        station_id: Specific weather station ID (optional)
        aggregation: Aggregation type (daily, weekly, monthly, none)
        output_filename: Name of output CSV file

    Returns:
        dict: Result dictionary with success status, message, and file path
    """

    try:
        # Initialize BigQuery client
        client = bigquery.Client()

        # Build SELECT clause
        select_fields = ["date"]

        # Add location fields
        if country or state or station_id:
            select_fields.extend(["station_id", "name", "country", "state"])

        # Add requested metrics
        for metric in metrics:
            if metric.lower() not in ['temp', 'max', 'min', 'prcp', 'wdsp', 'dewp', 'slp', 'sndp']:
                return {
                    "success": False,
                    "message": f"Invalid metric: {metric}. Valid metrics: temp, max, min, prcp, wdsp, dewp, slp, sndp",
                    "file_path": None
                }
            select_fields.append(metric.lower())

        # Build WHERE clause
        where_conditions = [f"date >= '{start_date}'", f"date <= '{end_date}'"]

        if country:
            where_conditions.append(f"country = '{country.upper()}'")

        if state:
            where_conditions.append(f"state = '{state.upper()}'")

        if station_id:
            where_conditions.append(f"station_id = '{station_id}'")

        # Build aggregation clause
        group_by_clause = ""
        if aggregation.lower() in ["weekly", "monthly"]:
            if aggregation.lower() == "weekly":
                select_fields[0] = "DATE_TRUNC(date, WEEK) as date"
            elif aggregation.lower() == "monthly":
                select_fields[0] = "DATE_TRUNC(date, MONTH) as date"

            # Average numeric metrics
            for i, field in enumerate(select_fields):
                if field in ['temp', 'max', 'min', 'prcp', 'wdsp', 'dewp', 'slp', 'sndp']:
                    select_fields[i] = f"AVG({field}) as {field}"

            # Group by clause
            group_by_fields = ["date"]
            if "country" in select_fields:
                group_by_fields.extend(["country", "state", "station_id", "name"])
            group_by_clause = f"\nGROUP BY {', '.join(group_by_fields)}"

        # Build final query
        query = f"""
        SELECT
            {', '.join(select_fields)}
        FROM
            `{Config.get_bigquery_table_path()}`
        WHERE
            {' AND '.join(where_conditions)}
        {group_by_clause}
        ORDER BY
            date
        LIMIT {Config.MAX_QUERY_ROWS}
        """

        print(f"Executing query:\n{query}\n")

        # Execute query
        query_job = client.query(query)
        results = query_job.result()

        # Convert to dataframe
        df = results.to_dataframe()

        if df.empty:
            return {
                "success": False,
                "message": f"No data found for the specified criteria. Check date range (must be within 2024) and location codes.",
                "file_path": None
            }

        # Save to CSV
        output_path = Config.OUTPUT_DIR / output_filename
        df.to_csv(output_path, index=False)

        return {
            "success": True,
            "message": f"Successfully retrieved {len(df)} rows of data. Saved to {output_filename}",
            "file_path": str(output_path),
            "row_count": len(df),
            "columns": list(df.columns)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error executing BigQuery query: {str(e)}",
            "file_path": None
        }


# Test function
if __name__ == "__main__":
    print("Testing BigQuery Tool...")

    result = execute_bigquery_query(
        start_date="2024-01-01",
        end_date="2024-01-07",
        metrics=["temp", "prcp"],
        state="CA",
        output_filename="test_query.csv"
    )

    print(f"\nResult: {result}")
