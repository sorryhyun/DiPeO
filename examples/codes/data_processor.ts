/**
 * Complex data processing pipeline example for Code Job node.
 * Demonstrates advanced features including data validation, transformation, and enrichment.
 */

interface InputData {
  [key: string]: any;
}

interface DataRow {
  [key: string]: string | number;
}

interface Config {
  required_fields?: string[];
  field_types?: { [key: string]: string };
  transformations?: {
    field_mappings?: { [key: string]: string };
    calculations?: { [key: string]: string };
    filters?: { [key: string]: string };
  };
}

interface Statistics {
  mean: number;
  median: number;
  std_dev: number;
  min: number;
  max: number;
}

interface InvalidRow {
  row_index: number;
  data: DataRow;
  issues: string[];
}

interface ParsedData {
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  columns: string[];
  data_rows: DataRow[];
  invalid_data: InvalidRow[];
  statistics: { [key: string]: Statistics };
  config: Config;
}

interface ProcessingResult {
  quality_score: number;
  quality_issues: string[];
  data_rows: DataRow[];
  config: Config;
  parsed_data: ParsedData;
  parse_info: { method: string; raw_input: string };
}

interface TransformedData {
  transformed_count: number;
  original_count: number;
  data: DataRow[];
}

interface EnrichedData {
  processed_at: string;
  total_records: number;
  enrichment_stats: {
    records_enriched: number;
    fields_added: string[];
    currencies_converted: string[];
  };
  data: DataRow[];
}

interface AnalysisResult {
  summary: {
    total_records: number;
    analysis_timestamp: string;
  };
  patterns: string[];
  anomalies: Array<{
    field: string;
    anomaly_count: number;
    percentage: string;
  }>;
  recommendations: string[];
}

interface ErrorResult {
  status: string;
  reason: string;
  quality_score: number;
  issues: string[];
  timestamp: string;
  recommendation: string;
}

export function main(inputs: InputData): InputData {
  /**
   * Main entry point - can be used for testing or single-function execution.
   */
  return {
    message: "Please call specific functions directly",
    available_functions: [
      "parse_data", "quality_check", "transform_data", "enrich_data", "analyze_patterns", "handle_error"
    ]
  };
}

export function parse_data(inputs: InputData): ParsedData {
  /**Parse CSV data and prepare for quality check.*/
  const raw_data = inputs.raw_data || '';
  const config_data = inputs.config_data || '{}';
  
  let data_rows: DataRow[] = [];
  
  // Handle raw_data - could be CSV string or already-parsed JSON
  if (typeof raw_data === 'string') {
    // Try to parse as JSON first (in case DB already parsed it)
    try {
      const parsed = JSON.parse(raw_data);
      if (Array.isArray(parsed)) {
        data_rows = parsed;
      } else {
        throw new Error("Not a list");
      }
    } catch {
      // Not JSON, parse as CSV
      data_rows = parseCSV(raw_data);
    }
  } else {
    // Already parsed data
    data_rows = Array.isArray(raw_data) ? raw_data : [];
  }
  
  // Parse config
  const config: Config = typeof config_data === 'string' ? JSON.parse(config_data) : config_data;
  
  // Enhanced validation
  const total_rows = data_rows.length;
  const valid_rows: DataRow[] = [];
  const invalid_rows: InvalidRow[] = [];
  
  data_rows.forEach((row, idx) => {
    // Check for required fields based on config
    const required_fields = config.required_fields || [];
    let is_valid = true;
    const issues: string[] = [];
    
    for (const field of required_fields) {
      if (!row[field] || String(row[field]).trim() === '') {
        is_valid = false;
        issues.push(`Missing ${field}`);
      }
    }
    
    // Type validation if specified in config
    const field_types = config.field_types || {};
    for (const [field, expected_type] of Object.entries(field_types)) {
      if (field in row && row[field]) {
        try {
          if (expected_type === 'number') {
            const num = parseFloat(String(row[field]));
            if (isNaN(num)) throw new Error();
          } else if (expected_type === 'integer') {
            const int = parseInt(String(row[field]));
            if (isNaN(int)) throw new Error();
          } else if (expected_type === 'date') {
            // Simple date validation
            const date = new Date(String(row[field]));
            if (isNaN(date.getTime())) throw new Error();
          }
        } catch {
          is_valid = false;
          issues.push(`Invalid ${expected_type} in ${field}`);
        }
      }
    }
    
    if (is_valid) {
      valid_rows.push(row);
    } else {
      invalid_rows.push({ row_index: idx, data: row, issues });
    }
  });
  
  // Calculate data statistics
  const numeric_fields = Object.entries(config.field_types || {})
    .filter(([_, ftype]) => ftype === 'number' || ftype === 'integer')
    .map(([field, _]) => field);
  
  const statistics_summary: { [key: string]: Statistics } = {};
  for (const field of numeric_fields) {
    const values: number[] = [];
    for (const row of valid_rows) {
      try {
        const val = parseFloat(String(row[field] || 0));
        if (!isNaN(val)) values.push(val);
      } catch {
        // Skip invalid values
      }
    }
    
    if (values.length > 0) {
      statistics_summary[field] = calculateStatistics(values);
    }
  }
  
  return {
    total_rows,
    valid_rows: valid_rows.length,
    invalid_rows: invalid_rows.length,
    columns: data_rows.length > 0 ? Object.keys(data_rows[0]) : [],
    data_rows: valid_rows,
    invalid_data: invalid_rows.slice(0, 10), // First 10 invalid rows
    statistics: statistics_summary,
    config
  };
}

