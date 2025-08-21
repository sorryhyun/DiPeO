"""
Complex data processing pipeline example for Code Job node.
Demonstrates advanced features including data validation, transformation, and enrichment.
"""

import json
import csv
from io import StringIO
from typing import Dict, List, Any, Optional
from datetime import datetime
import statistics


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point - can be used for testing or single-function execution.
    """
    # This main function is kept for backward compatibility
    # The diagram will call specific functions directly
    return {"message": "Please call specific functions directly", "available_functions": [
        "parse_data", "quality_check", "transform_data", "enrich_data", "analyze_patterns", "handle_error"
    ]}


def parse_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse CSV data and prepare for quality check."""
    raw_data = inputs.get('raw_data', '')
    config_data = inputs.get('config_data', '{}')
    
    # Handle raw_data - could be CSV string or already-parsed JSON
    if isinstance(raw_data, str):
        # Try to parse as JSON first (in case DB already parsed it)
        try:
            data_rows = json.loads(raw_data)
            if not isinstance(data_rows, list):
                raise ValueError("Not a list")
        except (json.JSONDecodeError, ValueError):
            # Not JSON, parse as CSV
            csv_reader = csv.DictReader(StringIO(raw_data))
            data_rows = list(csv_reader)
    else:
        # Already parsed data
        data_rows = raw_data if isinstance(raw_data, list) else []
    
    # Parse config
    config = json.loads(config_data) if isinstance(config_data, str) else config_data
    
    # Enhanced validation
    total_rows = len(data_rows)
    valid_rows = []
    invalid_rows = []
    
    for idx, row in enumerate(data_rows):
        # Check for required fields based on config
        required_fields = config.get('required_fields', [])
        is_valid = True
        issues = []
        
        for field in required_fields:
            if not row.get(field) or row[field].strip() == '':
                is_valid = False
                issues.append(f"Missing {field}")
        
        # Type validation if specified in config
        field_types = config.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in row and row[field]:
                try:
                    if expected_type == 'number':
                        float(row[field])
                    elif expected_type == 'integer':
                        int(row[field])
                    elif expected_type == 'date':
                        # Simple date validation
                        datetime.strptime(row[field], '%Y-%m-%d')
                except ValueError:
                    is_valid = False
                    issues.append(f"Invalid {expected_type} in {field}")
        
        if is_valid:
            valid_rows.append(row)
        else:
            invalid_rows.append({"row_index": idx, "data": row, "issues": issues})
    
    # Calculate data statistics
    numeric_fields = [field for field, ftype in config.get('field_types', {}).items() 
                      if ftype in ['number', 'integer']]
    
    statistics_summary = {}
    for field in numeric_fields:
        values = []
        for row in valid_rows:
            try:
                values.append(float(row.get(field, 0)))
            except ValueError:
                pass
        
        if values:
            statistics_summary[field] = {
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values)
            }
    
    return {
        "total_rows": total_rows,
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
        "columns": list(data_rows[0].keys()) if data_rows else [],
        "data_rows": valid_rows,
        "invalid_data": invalid_rows[:10],  # First 10 invalid rows
        "statistics": statistics_summary,
        "config": config
    }


