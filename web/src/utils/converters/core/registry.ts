import { DomainFormatConverter, SupportedFormat, FormatMetadata } from './types';

/**
 * Centralized converter registry for managing all format converters
 */
export class ConverterRegistry {
  private converters = new Map<SupportedFormat, DomainFormatConverter>();
  private metadata = new Map<SupportedFormat, FormatMetadata>();

  /**
   * Register a converter for a specific format
   */
  register(
    format: SupportedFormat, 
    converter: DomainFormatConverter,
    metadata?: Partial<FormatMetadata>
  ): void {
    this.converters.set(format, converter);
    
    // Set metadata
    this.metadata.set(format, {
      name: converter.formatName,
      displayName: metadata?.displayName || converter.formatName,
      extension: converter.fileExtension,
      description: metadata?.description || `${converter.formatName} format`
    });
  }

  /**
   * Get a converter for a specific format
   */
  get(format: SupportedFormat): DomainFormatConverter {
    const converter = this.converters.get(format);
    if (!converter) {
      throw new Error(`No converter registered for format: ${format}`);
    }
    return converter;
  }

  /**
   * Check if a converter is registered for a format
   */
  has(format: SupportedFormat): boolean {
    return this.converters.has(format);
  }

  /**
   * Get metadata for a format
   */
  getMetadata(format: SupportedFormat): FormatMetadata | undefined {
    return this.metadata.get(format);
  }

  /**
   * Get all registered formats
   */
  getFormats(): SupportedFormat[] {
    return Array.from(this.converters.keys());
  }

  /**
   * Get all format metadata
   */
  getAllMetadata(): Map<SupportedFormat, FormatMetadata> {
    return new Map(this.metadata);
  }

  /**
   * Clear all registered converters
   */
  clear(): void {
    this.converters.clear();
    this.metadata.clear();
  }
}

// Export singleton instance
export const converterRegistry = new ConverterRegistry();