# Weather Data Query & Visualization System

An AI-powered agent that enables natural language querying and visualization of NOAA weather data from BigQuery.

## 📚 Documentation Overview

This project includes comprehensive documentation optimized for LLM implementation:

### 1. [PRD.md](PRD.md) - Product Requirements Document
Complete product specification including:
- Project overview and success criteria
- Data source details (NOAA GSOD 2024 dataset)
- System architecture and technology stack
- Tool specifications (BigQuery query tool, Visualization tool)
- LLM orchestrator design with tool definitions
- Example conversations and tool calls
- Security and configuration requirements
- Project structure and dependencies
- User interaction patterns

### 2. [LLM_PROMPTS.md](LLM_PROMPTS.md) - LLM Prompts & Implementation Guide
Optimized prompts for AI agent implementation:
- Complete system prompt for orchestrator
- Tool-specific prompts and descriptions
- Conversation flow patterns
- Error handling prompts
- Parameter extraction logic
- Filename and title generation rules
- Advanced query patterns
- Testing scenarios
- Deployment checklist

### 3. [PRD_APPENDIX.md](PRD_APPENDIX.md) - Additional Examples
Extended examples and edge cases for reference

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Cloud account (for BigQuery access)
- Anthropic API key (for Claude Sonnet)

### Installation

1. **Clone or navigate to the project directory**
```bash
cd MyFirstAgent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

4. **Configure BigQuery access**
   - Option A: Use service account (recommended)
     - Create service account in GCP Console
     - Grant "BigQuery Data Viewer" role
     - Download JSON key
     - Set path in `GOOGLE_APPLICATION_CREDENTIALS`

   - Option B: Use Application Default Credentials
     ```bash
     gcloud auth application-default login
     ```

5. **Create project structure**
```bash
mkdir -p tools prompts outputs
```

---

## 📋 Implementation Roadmap

### Phase 1: Core Setup
- [ ] Create `config.py` - Load environment variables
- [ ] Create `prompts/system_prompt.txt` - Copy from [LLM_PROMPTS.md](LLM_PROMPTS.md) Section 1
- [ ] Set up `.gitignore` (see PRD Section 6.1.3)

### Phase 2: Tool Implementation
- [ ] Implement `tools/bigquery_tool.py`
  - SQL query generation
  - BigQuery client integration
  - CSV export functionality
  - Error handling

- [ ] Implement `tools/visualization_tool.py`
  - CSV reading with pandas
  - Chart type detection (line vs bar)
  - Matplotlib chart generation
  - PNG export functionality

### Phase 3: Orchestrator
- [ ] Implement `main.py`
  - Anthropic client initialization
  - Tool definitions (from PRD Section 5.2)
  - Conversation loop (from LLM_PROMPTS.md Section 7.1)
  - Tool execution routing
  - Conversation history management

### Phase 4: Testing
- [ ] Test basic queries (Section 8.1 test cases)
- [ ] Test visualizations
- [ ] Test error handling
- [ ] Test multi-turn conversations

### Phase 5: Polish
- [ ] Add logging
- [ ] Optimize query performance
- [ ] Add usage examples
- [ ] Create demo video/screenshots

---

## 💻 Usage Examples

Once implemented, users can interact with natural language:

```
You: Show me temperatures in California for March 2024
Assistant: I'll query the NOAA weather data for California in March 2024...
[Creates ca_march_temps.csv with temperature data]

You: Now plot that data
Assistant: I'll create a line chart visualization...
[Creates ca_march_temps_chart.png]

You: Compare precipitation between US and Canada for summer
Assistant: I'll query both countries for June-August and create a comparison...
[Creates data and bar chart comparing the two countries]
```

---

## 🏗️ Project Structure

```
MyFirstAgent/
│
├── README.md                     # This file - project overview
├── PRD.md                        # Complete product requirements
├── LLM_PROMPTS.md               # Optimized prompts for implementation
├── PRD_APPENDIX.md              # Additional examples and details
│
├── .env                          # API keys and secrets (create this, not in git)
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
│
├── main.py                       # Main orchestrator (to be created)
├── config.py                     # Configuration loader (to be created)
│
├── tools/
│   ├── __init__.py              # Tool package init (to be created)
│   ├── bigquery_tool.py         # BigQuery implementation (to be created)
│   └── visualization_tool.py    # Visualization implementation (to be created)
│
├── prompts/
│   └── system_prompt.txt        # LLM system prompt (to be created)
│
└── outputs/                      # Generated files (created automatically)
    ├── *.csv                    # Query results
    └── *.png                    # Visualizations
