/**
 * Native YAML format converter for DiPeO diagrams
 * 
 * Performs direct JSON-to-YAML conversion maintaining the same structure
 * Compatible with tool.py for seamless interoperability
 */

import { stringify, parse } from 'yaml';
import type { ConverterDiagram } from '../types';
import { JsonConverter, type ExportFormat } from './json';
import { YAML_STRINGIFY_OPTIONS } from '../constants';

export class YamlConverter {
  private jsonConverter = new JsonConverter();

  /**
   * Serialize diagram to YAML string
   * Uses the same structure as JSON for compatibility
   */
  serialize(diagram: ConverterDiagram): string {
    // Convert to JSON export format first
    const jsonFormat = this.jsonConverter.toExportFormat(diagram);
    
    // Convert to YAML maintaining the same structure
    return stringify(jsonFormat, YAML_STRINGIFY_OPTIONS);
  }

  /**
   * Deserialize diagram from YAML string
   */
  deserialize(yamlString: string): ConverterDiagram {
    // Parse YAML to get the same structure as JSON
    const data = parse(yamlString) as ExportFormat;
    
    // Use JSON converter to handle the import
    return this.jsonConverter.fromExportFormat(data);
  }
}

// Legacy static class for backward compatibility
export class Yaml {
  private static converter = new YamlConverter();

  static toYAML(diagram: ConverterDiagram): string {
    return this.converter.serialize(diagram);
  }

  static fromYAML(yamlString: string): ConverterDiagram {
    return this.converter.deserialize(yamlString);
  }
}