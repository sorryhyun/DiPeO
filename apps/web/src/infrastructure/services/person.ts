/**
 * Person domain service - manages AI personas
 * Handles person configuration, validation, and operations
 */

import type {
  DomainPerson,
  PersonID,
  LLMService,
} from '@dipeo/models';
import {
  isValidLLMService,
  llmServiceToAPIServiceType,
} from '@dipeo/models';
import { ValidationService } from './validation';
import { GraphQLService } from '../api/graphql';
import { PersonConverter } from '../converters/person-converter';
import {
  GetPersonDocument,
  ListPersonsDocument,
  CreatePersonDocument,
  UpdatePersonDocument,
  DeletePersonDocument,
} from '@/__generated__/graphql';

/**
 * Default person configurations
 */
const DEFAULT_PERSONS: Record<string, Partial<DomainPerson>> = {
  analyst: {
    label: 'Data Analyst',
    llm_config: {
      service: 'gpt-4.1-nano' as LLMService,
      model: 'gpt-4.1-nano',
      api_key_id: '' as any,
      system_prompt: 'You are a data analyst. Provide clear, data-driven insights.',
    },
  },
  developer: {
    label: 'Software Developer',
    llm_config: {
      service: 'gpt-4.1-nano' as LLMService,
      model: 'gpt-4.1-nano',
      api_key_id: '' as any,
      system_prompt: 'You are an experienced software developer. Write clean, efficient code.',
    },
  },
  creative: {
    label: 'Creative Writer',
    llm_config: {
      service: 'gpt-4.1-nano' as LLMService,
      model: 'gpt-4.1-nano',
      api_key_id: '' as any,
      system_prompt: 'You are a creative writer. Generate engaging and original content.',
    },
  },
};

/**
 * Person management service
 */
export class PersonService {
  private static personsCache = new Map<PersonID, DomainPerson>();
  private static lastFetch: number = 0;
  private static CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Create a new person
   */
  static async createPerson(person: Omit<DomainPerson, 'id'>): Promise<DomainPerson> {
    // Validate person data
    const validation = ValidationService.validatePerson(person as DomainPerson);
    if (!validation.valid) {
      throw new Error(`Invalid person: ${validation.errors.map(e => e.message).join(', ')}`);
    }

    // Convert to GraphQL format and create
    const input = PersonConverter.toGraphQL(person as DomainPerson);
    const result = await GraphQLService.mutate(
      CreatePersonDocument,
      { input },
    );

    const created = PersonConverter.toDomain(result.create_person.person);
    this.personsCache.set(created.id, created);

    return created;
  }

  /**
   * Update an existing person
   */
  static async updatePerson(
    id: PersonID,
    updates: Partial<DomainPerson>,
  ): Promise<DomainPerson> {
    const existing = await this.getPerson(id);
    if (!existing) {
      throw new Error(`Person ${id} not found`);
    }

    const updated = { ...existing, ...updates };

    // Validate updated person
    const validation = ValidationService.validatePerson(updated);
    if (!validation.valid) {
      throw new Error(`Invalid person: ${validation.errors.map(e => e.message).join(', ')}`);
    }

    // Update via GraphQL
    const input = PersonConverter.toGraphQL(updated);
    const result = await GraphQLService.mutate(
      UpdatePersonDocument,
      { id, input },
    );

    const updatedPerson = PersonConverter.toDomain(result.update_person.person);
    this.personsCache.set(id, updatedPerson);

    return updatedPerson;
  }

  /**
   * Delete a person
   */
  static async deletePerson(id: PersonID): Promise<boolean> {
    const result = await GraphQLService.mutate(
      DeletePersonDocument,
      { id },
    );

    this.personsCache.delete(id);
    return result.delete_person.success;
  }

  /**
   * Get a person by ID
   */
  static async getPerson(id: PersonID): Promise<DomainPerson | null> {
    // Check cache first
    if (this.personsCache.has(id)) {
      return this.personsCache.get(id)!;
    }

    // Fetch from backend
    const result = await GraphQLService.query(
      GetPersonDocument,
      { id },
    );

    if (!result.person) {
      return null;
    }

    const person = PersonConverter.toDomain(result.person);
    this.personsCache.set(id, person);

    return person;
  }

  /**
   * Get all persons
   */
  static async getAllPersons(forceRefresh = false): Promise<DomainPerson[]> {
    const now = Date.now();

    // Check if cache is still valid
    if (!forceRefresh && (now - this.lastFetch) < this.CACHE_TTL && this.personsCache.size > 0) {
      return Array.from(this.personsCache.values());
    }

    // Fetch from backend
    const result = await GraphQLService.query(
      ListPersonsDocument,
      { limit: 100 },
    );

    // Update cache
    this.personsCache.clear();
    const persons = result.persons.map((p: any) => {
      const person = PersonConverter.toDomain(p);
      this.personsCache.set(person.id, person);
      return person;
    });

    this.lastFetch = now;
    return persons;
  }

