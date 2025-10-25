# Weather Data Query & Visualization System - Product Requirements Document (PRD)

## Executive Summary
A proof-of-concept (POC) AI agent system that enables users to query NOAA weather data from BigQuery using natural language and automatically generates appropriate visualizations. The system uses Claude Sonnet LLM as an orchestrator to interpret user requests and route them to appropriate tools.

---

## 1. Project Overview

### 1.1 Purpose
Build an LLM-orchestrated agent that:
- Interprets natural language queries about weather data
- Queries BigQuery public weather dataset (NOAA GSOD 2024)
- Generates CSV outputs from queries
- Creates appropriate visualizations (line charts for continuous data, bar charts for discrete data)

### 1.2 Success Criteria
- Users can query weather data using natural language
- System correctly chooses between query and visualization tools
- Visualizations match data type (continuous vs discrete)
- Secrets are managed securely outside code
- Fast execution for POC demonstration

---

## 2. Data Source

### 2.1 BigQuery Dataset
- **Project**: `bigquery-public-data`
- **Dataset**: `noaa_gsod`
- **Table**: `gsod2024`
- **Access**: Public dataset (read-only)

### 2.2 Schema Overview (Key Fields)
```
- station_id: STRING (weather station identifier)
- date: DATE (observation date)
- temp: FLOAT (mean temperature in Fahrenheit)
- max: FLOAT (maximum temperature)
- min: FLOAT (minimum temperature)
- dewp: FLOAT (mean dew point)
- slp: FLOAT (mean sea level pressure)
- prcp: FLOAT (precipitation amount)
- sndp: FLOAT (snow depth)
- wdsp: FLOAT (mean wind speed)
- name: STRING (station name)
- country: STRING (country code)
- state: STRING (state code)
```

---

## 3. System Architecture

### 3.1 Component Overview
```
┌─────────────────────────────────────────┐
│           User Interface (CLI)          │
└─────────────────┬───────────────────────┘
                  │ Natural Language Query
                  ▼
┌─────────────────────────────────────────┐
│      LLM Orchestrator (Claude Sonnet)   │
│  - Interprets user intent               │
│  - Selects appropriate tool             │
│  - Generates tool parameters            │
└─────────────┬───────────┬───────────────┘
              │           │
    ┌─────────▼───┐   ┌───▼──────────┐
    │   Tool 1:   │   │   Tool 2:    │
    │   BigQuery  │   │ Visualization│
    │   Query     │   │   Generator  │
    └─────────┬───┘   └───▲──────────┘
              │           │
              │  CSV File │
              └───────────┘
```

### 3.2 Technology Stack
- **Language**: Python 3.8+
- **LLM**: Anthropic Claude Sonnet (via API)
- **BigQuery Client**: google-cloud-bigquery
- **Visualization**: matplotlib, pandas
- **Environment Management**: python-dotenv

---

## 4. Tool Specifications

### 4.1 Tool 1: BigQuery Query Tool

#### 4.1.1 Purpose
Execute SQL queries against NOAA weather dataset based on user parameters.

#### 4.1.2 Input Schema
```python
{
    "type": "object",
    "properties": {
        "filters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "format": "YYYY-MM-DD"},
                "end_date": {"type": "string", "format": "YYYY-MM-DD"},
                "country": {"type": "string"},
                "state": {"type": "string"},
                "station_id": {"type": "string"},
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "examples": ["temp", "prcp", "wdsp", "max", "min"]
                }
            }
        },
        "aggregation": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly", "none"],
            "default": "none"
        },
        "output_filename": {"type": "string", "default": "weather_data.csv"}
    }
}
```

#### 4.1.3 Output
- **Success**: CSV file saved to disk, returns file path
- **Error**: Error message with details

#### 4.1.4 Base SQL Template
```sql
SELECT
    {selected_fields}
FROM
    `bigquery-public-data.noaa_gsod.gsod2024`
WHERE
    {filter_conditions}
{group_by_clause}
ORDER BY
    date
```

#### 4.1.5 Implementation Requirements
- Query validation before execution
- Result size limits (max 10,000 rows for POC)
- CSV export with proper encoding (UTF-8)
- Error handling for invalid dates, missing stations

---

### 4.2 Tool 2: Data Visualization Tool

#### 4.2.1 Purpose
Generate appropriate visualizations from CSV data files.

#### 4.2.2 Input Schema
```python
{
    "type": "object",
    "properties": {
        "csv_filepath": {"type": "string", "required": true},
        "chart_type": {
            "type": "string",
            "enum": ["line", "bar", "auto"],
            "default": "auto"
        },
        "x_column": {"type": "string"},
        "y_columns": {
            "type": "array",
            "items": {"type": "string"}
        },
        "title": {"type": "string"},
        "output_filename": {"type": "string", "default": "visualization.png"}
    }
}
```

#### 4.2.3 Chart Type Selection Logic
- **Line Chart**: Use when x-axis is continuous (dates, time series)
- **Bar Chart**: Use when x-axis is discrete (categories, stations, countries)
- **Auto**: Detect based on x-column data type

