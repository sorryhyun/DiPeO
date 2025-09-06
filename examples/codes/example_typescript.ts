/**
 * Example TypeScript file for Code Job node execution.
 */

interface Inputs {
  [key: string]: any;
}

interface Result {
  message: string;
  processedData?: any;
  timestamp: string;
  inputKeys: string[];
}

export function main(inputs: Inputs): Result {
  // Access inputs by connection labels
  const dataSource = inputs.data_source || "No data source";
  const config = inputs.config || {};

  // Process the data
  const result: Result = {
    message: `TypeScript processed data from: ${dataSource}`,
    timestamp: new Date().toISOString(),
    inputKeys: Object.keys(inputs),
  };

  // Example: Transform data if present
  if (inputs.transform_data) {
    result.processedData = {
      original: inputs.transform_data,
      transformed: typeof inputs.transform_data === 'string'
        ? inputs.transform_data.split('').reverse().join('')
        : inputs.transform_data
    };
  }

  // Example: Handle array data
  if (Array.isArray(inputs.items)) {
    result.processedData = {
      ...result.processedData,
      itemCount: inputs.items.length,
      items: inputs.items.map((item: any, index: number) => ({
        index,
        value: item,
        type: typeof item
      }))
    };
  }

  return result;
}

// Alternative function for text processing
export function processJson(inputs: Inputs): object {
  const jsonString = inputs.json_data || "{}";
  try {
    const parsed = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;
    return {
      success: true,
      data: parsed,
      keys: Object.keys(parsed)
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      input: jsonString
    };
  }
}