export function extract_score(inputs: InputData): ProcessingResult {
  /**Extract quality score from the person job's quality check result.*/
  // Remove console.log debug statements as they interfere with JSON output
  const quality_result = inputs.quality_result || '{}';
  
  let quality_score = 0;
  let quality_issues: string[] = [];
  let parsed_data: any = {};
  const parse_info = { method: "unknown", raw_input: String(quality_result).substring(0, 200) };
  
  // Try multiple parsing strategies
  if (typeof quality_result === 'string') {
    // Strategy 1: Try direct JSON parsing
    try {
      const quality_data = JSON.parse(quality_result);
      quality_score = quality_data.score || 0;
      quality_issues = quality_data.issues || [];
      parsed_data = quality_data.parsed_data || {};
      parse_info.method = "direct_json";
    } catch {
      // Strategy 2: Try to find JSON in the text
      const json_start = quality_result.indexOf('{');
      if (json_start !== -1) {
        // Try to parse from the first { to the end
        try {
          const quality_data = JSON.parse(quality_result.substring(json_start));
          quality_score = quality_data.score || 0;
          quality_issues = quality_data.issues || [];
          parsed_data = quality_data.parsed_data || {};
          parse_info.method = "extracted_json_from_start";
        } catch {
          // If that fails, try to find a balanced JSON object
          let brace_count = 0;
          let end_pos = json_start;
          for (let i = json_start; i < quality_result.length; i++) {
            const char = quality_result[i];
            if (char === '{') {
              brace_count++;
            } else if (char === '}') {
              brace_count--;
              if (brace_count === 0) {
                end_pos = i + 1;
                break;
              }
            }
          }
          
          if (end_pos > json_start) {
            try {
              const quality_data = JSON.parse(quality_result.substring(json_start, end_pos));
              quality_score = quality_data.score || 0;
              quality_issues = quality_data.issues || [];
              parsed_data = quality_data.parsed_data || {};
              parse_info.method = "extracted_balanced_json";
            } catch {
              // Continue to next strategy
            }
          }
        }
      }
      
      // Strategy 3: Try to extract score from text
      if (quality_score === 0) {
        const score_match = quality_result.match(/score[:\s]*(\d+)/i);
        if (score_match) {
          quality_score = parseInt(score_match[1]);
          parse_info.method = "regex_extraction";
          // Try to extract issues
          const issues_match = quality_result.match(/[-•*]\s*(.+?)(?=[-•*]|$)/g);
          if (issues_match) {
            quality_issues = issues_match.map(issue => issue.replace(/^[-•*]\s*/, '').trim());
          }
        }
      }
      
      // Strategy 4: Default if nothing works
      if (quality_score === 0) {
        quality_issues = ["Failed to parse quality result", `Raw result: ${quality_result.substring(0, 100)}...`];
        parse_info.method = "parse_failed";
      }
    }
  } else {
    // Handle dict/object input
    if (typeof quality_result === 'object' && quality_result !== null) {
      quality_score = quality_result.score || 0;
      quality_issues = quality_result.issues || [];
      parsed_data = quality_result.parsed_data || {};
    }
    parse_info.method = "dict_input";
  }
  
  // Get the parsed_data directly from inputs (new connection from Parse Data node)
  const input_parsed_data = inputs.parsed_data || {};
  
  // Extract data from parsed_data for downstream use
  const data_rows = input_parsed_data.data_rows || [];
  const config = input_parsed_data.config || {};
  
  // Set result variables for downstream nodes
  const result: ProcessingResult = {
    quality_score,
    quality_issues,
    data_rows,
    config,
    parsed_data: input_parsed_data,
    parse_info // For debugging
  };
  
  return result;
}

