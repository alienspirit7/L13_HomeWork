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

# Valid metric fields (numeric values that can be aggregated)
VALID_METRICS = ['temp', 'max', 'min', 'prcp', 'wdsp', 'dewp', 'slp', 'sndp']

# Dimension fields (grouping attributes)
DIMENSION_FIELDS = ['country', 'state', 'stn', 'name']


def execute_bigquery_query(
    start_date: str,
    end_date: str,
    metrics: list,
    country: str = None,
    state: str = None,
    station_id: str = None,
    aggregation: str = "none",
    metric_aggregation: str = "avg",
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
        aggregation: Date aggregation type (daily, weekly, monthly, none)
        metric_aggregation: Metric aggregation function (avg, min, max)
        output_filename: Name of output CSV file

    Returns:
        dict: Result dictionary with success status, message, and file path
    """

    try:
        # Initialize BigQuery client
        client = bigquery.Client()

        # Determine if we need to join with stations table
        needs_station_join = country or state or station_id

        # Determine if we should include dimensional breakdown
        # Only include dimensions if: no aggregation (raw data) OR filtering by specific station
        include_dimensions = aggregation.lower() == "none" or station_id

        # Build SELECT clause
        select_fields = []

        # Add date field based on query type:
        # - Time-based aggregation (daily/weekly/monthly): need date
        # - Dimensional breakdown (raw data): need date
        # - Overall aggregate (no dimensions): don't need date
        if aggregation.lower() != "none" or include_dimensions or not needs_station_join:
            select_fields.append("g.date")

        # Add location fields only if we want dimensional breakdown
        if needs_station_join and include_dimensions:
            select_fields.extend(["g.stn as station_id", "s.name", "s.country", "s.state"])

        # Add requested metrics with table alias
        for metric in metrics:
            if metric.lower() not in VALID_METRICS:
                return {
                    "success": False,
                    "message": f"Invalid metric: {metric}. Valid metrics: {', '.join(VALID_METRICS)}",
                    "file_path": None
                }
            select_fields.append(f"g.{metric.lower()}")

        # Build WHERE clause
        where_conditions = [f"g.date >= '{start_date}'", f"g.date <= '{end_date}'"]

        if country:
            where_conditions.append(f"s.country = '{country.upper()}'")

        if state:
            where_conditions.append(f"s.state = '{state.upper()}'")

        if station_id:
            where_conditions.append(f"g.stn = '{station_id}'")

        # Build aggregation and GROUP BY clause
        group_by_clause = ""
        order_by_field = "g.date" if select_fields and "g.date" in str(select_fields[0]) else None

        # Determine if we should apply aggregation functions to metrics
        # Apply aggregation if we're grouping by dimensions or if it's an overall aggregate
        should_aggregate_metrics = not include_dimensions

        if should_aggregate_metrics:
            # Determine aggregation function
            agg_func = metric_aggregation.upper()
            if agg_func not in ['AVG', 'MIN', 'MAX']:
                agg_func = 'AVG'  # Default to AVG if invalid

            # Apply aggregation functions to all metrics
            for i, field in enumerate(select_fields):
                # Check if this field is a metric (contains g.metric_name)
                for metric in VALID_METRICS:
                    if field == f"g.{metric}":
                        select_fields[i] = f"{agg_func}(g.{metric}) as {metric}"
                        break

            # Build GROUP BY clause only if we have dimensional fields
            group_by_fields = []

            # Check if we're doing time-based aggregation
            if aggregation.lower() in ["daily", "weekly", "monthly"]:
                # Apply date truncation for weekly/monthly aggregation
                if aggregation.lower() == "weekly":
                    # Update the date field in select_fields
                    for i, field in enumerate(select_fields):
                        if "g.date" in field:
                            select_fields[i] = "DATE_TRUNC(g.date, WEEK) as date"
                            break
                elif aggregation.lower() == "monthly":
                    for i, field in enumerate(select_fields):
                        if "g.date" in field:
                            select_fields[i] = "DATE_TRUNC(g.date, MONTH) as date"
                            break
                else:  # daily
                    for i, field in enumerate(select_fields):
                        if "g.date" in field:
                            select_fields[i] = "g.date as date"
                            break

                group_by_fields.append("date")
                order_by_field = "date"

            # Add location dimensions to GROUP BY if they're in the select
            if include_dimensions and needs_station_join:
                for i, field in enumerate(select_fields):
                    if "g.date" in field:
                        select_fields[i] = "g.date as date"
                        break
                if "date" not in group_by_fields:
                    group_by_fields.append("date")
                group_by_fields.extend(["g.stn", "s.name", "s.country", "s.state"])
                if not order_by_field:
                    order_by_field = "date"

            if group_by_fields:
                group_by_clause = f"\nGROUP BY {', '.join(group_by_fields)}"

        # Build ORDER BY clause
        order_by_clause = ""
        if order_by_field:
            order_by_clause = f"\nORDER BY\n            {order_by_field}"

        # Build final query
        if needs_station_join:
            query = f"""
        SELECT
            {', '.join(select_fields)}
        FROM
            `{Config.get_bigquery_table_path()}` g
        JOIN
            `bigquery-public-data.noaa_gsod.stations` s
        ON
            g.stn = s.usaf AND g.wban = s.wban
        WHERE
            {' AND '.join(where_conditions)}
        {group_by_clause}{order_by_clause}
        LIMIT {Config.MAX_QUERY_ROWS}
        """
        else:
            query = f"""
        SELECT
            {', '.join(select_fields)}
        FROM
            `{Config.get_bigquery_table_path()}` g
        WHERE
            {' AND '.join(where_conditions)}
        {group_by_clause}{order_by_clause}
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