def extract_score(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract quality score from the person job's quality check result."""
    print("DEBUG: extract_score function called!")
    print(f"DEBUG: Inputs keys: {list(inputs.keys())}")
    quality_result = inputs.get('quality_result', '{}')
    
    # Debug logging
    print(f"DEBUG: Raw quality_result type: {type(quality_result)}")
    print(f"DEBUG: Raw quality_result content: {quality_result[:200] if isinstance(quality_result, str) else quality_result}")
    
    quality_score = 0
    quality_issues = []
    parsed_data = {}
    parse_info = {"method": "unknown", "raw_input": str(quality_result)[:200]}
    
    # Try multiple parsing strategies
    if isinstance(quality_result, str):
        # Strategy 1: Try direct JSON parsing
        try:
            quality_data = json.loads(quality_result)
            quality_score = quality_data.get("score", 0)
            quality_issues = quality_data.get("issues", [])
            # Extract parsed_data from the quality result
            parsed_data = quality_data.get("parsed_data", {})
            parse_info["method"] = "direct_json"
        except json.JSONDecodeError:
            # Strategy 2: Try to find JSON in the text
            import re
            # Look for the start of a JSON object and capture everything to the end
            # This handles nested objects properly
            json_start = quality_result.find('{')
            if json_start != -1:
                # Try to parse from the first { to the end
                try:
                    quality_data = json.loads(quality_result[json_start:])
                    quality_score = quality_data.get("score", 0)
                    quality_issues = quality_data.get("issues", [])
                    parsed_data = quality_data.get("parsed_data", {})
                    parse_info["method"] = "extracted_json_from_start"
                except json.JSONDecodeError:
                    # If that fails, try to find a balanced JSON object
                    brace_count = 0
                    end_pos = json_start
                    for i, char in enumerate(quality_result[json_start:], json_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end_pos = i + 1
                                break
                    
                    if end_pos > json_start:
                        try:
                            quality_data = json.loads(quality_result[json_start:end_pos])
                            quality_score = quality_data.get("score", 0)
                            quality_issues = quality_data.get("issues", [])
                            parsed_data = quality_data.get("parsed_data", {})
                            parse_info["method"] = "extracted_balanced_json"
                        except:
                            pass
            
            # Strategy 3: Try to extract score from text
            if quality_score == 0:
                score_match = re.search(r'score[:\s]*(\d+)', quality_result, re.IGNORECASE)
                if score_match:
                    quality_score = int(score_match.group(1))
                    parse_info["method"] = "regex_extraction"
                    # Try to extract issues
                    issues_match = re.findall(r'[-•*]\s*(.+?)(?=[-•*]|$)', quality_result)
                    if issues_match:
                        quality_issues = [issue.strip() for issue in issues_match]
            
            # Strategy 4: Default if nothing works
            if quality_score == 0:
                quality_issues = ["Failed to parse quality result", f"Raw result: {quality_result[:100]}..."]
                parse_info["method"] = "parse_failed"
    else:
        # Handle dict/object input
        quality_score = quality_result.get("score", 0) if isinstance(quality_result, dict) else 0
        quality_issues = quality_result.get("issues", []) if isinstance(quality_result, dict) else []
        parsed_data = quality_result.get("parsed_data", {}) if isinstance(quality_result, dict) else {}
        parse_info["method"] = "dict_input"
    
    # Get the parsed_data directly from inputs (new connection from Parse Data node)
    input_parsed_data = inputs.get('parsed_data', {})
    
    # Extract data from parsed_data for downstream use
    data_rows = input_parsed_data.get('data_rows', [])
    config = input_parsed_data.get('config', {})
    
    # Set result variables for downstream nodes
    result = {
        "quality_score": quality_score,
        "quality_issues": quality_issues,
        "data_rows": data_rows,
        "config": config,
        "parsed_data": input_parsed_data,
        "parse_info": parse_info  # For debugging
    }
    
    print(f"DEBUG: Extract Score returning: quality_score={quality_score}, has_data_rows={len(data_rows)}, has_config={bool(config)}")
    return result


def transform_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Transform data according to business rules."""
    # Debug logging
    print(f"DEBUG transform_data: inputs keys = {list(inputs.keys())}")
    print(f"DEBUG transform_data: processing_result type = {type(inputs.get('processing_result'))}")
    print(f"DEBUG transform_data: processing_result value = {inputs.get('processing_result')}")
    
    # Data comes from the condition check which passes through Extract Score output
    # Check all possible input keys to understand the structure
    for key, value in inputs.items():
        print(f"DEBUG transform_data: input '{key}' = {str(value)[:200] if isinstance(value, (dict, list, str)) else value}")
    
    # Get processing_result directly from inputs
    processing_result = inputs.get('processing_result', {})
    
    # If it's not a dict, something went wrong
    if not isinstance(processing_result, dict):
        print(f"DEBUG transform_data: processing_result is not a dict, got {type(processing_result)}")
        processing_result = {}
    
    data_rows = processing_result.get('data_rows', [])
    config = processing_result.get('config', {})
    quality_score = processing_result.get('quality_score', 0)
    
    print(f"DEBUG transform_data: data_rows count = {len(data_rows)}")
    print(f"DEBUG transform_data: quality_score = {quality_score}")
    
    if quality_score < 70:
        return {
            "error": "Quality score too low for transformation",
            "quality_score": quality_score,
            "issues": inputs.get('quality_issues', [])
        }
    
    # Apply transformations based on config
    transformation_rules = config.get('transformations', {})
    transformed_data = []
    
    for row in data_rows:
        transformed_row = row.copy()
        
        # Apply field mappings
        field_mappings = transformation_rules.get('field_mappings', {})
        for old_field, new_field in field_mappings.items():
            if old_field in transformed_row:
                transformed_row[new_field] = transformed_row.pop(old_field)
        
        # Apply calculations
        calculations = transformation_rules.get('calculations', {})
        for new_field, formula in calculations.items():
            # Simple calculation support (e.g., "field1 + field2")
            try:
                # This is a simplified calculation - in production use safer evaluation
                if '+' in formula:
                    fields = [f.strip() for f in formula.split('+')]
                    value = sum(float(transformed_row.get(f, 0)) for f in fields)
                    transformed_row[new_field] = value
            except:
                pass
        
        # Apply filters
        filters = transformation_rules.get('filters', {})
        include_row = True
        for field, condition in filters.items():
            if field in transformed_row:
                # Simple filter support
                if condition.startswith('>'):
                    threshold = float(condition[1:])
                    try:
                        if float(transformed_row[field]) <= threshold:
                            include_row = False
                    except (ValueError, KeyError):
                        pass
        
        if include_row:
            transformed_data.append(transformed_row)
    
    result = {
        "transformed_count": len(transformed_data),
        "original_count": len(data_rows),
        "data": transformed_data
    }
    
    print(f"DEBUG transform_data: returning {len(transformed_data)} transformed rows")
    print(f"DEBUG transform_data: first row = {transformed_data[0] if transformed_data else 'none'}")
    
    return result


def enrich_data(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich data with external API information."""
    print(f"DEBUG enrich_data: inputs keys = {list(inputs.keys())}")
    print(f"DEBUG enrich_data: transformed_data type = {type(inputs.get('transformed_data'))}")
    print(f"DEBUG enrich_data: transformed_data value = {inputs.get('transformed_data')}")
    print(f"DEBUG enrich_data: api_response type = {type(inputs.get('api_response'))}")
    
    # Handle transformed_data - now it should be an object with 'data' key
    transformed_data_input = inputs.get('transformed_data', {})
    if isinstance(transformed_data_input, dict):
        transformed_data = transformed_data_input.get('data', [])
    else:
        # Fallback for any unexpected input
        transformed_data = []
    
    api_response = inputs.get('api_response', '{}')
    
    # Parse API response
    try:
        api_data = json.loads(api_response) if isinstance(api_response, str) else api_response
        exchange_rates = api_data.get('rates', {})
    except json.JSONDecodeError as e:
        print(f"DEBUG enrich_data: JSON decode error: {e}")
        print(f"DEBUG enrich_data: api_response content: {api_response[:200]}")
        return {
            "error": "Failed to parse API response",
            "details": str(e),
            "api_response_preview": api_response[:200] if isinstance(api_response, str) else str(api_response)
        }
    
    # Enrich each record
    enriched_data = []
    enrichment_stats = {
        "records_enriched": 0,
        "fields_added": set(),
        "currencies_converted": []
    }
    
    for item in transformed_data:
        enriched_item = item.copy()
        
        # Currency conversion enrichment
        for field, value in item.items():
            if 'amount' in field.lower() or 'price' in field.lower():  # Handle both amount_usd and price_usd
                try:
                    usd_amount = float(value)
                    # Add conversions for major currencies
                    for currency, rate in [('EUR', exchange_rates.get('EUR', 0.85)),
                                          ('GBP', exchange_rates.get('GBP', 0.73)),
                                          ('JPY', exchange_rates.get('JPY', 110))]:
                        new_field = field.replace('usd', currency.lower())
                        enriched_item[new_field] = round(usd_amount * rate, 2)
                        enrichment_stats["fields_added"].add(new_field)
                        if currency not in enrichment_stats["currencies_converted"]:
                            enrichment_stats["currencies_converted"].append(currency)
                    enrichment_stats["records_enriched"] += 1
                except ValueError:
                    pass
        
        # Add metadata
        enriched_item['enriched_at'] = datetime.now().isoformat()
        enriched_item['exchange_rate_date'] = api_data.get('date', 'unknown')
        
        enriched_data.append(enriched_item)
    
    result = {
        "processed_at": api_data.get('date', datetime.now().isoformat()),
        "total_records": len(enriched_data),
        "enrichment_stats": {
            "records_enriched": enrichment_stats["records_enriched"],
            "fields_added": list(enrichment_stats["fields_added"]),
            "currencies_converted": enrichment_stats["currencies_converted"]
        },
        "data": enriched_data
    }
    
    print(f"DEBUG enrich_data: returning result with {len(enriched_data)} records")
    print(f"DEBUG enrich_data: result keys = {list(result.keys())}")
    
    return result


def analyze_patterns(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze patterns in the enriched data."""
    # Debug logging
    print(f"DEBUG analyze_patterns: inputs keys = {list(inputs.keys())}")
    print(f"DEBUG analyze_patterns: enriched_data type = {type(inputs.get('enriched_data'))}")
    print(f"DEBUG analyze_patterns: enriched_data value = {str(inputs.get('enriched_data'))[:200]}")
    
    enriched_result = inputs.get('enriched_data', {})
    
    # Handle case where enriched_result might be a string (error message)
    if isinstance(enriched_result, str):
        return {
            "error": "Invalid input format",
            "details": f"Expected dict but got string: {enriched_result[:100]}",
            "summary": {"total_records": 0, "analysis_timestamp": datetime.now().isoformat()},
            "patterns": ["Error in data processing"],
            "anomalies": [],
            "recommendations": ["Check data processing pipeline"]
        }
    
    enriched_data = enriched_result.get('data', [])
    
    analysis = {
        "summary": {
            "total_records": len(enriched_data),
            "analysis_timestamp": datetime.now().isoformat()
        },
        "patterns": [],
        "anomalies": [],
        "recommendations": []
    }
    
    if not enriched_data:
        analysis["patterns"].append("No data available for analysis")
        return analysis
    
    # Analyze numeric fields
    numeric_fields = {}
    for row in enriched_data[:10]:  # Sample first 10 rows to identify numeric fields
        for field, value in row.items():
            try:
                float(value)
                if field not in numeric_fields:
                    numeric_fields[field] = []
            except:
                pass
    
    # Collect values for numeric fields
    for row in enriched_data:
        for field in numeric_fields:
            try:
                numeric_fields[field].append(float(row.get(field, 0)))
            except:
                pass
    
    # Pattern analysis
    for field, values in numeric_fields.items():
        if values:
            mean_val = statistics.mean(values)
            median_val = statistics.median(values)
            std_val = statistics.stdev(values) if len(values) > 1 else 0
            
            # Detect patterns
            if abs(mean_val - median_val) > std_val:
                analysis["patterns"].append(f"{field} shows skewed distribution")
            
            # Detect anomalies (values beyond 2 standard deviations)
            anomaly_count = sum(1 for v in values if abs(v - mean_val) > 2 * std_val)
            if anomaly_count > 0:
                analysis["anomalies"].append({
                    "field": field,
                    "anomaly_count": anomaly_count,
                    "percentage": f"{(anomaly_count/len(values))*100:.1f}%"
                })
    
    # Currency analysis if available
    currency_fields = [f for f in enriched_data[0].keys() if any(curr in f.lower() for curr in ['eur', 'gbp', 'jpy'])]
    if currency_fields:
        analysis["patterns"].append(f"Data enriched with {len(currency_fields)} currency conversions")
    
    # Generate recommendations
    if analysis["anomalies"]:
        analysis["recommendations"].append("Review detected anomalies for data quality issues")
    
    if len(enriched_data) < 100:
        analysis["recommendations"].append("Consider collecting more data for robust analysis")
    
    if not analysis["recommendations"]:
        analysis["recommendations"].append("Data quality appears good, proceed with downstream processing")
    
    return analysis


def handle_error(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Handle low quality data and generate error report."""
    # Receives data from the false condition path
    processing_result = inputs.get('processing_result', {})
    quality_score = processing_result.get('quality_score', 0)
    quality_issues = processing_result.get('quality_issues', [])
    
    return {
        "status": "failed",
        "reason": "Data quality below threshold",
        "quality_score": quality_score,
        "issues": quality_issues,
        "timestamp": datetime.now().isoformat(),
        "recommendation": "Please clean the source data and retry"
    }