export function transform_data(inputs: InputData): TransformedData | { error: string; quality_score: number; issues: string[] } {
  /**Transform data according to business rules.*/
  // Data comes from the condition check which passes through Extract Score output
  
  // Get processing_result directly from inputs
  let processing_result = inputs.processing_result || {};
  
  // If it's not an object, something went wrong
  if (typeof processing_result !== 'object' || processing_result === null) {
    processing_result = {};
  }
  
  const data_rows = processing_result.data_rows || [];
  const config = processing_result.config || {};
  const quality_score = processing_result.quality_score || 0;
  
  if (quality_score < 70) {
    return {
      error: "Quality score too low for transformation",
      quality_score,
      issues: inputs.quality_issues || []
    };
  }
  
  // Apply transformations based on config
  const transformation_rules = config.transformations || {};
  const transformed_data: DataRow[] = [];
  
  for (const row of data_rows) {
    const transformed_row: DataRow = { ...row };
    
    // Apply field mappings
    const field_mappings = transformation_rules.field_mappings || {};
    for (const [old_field, new_field] of Object.entries(field_mappings)) {
      if (old_field in transformed_row) {
        transformed_row[new_field] = transformed_row[old_field];
        delete transformed_row[old_field];
      }
    }
    
    // Apply calculations
    const calculations = transformation_rules.calculations || {};
    for (const [new_field, formula] of Object.entries(calculations)) {
      // Simple calculation support (e.g., "field1 + field2")
      try {
        // This is a simplified calculation - in production use safer evaluation
        if (formula.includes('+')) {
          const fields = formula.split('+').map(f => f.trim());
          const value = fields.reduce((sum, f) => sum + parseFloat(String(transformed_row[f] || 0)), 0);
          transformed_row[new_field] = value;
        }
      } catch {
        // Skip failed calculations
      }
    }
    
    // Apply filters
    const filters = transformation_rules.filters || {};
    let include_row = true;
    for (const [field, condition] of Object.entries(filters)) {
      if (field in transformed_row) {
        // Simple filter support
        if (condition.startsWith('>')) {
          const threshold = parseFloat(condition.substring(1));
          try {
            if (parseFloat(String(transformed_row[field])) <= threshold) {
              include_row = false;
            }
          } catch {
            // Skip invalid comparisons
          }
        }
      }
    }
    
    if (include_row) {
      transformed_data.push(transformed_row);
    }
  }
  
  const result: TransformedData = {
    transformed_count: transformed_data.length,
    original_count: data_rows.length,
    data: transformed_data
  };
  
  return result;
}