#### 4.2.4 Output
- **Success**: PNG image file saved to disk, returns file path
- **Error**: "CSV file not found" or other error messages

#### 4.2.5 Visualization Requirements
- Figure size: 12x6 inches (readable)
- DPI: 100 (web-quality)
- Grid lines enabled
- Legend when multiple series
- Rotated x-labels if needed (for readability)
- Proper axis labels with units

---

## 5. LLM Orchestrator Design

### 5.1 System Prompt

```
You are a weather data assistant that helps users query and visualize NOAA weather data from BigQuery. You have access to two tools:

1. **bigquery_query_tool**: Queries weather data and saves results to CSV
   - Use when users want to retrieve, search, or filter weather data
   - Can filter by date range, location (country/state/station), and metrics
   - Outputs CSV file

2. **visualization_tool**: Creates charts from CSV data
   - Use when users want to see graphs, charts, or visualizations
   - Automatically selects line charts for time series and bar charts for categorical data
   - Requires a CSV file to exist first

**Decision Logic:**
- If user asks to "query", "get", "find", "retrieve" data → use bigquery_query_tool
- If user asks to "visualize", "plot", "chart", "graph" data → use visualization_tool
- If user asks to do both → use bigquery_query_tool first, then visualization_tool
- If CSV file doesn't exist for visualization → inform user to query data first

**Data Understanding:**
- Dataset: NOAA Global Surface Summary of Day (GSOD) 2024
- Available metrics: temperature (temp, max, min), precipitation (prcp), wind speed (wdsp), dew point (dewp), pressure (slp), snow depth (sndp)
- Date range: 2024-01-01 to 2024-12-31
- Locations: Worldwide weather stations

**Response Format:**
1. Acknowledge the user's request
2. Explain which tool(s) you'll use and why
3. Show the parameters you'll pass to the tool
4. Execute the tool
5. Summarize the results
```

### 5.2 Tool Function Definitions

#### 5.2.1 BigQuery Query Tool Definition
```json
{
    "name": "bigquery_query_tool",
    "description": "Queries NOAA weather data from BigQuery based on user-specified filters and saves results to CSV file. Use this when users want to retrieve, search, or filter weather data.",
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "Start date for query in YYYY-MM-DD format"
            },
            "end_date": {
                "type": "string",
                "description": "End date for query in YYYY-MM-DD format"
            },
            "country": {
                "type": "string",
                "description": "Two-letter country code (e.g., 'US', 'CA', 'GB')"
            },
            "state": {
                "type": "string",
                "description": "Two-letter state code for US states (e.g., 'CA', 'NY')"
            },
            "station_id": {
                "type": "string",
                "description": "Specific weather station ID"
            },
            "metrics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of metrics to retrieve: temp, max, min, prcp, wdsp, dewp, slp, sndp"
            },
            "aggregation": {
                "type": "string",
                "enum": ["daily", "weekly", "monthly", "none"],
                "description": "How to aggregate the data"
            },
            "output_filename": {
                "type": "string",
                "description": "Name of the output CSV file",
                "default": "weather_data.csv"
            }
        },
        "required": ["start_date", "end_date", "metrics"]
    }
}
```

#### 5.2.2 Visualization Tool Definition
```json
{
    "name": "visualization_tool",
    "description": "Creates visualizations from CSV data files. Automatically chooses line charts for time series (continuous) data and bar charts for categorical (discrete) data. Use this when users want to see graphs or charts.",
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_filepath": {
                "type": "string",
                "description": "Path to the CSV file to visualize"
            },
            "chart_type": {
                "type": "string",
                "enum": ["line", "bar", "auto"],
                "description": "Type of chart to create. 'auto' will detect based on data.",
                "default": "auto"
            },
            "x_column": {
                "type": "string",
                "description": "Column name to use for x-axis"
            },
            "y_columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Column name(s) to use for y-axis. Can be multiple for comparison."
            },
            "title": {
                "type": "string",
                "description": "Title for the chart"
            },
            "output_filename": {
                "type": "string",
                "description": "Name of the output PNG file",
                "default": "visualization.png"
            }
        },
        "required": ["csv_filepath", "x_column", "y_columns"]
    }
}
```

### 5.3 Example Conversations with Tool Calls

#### Example 1: Simple Query
```
User: "Show me temperatures in New York for January 2024"

LLM Response:
"I'll query the NOAA weather data for New York state in January 2024. I'll retrieve temperature data including mean, max, and min temperatures.

Using: bigquery_query_tool
Parameters:
- start_date: "2024-01-01"
- end_date: "2024-01-31"
- state: "NY"
- metrics: ["temp", "max", "min"]
- output_filename: "ny_jan_temps.csv"

[Tool execution]

Successfully retrieved 31 days of temperature data for New York. The data has been saved to 'ny_jan_temps.csv'."
```

