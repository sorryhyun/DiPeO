/**
 * Person Converter Module
 *
 * Handles all conversions related to AI personas.
 * Manages transformations between GraphQL and Domain representations.
 */

import {
  type PersonID,
  type DomainPerson,
  type PersonLLMConfig,
  type LLMService,
  convertGraphQLPersonToDomain
} from '@dipeo/models';
import type { DomainPersonType } from '@/__generated__/graphql';
import { personId, apiKeyId } from '@/infrastructure/types/branded';

export class PersonConverter {
  /**
   * Convert GraphQL person to domain person
   * Uses the utility from @dipeo/models
   */
  static toDomain(graphqlPerson: DomainPersonType | any): DomainPerson {
    return convertGraphQLPersonToDomain(graphqlPerson);
  }

  /**
   * Convert domain person to GraphQL input
   */
  static toGraphQL(domainPerson: DomainPerson): Partial<DomainPersonType> {
    return {
      id: domainPerson.id,
      label: domainPerson.label,
      llm_config: {
        service: domainPerson.llm_config.service,
        model: domainPerson.llm_config.model,
        api_key_id: domainPerson.llm_config.api_key_id,
        system_prompt: domainPerson.llm_config.system_prompt
      }
    };
  }

  /**
   * Batch convert GraphQL persons to domain
   */
  static batchToDomain(graphqlPersons: DomainPersonType[]): DomainPerson[] {
    return graphqlPersons.map(person => this.toDomain(person));
  }

  /**
   * Batch convert domain persons to GraphQL
   */
  static batchToGraphQL(domainPersons: DomainPerson[]): Partial<DomainPersonType>[] {
    return domainPersons.map(person => this.toGraphQL(person));
  }

  /**
   * Convert array to Map for efficient lookups
   */
  static arrayToMap(persons: DomainPerson[]): Map<PersonID, DomainPerson> {
    return new Map(persons.map(person => [person.id, person]));
  }

  /**
   * Filter persons by LLM service
   */
  static filterByService(persons: DomainPerson[], service: LLMService): DomainPerson[] {
    return persons.filter(person => person.llm_config.service === service);
  }

  /**
   * Group persons by LLM service
   */
  static groupByService(persons: DomainPerson[]): Map<LLMService, DomainPerson[]> {
    const groups = new Map<LLMService, DomainPerson[]>();
    persons.forEach(person => {
      const service = person.llm_config.service;
      const group = groups.get(service) || [];
      group.push(person);
      groups.set(service, group);
    });
    return groups;
  }

  /**
   * Create a minimal person
   */
  static createPerson(
    label: string,
    service: LLMService,
    model: string
  ): DomainPerson {
    return {
      id: personId(`person_${Date.now()}`),
      label,
      llm_config: {
        service,
        model,
        api_key_id: apiKeyId(''),
        system_prompt: null
      },
      type: 'person'
    };
  }

  /**
   * Update LLM config for a person
   */
  static updateLLMConfig(
    person: DomainPerson,
    updates: Partial<PersonLLMConfig>
  ): DomainPerson {
    return {
      ...person,
      llm_config: {
        ...person.llm_config,
        ...updates
      }
    };
  }

  /**
   * Check if person has valid API key
   */
  static hasApiKey(person: DomainPerson): boolean {
    return person.llm_config.api_key_id !== '' &&
           person.llm_config.api_key_id !== apiKeyId('');
  }
}