export function enrich_data(inputs: InputData): EnrichedData | { error: string; details: string; api_response_preview: string } {
  /**Enrich data with external API information.*/
  // Handle transformed_data - now it should be an object with 'data' key
  const transformed_data_input = inputs.transformed_data || {};
  let transformed_data: DataRow[] = [];
  if (typeof transformed_data_input === 'object' && transformed_data_input !== null && 'data' in transformed_data_input) {
    transformed_data = transformed_data_input.data || [];
  }
  
  const api_response = inputs.api_response || '{}';
  
  // Parse API response
  let api_data: any;
  let exchange_rates: { [key: string]: number } = {};
  try {
    api_data = typeof api_response === 'string' ? JSON.parse(api_response) : api_response;
    exchange_rates = api_data.rates || {};
  } catch (e: any) {
    return {
      error: "Failed to parse API response",
      details: String(e),
      api_response_preview: typeof api_response === 'string' ? api_response.substring(0, 200) : String(api_response)
    };
  }
  
  // Enrich each record
  const enriched_data: DataRow[] = [];
  const enrichment_stats = {
    records_enriched: 0,
    fields_added: new Set<string>(),
    currencies_converted: [] as string[]
  };
  
  for (const item of transformed_data) {
    const enriched_item: DataRow = { ...item };
    
    // Currency conversion enrichment
    for (const [field, value] of Object.entries(item)) {
      if (field.toLowerCase().includes('amount') || field.toLowerCase().includes('price')) {
        try {
          const usd_amount = parseFloat(String(value));
          // Add conversions for major currencies
          const conversions: [string, number][] = [
            ['EUR', exchange_rates.EUR || 0.85],
            ['GBP', exchange_rates.GBP || 0.73],
            ['JPY', exchange_rates.JPY || 110]
          ];
          
          for (const [currency, rate] of conversions) {
            const new_field = field.replace('usd', currency.toLowerCase());
            enriched_item[new_field] = Math.round(usd_amount * rate * 100) / 100;
            enrichment_stats.fields_added.add(new_field);
            if (!enrichment_stats.currencies_converted.includes(currency)) {
              enrichment_stats.currencies_converted.push(currency);
            }
          }
          enrichment_stats.records_enriched++;
        } catch {
          // Skip invalid values
        }
      }
    }
    
    // Add metadata
    enriched_item['enriched_at'] = new Date().toISOString();
    enriched_item['exchange_rate_date'] = api_data.date || 'unknown';
    
    enriched_data.push(enriched_item);
  }
  
  const result: EnrichedData = {
    processed_at: api_data.date || new Date().toISOString(),
    total_records: enriched_data.length,
    enrichment_stats: {
      records_enriched: enrichment_stats.records_enriched,
      fields_added: Array.from(enrichment_stats.fields_added),
      currencies_converted: enrichment_stats.currencies_converted
    },
    data: enriched_data
  };
  
  return result;
}