#### Example 2: Query + Visualization
```
User: "Plot the precipitation in California for March 2024"

LLM Response:
"I'll first query precipitation data for California in March 2024, then create a line chart to visualize it.

Step 1 - Using: bigquery_query_tool
Parameters:
- start_date: "2024-03-01"
- end_date: "2024-03-31"
- state: "CA"
- metrics: ["prcp", "date"]
- output_filename: "ca_march_precip.csv"

[Tool execution]

Step 2 - Using: visualization_tool
Parameters:
- csv_filepath: "ca_march_precip.csv"
- chart_type: "line"
- x_column: "date"
- y_columns: ["prcp"]
- title: "Precipitation in California - March 2024"
- output_filename: "ca_precip_chart.png"

[Tool execution]

Visualization created successfully! The chart shows daily precipitation patterns across California in March 2024."
```

#### Example 3: Comparison Query
```
User: "Compare average temperatures between US and Canada in summer 2024"

LLM Response:
"I'll query temperature data for both countries during summer months (June-August 2024) and create a bar chart comparison.

Using: bigquery_query_tool
Parameters:
- start_date: "2024-06-01"
- end_date: "2024-08-31"
- metrics: ["temp", "country"]
- aggregation: "monthly"
- output_filename: "us_canada_summer_temps.csv"

[Tool execution]

Using: visualization_tool
Parameters:
- csv_filepath: "us_canada_summer_temps.csv"
- chart_type: "bar"
- x_column: "country"
- y_columns: ["temp"]
- title: "Average Summer Temperatures: US vs Canada 2024"
- output_filename: "country_comparison.png"

[Tool execution]

The comparison shows average summer temperatures for both countries."
```

#### Example 4: Error Handling
```
User: "Visualize the wind speed trends"

LLM Response:
"To create a visualization, I need data in a CSV file first. I don't see any existing data file.

Could you please specify:
1. What location you're interested in (country/state/station)?
2. What time period (date range)?

Once you provide these details, I'll:
1. Query the wind speed data
2. Create a visualization of the trends"
```

---

## 6. Security & Configuration

### 6.1 Secrets Management

#### 6.1.1 Required Secrets
- `ANTHROPIC_API_KEY`: Claude API key
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to BigQuery service account JSON (or use Application Default Credentials)

#### 6.1.2 .env File Format
```bash
# Anthropic API Configuration
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
# OR if using ADC, leave empty
```

#### 6.1.3 .gitignore Entries
```
.env
*.json
*.csv
*.png
__pycache__/
*.pyc
outputs/
```

### 6.2 BigQuery Authentication Options

**Option 1: Service Account (Recommended for POC)**
1. Create service account in GCP Console
2. Grant "BigQuery Data Viewer" role
3. Download JSON key
4. Set path in GOOGLE_APPLICATION_CREDENTIALS

**Option 2: Application Default Credentials**
```bash
gcloud auth application-default login
```

---

## 7. Implementation Guide

### 7.1 Project Structure
```
MyFirstAgent/
│
├── .env                          # Secret keys (not in git)
├── .gitignore                    # Ignore secrets and outputs
├── requirements.txt              # Python dependencies
├── README.md                     # Setup and usage instructions
│
├── main.py                       # Orchestrator entry point
├── config.py                     # Load environment variables
│
├── tools/
│   ├── __init__.py
│   ├── bigquery_tool.py         # BigQuery query implementation
│   └── visualization_tool.py    # Visualization implementation
│
├── prompts/
│   └── system_prompt.txt        # LLM system prompt
│
└── outputs/                      # Generated files (git-ignored)
    ├── *.csv
    └── *.png
```

### 7.2 Dependencies (requirements.txt)
```
anthropic>=0.39.0
google-cloud-bigquery>=3.25.0
pandas>=2.2.0
matplotlib>=3.9.0
python-dotenv>=1.0.0
```

### 7.3 Main Orchestrator Flow

```python
# Pseudocode for main.py

1. Load environment variables (.env)
2. Initialize Anthropic client with API key
3. Initialize tool functions (BigQuery, Visualization)
4. Load system prompt
5. Start conversation loop:
   a. Get user input
   b. Send to Claude with tool definitions
   c. Process tool calls if any:
      - Execute corresponding Python function
      - Return results to Claude
   d. Display Claude's response to user
   e. Repeat until user exits
```

---

## 8. User Interaction Examples

### 8.1 Supported Query Patterns

**Temporal Queries:**
- "Show temperatures for last week"
- "Get precipitation data for January 2024"
- "Compare summer vs winter temperatures"

**Location Queries:**
- "Weather in California"
- "Temperatures across US states"
- "Precipitation in station ID 72295013874"

**Metric Queries:**
- "Show me wind speed and temperature"
- "Get all available metrics for Texas in March"
- "Maximum and minimum temperatures"

**Aggregation Queries:**
- "Monthly average temperatures"
- "Weekly precipitation totals"
- "Daily weather summary"

**Visualization Requests:**
- "Plot temperature trends"
- "Create a chart of precipitation"
- "Visualize wind speed over time"
- "Bar chart comparing states"

### 8.2 Sample User Sessions

#### Session 1: First-time User
```
System: Welcome to Weather Data Assistant! Ask me about NOAA weather data.

User: What can you do?