"""
Pydantic models for Core Kernel generation.
Defines structured output for Core Kernel Architect to generate foundational contracts.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class CoreFile(BaseModel):
    """A single core kernel file with its implementation."""
    model_config = ConfigDict(extra='forbid')
    
    file_path: str = Field(
        description="File path relative to src/ (e.g., 'core/contracts.ts', 'app/config.ts')"
    )
    purpose: str = Field(
        description="Brief description of what this file provides to the application"
    )
    exports: List[str] = Field(
        description="List of key exports from this file (types, functions, classes, constants)"
    )
    content: str = Field(
        description="Complete TypeScript/JavaScript code for this file"
    )


class CoreKernelResponse(BaseModel):
    """Response containing all core kernel files."""
    model_config = ConfigDict(extra='forbid')
    
    overview: str = Field(
        description="Brief explanation of how the core kernel provides foundation for all sections"
    )
    files: List[CoreFile] = Field(
        min_items=1,
        max_items=8,
        description="Core kernel files that establish shared contracts and utilities"
    )
    usage_guidelines: List[str] = Field(
        min_items=1,
        max_items=10,
        description="Key guidelines for sections using the core kernel (e.g., 'Import types from @/core/contracts', 'Use hooks.register() for extensions')"
    )


# Example for LLM understanding
EXAMPLE_RESPONSE = CoreKernelResponse(
    overview="Core kernel provides shared contracts, dependency injection, event bus, and configuration that all sections import from @/core/*. This ensures consistency and eliminates guesswork about types and patterns.",
    files=[
        CoreFile(
            file_path="core/contracts.ts",
            purpose="Domain types and API contracts used throughout the application",
            exports=["User", "Patient", "Appointment", "ApiResult", "ApiError"],
            content="""export interface User {
  id: string;
  email: string;
  role: 'patient' | 'doctor' | 'nurse';
  name: string;
  avatar?: string;
}

export interface Patient extends User {
  medicalRecordNumber: string;
  dateOfBirth: string;
  insuranceProvider?: string;
}

export interface Appointment {
  id: string;
  patientId: string;
  doctorId: string;
  dateTime: string;
  status: 'scheduled' | 'completed' | 'cancelled';
  reason: string;
  notes?: string;
}

export type ApiResult<T> = 
  | { success: true; data: T }
  | { success: false; error: ApiError };

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}"""
        ),
        CoreFile(
            file_path="core/hooks.ts",
            purpose="Hook registry for extension points throughout the app",
            exports=["HookPoint", "HookContext", "HookRegistry", "hooks"],
            content="""export type HookPoint =
  | 'beforeApiRequest'
  | 'afterApiResponse'
  | 'onLogin'
  | 'onLogout'
  | 'onRouteChange';

export interface HookContext {
  config: any;
  user?: any;
}

export type Hook<TPayload, TResult = void> = 
  (ctx: HookContext, payload: TPayload) => Promise<TResult> | TResult;

export class HookRegistry {
  private handlers: Record<string, Hook<any, any>[]> = {};
  
  register<K extends HookPoint>(point: K, fn: Hook<any, any>) {
    (this.handlers[point] ??= []).push(fn);
  }
  
  async run<K extends HookPoint>(point: K, payload: any) {
    const fns = this.handlers[point] ?? [];
    for (const fn of fns) {
      await fn({} as HookContext, payload);
    }
  }
}

export const hooks = new HookRegistry();"""
        ),
        CoreFile(
            file_path="app/config.ts",
            purpose="Materialized configuration from JSON config file",
            exports=["config", "isDevelopment", "shouldUseMockData"],
            content="""// Configuration materialized from healthcare_portal_config.json
export const config = {
  appType: 'healthcare',
  framework: 'react',
  developmentMode: {
    enableMockData: true,
    disableWebsocketInDev: true,
    useLocalstoragePresistence: true,
    mockAuthUsers: [
      {email: 'patient@email.com', password: 'patient123', role: 'patient'}
    ]
  },
  features: [
    'appointment_scheduling',
    'medical_records_viewer',
    'prescription_management'
  ]
} as const;

export const isDevelopment = process.env.NODE_ENV === 'development';
export const shouldUseMockData = isDevelopment && config.developmentMode.enableMockData;"""
        )
    ],
    usage_guidelines=[
        "Import all domain types from @/core/contracts instead of defining locally",
        "Use hooks.register() to add custom behavior at extension points",
        "Reference config from @/app/config for feature flags and settings",
        "Never import from relative paths when a @/core/* export exists",
        "Use the event bus for decoupled communication between features"
    ]
)


if __name__ == "__main__":
    # Rebuild models to ensure proper schema generation
    CoreFile.model_rebuild()
    CoreKernelResponse.model_rebuild()
    
    # Print example for reference
    print("Example Core Kernel Response:")
    print(EXAMPLE_RESPONSE.model_dump_json(indent=2))