export function analyze_patterns(inputs: InputData): AnalysisResult {
  /**Analyze patterns in the enriched data.*/
  const enriched_result = inputs.enriched_data || {};
  
  // Handle case where enriched_result might be a string (error message)
  if (typeof enriched_result === 'string') {
    return {
      summary: {
        total_records: 0,
        analysis_timestamp: new Date().toISOString()
      },
      patterns: ["Error in data processing"],
      anomalies: [],
      recommendations: ["Check data processing pipeline"]
    };
  }
  
  const enriched_data = enriched_result.data || [];
  
  const analysis: AnalysisResult = {
    summary: {
      total_records: enriched_data.length,
      analysis_timestamp: new Date().toISOString()
    },
    patterns: [],
    anomalies: [],
    recommendations: []
  };
  
  if (enriched_data.length === 0) {
    analysis.patterns.push("No data available for analysis");
    return analysis;
  }
  
  // Analyze numeric fields
  const numeric_fields: { [key: string]: number[] } = {};
  
  // Sample first 10 rows to identify numeric fields
  const sample_rows = enriched_data.slice(0, 10);
  for (const row of sample_rows) {
    for (const [field, value] of Object.entries(row)) {
      const num = parseFloat(String(value));
      if (!isNaN(num)) {
        if (!(field in numeric_fields)) {
          numeric_fields[field] = [];
        }
      }
    }
  }
  
  // Collect values for numeric fields
  for (const row of enriched_data) {
    for (const field of Object.keys(numeric_fields)) {
      const num = parseFloat(String(row[field] || 0));
      if (!isNaN(num)) {
        numeric_fields[field].push(num);
      }
    }
  }
  
  // Pattern analysis
  for (const [field, values] of Object.entries(numeric_fields)) {
    if (values.length > 0) {
      const stats = calculateStatistics(values);
      
      // Detect patterns
      if (Math.abs(stats.mean - stats.median) > stats.std_dev) {
        analysis.patterns.push(`${field} shows skewed distribution`);
      }
      
      // Detect anomalies (values beyond 2 standard deviations)
      const anomaly_count = values.filter(v => Math.abs(v - stats.mean) > 2 * stats.std_dev).length;
      if (anomaly_count > 0) {
        analysis.anomalies.push({
          field,
          anomaly_count,
          percentage: `${(anomaly_count / values.length * 100).toFixed(1)}%`
        });
      }
    }
  }
  
  // Currency analysis if available
  if (enriched_data.length > 0) {
    const currency_fields = Object.keys(enriched_data[0]).filter(f => 
      ['eur', 'gbp', 'jpy'].some(curr => f.toLowerCase().includes(curr))
    );
    if (currency_fields.length > 0) {
      analysis.patterns.push(`Data enriched with ${currency_fields.length} currency conversions`);
    }
  }
  
  // Generate recommendations
  if (analysis.anomalies.length > 0) {
    analysis.recommendations.push("Review detected anomalies for data quality issues");
  }
  
  if (enriched_data.length < 100) {
    analysis.recommendations.push("Consider collecting more data for robust analysis");
  }
  
  if (analysis.recommendations.length === 0) {
    analysis.recommendations.push("Data quality appears good, proceed with downstream processing");
  }
  
  return analysis;
}

export function handle_error(inputs: InputData): ErrorResult {
  /**Handle low quality data and generate error report.*/
  // Receives data from the false condition path
  const processing_result = inputs.processing_result || {};
  const quality_score = processing_result.quality_score || 0;
  const quality_issues = processing_result.quality_issues || [];
  
  return {
    status: "failed",
    reason: "Data quality below threshold",
    quality_score,
    issues: quality_issues,
    timestamp: new Date().toISOString(),
    recommendation: "Please clean the source data and retry"
  };
}

// Helper functions

function parseCSV(csvString: string): DataRow[] {
  const lines = csvString.trim().split('\n');
  if (lines.length === 0) return [];
  
  const headers = lines[0].split(',').map(h => h.trim());
  const rows: DataRow[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    const row: DataRow = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || '';
    });
    rows.push(row);
  }
  
  return rows;
}

function calculateStatistics(values: number[]): Statistics {
  if (values.length === 0) {
    return { mean: 0, median: 0, std_dev: 0, min: 0, max: 0 };
  }
  
  const sorted = [...values].sort((a, b) => a - b);
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / values.length;
  
  const median = values.length % 2 === 0
    ? (sorted[values.length / 2 - 1] + sorted[values.length / 2]) / 2
    : sorted[Math.floor(values.length / 2)];
  
  const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
  const std_dev = Math.sqrt(variance);
  
  return {
    mean,
    median,
    std_dev: values.length > 1 ? std_dev : 0,
    min: Math.min(...values),
    max: Math.max(...values)
  };
}