```

---

## 🔧 Technical Details

### Technologies Used
- **LLM**: Anthropic Claude Sonnet 4.5 (via API)
- **Database**: Google BigQuery (public dataset)
- **Data Processing**: Pandas
- **Visualization**: Matplotlib
- **Environment**: Python 3.8+, python-dotenv

### Dataset Information
- **Source**: `bigquery-public-data.noaa_gsod.gsod2024`
- **Description**: NOAA Global Surface Summary of Day
- **Year**: 2024
- **Coverage**: Worldwide weather stations
- **Update Frequency**: Daily

### Key Features
1. **Natural Language Interface**: Users query with plain English
2. **Intelligent Tool Selection**: LLM chooses appropriate tools
3. **Automatic Visualizations**: Smart chart type selection
4. **Secure**: API keys and credentials outside code
5. **Fast**: Optimized for POC demonstration

---

## 🔐 Security Best Practices

1. **Never commit secrets**
   - Use `.env` for API keys
   - Add `.env` and `*.json` to `.gitignore`
   - Don't hardcode credentials in code

2. **BigQuery access**
   - Use service accounts with minimal permissions
   - Grant only "BigQuery Data Viewer" role
   - Rotate keys periodically

3. **API key management**
   - Store Anthropic API key in environment variables
   - Don't share keys in logs or error messages
   - Use separate keys for dev/prod

---

## 📊 Available Metrics

The system supports querying these weather metrics:

- **temp**: Mean temperature (°F)
- **max**: Maximum temperature (°F)
- **min**: Minimum temperature (°F)
- **prcp**: Precipitation amount (inches)
- **wdsp**: Mean wind speed (knots)
- **dewp**: Mean dew point (°F)
- **slp**: Mean sea level pressure (millibars)
- **sndp**: Snow depth (inches)

Plus location fields: station_id, name, country, state

And aggregation functions for metrics:
- **metric_aggregation**: `avg` (default), `min`, `max`

---

## 🎯 Sample Queries You Can Make

### Temperature Queries
- "Show me temperatures in New York for January"
- "Get monthly average temps for California in 2024"
- "What was the minimum temperature in Boston in February?"
- "Compare max temperatures between summer and winter in Texas"

### Precipitation Queries
- "Plot precipitation in Seattle for March"
- "Show me rainfall data for Florida during hurricane season"
- "Compare precipitation between California and Washington"

### Multi-Metric Queries
- "Get temperature, precipitation, and wind speed for Chicago in July"
- "Show all weather metrics for station ID 72295013874"

### Comparison Queries
- "Compare average temperatures between US and Canada"
- "Show precipitation differences between coastal and inland stations"

### Trend Analysis
- "Plot monthly temperature trends for New York in 2024"
- "Visualize wind speed patterns over the year in Texas"

---

## 🐛 Troubleshooting

### BigQuery Authentication Issues
```
Error: Could not authenticate with BigQuery
```
**Solution**: Check `GOOGLE_APPLICATION_CREDENTIALS` path is correct and service account has BigQuery Data Viewer role

### Missing API Key
```
Error: ANTHROPIC_API_KEY not found
```
**Solution**: Ensure `.env` file exists and contains valid API key

### No Data Returned
```
Query returned 0 rows
```
**Solution**: Check date range is within 2024 and location codes are valid (e.g., "CA" not "California")

### Visualization Fails
```
Error: CSV file not found
```
**Solution**: Run a query first to create the CSV file before visualization

---

## 📈 Future Enhancements

Potential improvements for future versions:

1. **Extended Dataset Coverage**
   - Support multiple years (2020-2024)
   - Include additional weather datasets

2. **Advanced Visualizations**
   - Heatmaps for geographic data
   - Multi-panel comparison charts
   - Interactive dashboards

3. **Enhanced Queries**
   - Statistical analysis (correlations, anomalies)
   - Predictive insights
   - Export to multiple formats (Excel, JSON)

4. **User Experience**
   - Web interface (Streamlit/Gradio)
   - Saved query templates
   - Report generation

5. **Performance**
   - Query result caching
   - Async processing for large queries
   - Database optimization

---

## 📝 License

This is a POC (Proof of Concept) project for educational purposes.

---

## 🤝 Contributing

This is a learning project. Feel free to:
- Experiment with different prompts
- Add new visualization types
- Optimize query performance
- Extend to other datasets

---

## 📞 Support

For questions about:
- **BigQuery**: See Google Cloud BigQuery documentation
- **Anthropic API**: See Anthropic Claude API documentation
- **Dataset**: See NOAA GSOD documentation

---

## 🎓 Learning Resources

- [Anthropic Claude API Docs](https://docs.anthropic.com/)
- [Google BigQuery Public Datasets](https://cloud.google.com/bigquery/public-data)
- [NOAA GSOD Documentation](https://www.ncei.noaa.gov/products/land-based-station/global-surface-summary-day)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)

---

**Ready to implement?** Start with Phase 1 of the Implementation Roadmap above, and refer to [PRD.md](PRD.md) and [LLM_PROMPTS.md](LLM_PROMPTS.md) for detailed specifications and prompts.

Good luck building your weather data agent! 🌤️📊