  /**
   * Create a person from a template
   */
  static createFromTemplate(template: keyof typeof DEFAULT_PERSONS): Partial<DomainPerson> {
    const base = DEFAULT_PERSONS[template];
    if (!base) {
      throw new Error(`Unknown person template: ${template}`);
    }

    return {
      ...base,
      label: `${base.label} (${new Date().toISOString().split('T')[0]})`,
    };
  }

  /**
   * Get recommended temperature for a role
   */
  static getRecommendedTemperature(role: string): number {
    const lowerRole = role.toLowerCase();

    if (lowerRole.includes('analy') || lowerRole.includes('data')) {
      return 0.3; // Low temperature for analytical tasks
    }
    if (lowerRole.includes('code') || lowerRole.includes('develop')) {
      return 0.2; // Very low for code generation
    }
    if (lowerRole.includes('creative') || lowerRole.includes('write')) {
      return 0.8; // Higher for creative tasks
    }
    if (lowerRole.includes('chat') || lowerRole.includes('convers')) {
      return 0.7; // Moderate-high for conversational
    }

    return 0.5; // Default moderate temperature
  }

  /**
   * Get recommended model for a use case
   */
  static getRecommendedModel(useCase: 'fast' | 'balanced' | 'powerful'): LLMService {
    switch (useCase) {
      case 'fast':
        return 'gpt-4.1-nano' as LLMService;
      case 'balanced':
        return 'gpt-4' as LLMService;
      case 'powerful':
        return 'gpt-4-turbo' as LLMService;
      default:
        return 'gpt-4.1-nano' as LLMService;
    }
  }

  /**
   * Validate a system prompt
   */
  static validateSystemPrompt(prompt: string): {
    valid: boolean;
    warnings: string[];
  } {
    const warnings: string[] = [];

    if (prompt.length > 5000) {
      warnings.push('System prompt is very long (>5000 chars), may impact performance');
    }

    if (prompt.length < 10) {
      warnings.push('System prompt is very short, consider adding more context');
    }

    if (prompt.includes('{{') && prompt.includes('}}')) {
      warnings.push('System prompt contains template variables that may not be replaced');
    }

    return {
      valid: true,
      warnings,
    };
  }

  /**
   * Generate a system prompt based on role
   */
  static generateSystemPrompt(role: string, style?: 'formal' | 'casual' | 'technical'): string {
    const basePrompt = `You are a ${role}.`;

    let styleAddition = '';
    switch (style) {
      case 'formal':
        styleAddition = ' Maintain a professional and formal tone in all responses.';
        break;
      case 'casual':
        styleAddition = ' Use a friendly and conversational tone.';
        break;
      case 'technical':
        styleAddition = ' Provide detailed technical explanations when appropriate.';
        break;
    }

    let roleSpecific = '';
    const lowerRole = role.toLowerCase();

    if (lowerRole.includes('analy')) {
      roleSpecific = ' Focus on data-driven insights and objective analysis.';
    } else if (lowerRole.includes('develop')) {
      roleSpecific = ' Write clean, well-documented code following best practices.';
    } else if (lowerRole.includes('write')) {
      roleSpecific = ' Create engaging and well-structured content.';
    } else if (lowerRole.includes('teach')) {
      roleSpecific = ' Explain concepts clearly and provide helpful examples.';
    }

    return basePrompt + styleAddition + roleSpecific;
  }

  /**
   * Clone a person with a new name
   */
  static clonePerson(person: DomainPerson, newName: string): Omit<DomainPerson, 'id'> {
    return {
      ...person,
      label: newName,
      // Remove ID so a new one will be generated
    };
  }

  /**
   * Export persons to JSON
   */
  static async exportPersons(): Promise<string> {
    const persons = await this.getAllPersons();
    return JSON.stringify(persons, null, 2);
  }

  /**
   * Import persons from JSON
   */
  static async importPersons(json: string): Promise<DomainPerson[]> {
    const parsed = JSON.parse(json);
    if (!Array.isArray(parsed)) {
      throw new Error('Invalid persons JSON: must be an array');
    }

    const imported: DomainPerson[] = [];

    for (const personData of parsed) {
      // Remove ID to create new persons
      const { id, ...data } = personData;
      try {
        const person = await this.createPerson(data);
        imported.push(person);
      } catch (error) {
        console.error(`Failed to import person: ${error}`);
      }
    }

    return imported;
  }
}
