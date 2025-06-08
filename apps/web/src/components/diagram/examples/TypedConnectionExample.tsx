/**
 * Example component demonstrating the typed connection system
 * This shows how to use the new type-safe connection validation
 */

import React from 'react';
import { useTypedConnectionValidation, useTypedNodes } from '@/utils/connections/typed-facade';
import { NodeType } from '@/types/enums';

export function TypedConnectionExample() {
  const { 
    validateConnection, 
    findValidTargets, 
    canConnect,
    getInvalidConnections 
  } = useTypedConnectionValidation();
  
  const typedNodes = useTypedNodes();

  // Example: Find all valid targets for a person_job output
  const findPersonJobTargets = () => {
    const personJobNodes = Array.from(typedNodes.values())
      .filter(node => node.type === NodeType.PersonJob);
    
    if (personJobNodes.length > 0) {
      const targets = findValidTargets(personJobNodes[0].id, 'output');
      console.log('Valid targets for PersonJob output:', targets);
    }
  };

  // Example: Validate all current connections
  const validateAllConnections = () => {
    const invalidConnections = getInvalidConnections();
    if (invalidConnections.length > 0) {
      console.error('Invalid connections found:', invalidConnections);
    } else {
      console.log('All connections are valid!');
    }
  };

  // Example: Check if two specific handles can connect
  const checkConnection = (sourceHandleId: string, targetHandleId: string) => {
    const canConnectResult = canConnect(sourceHandleId as any, targetHandleId as any);
    console.log(`Can connect ${sourceHandleId} to ${targetHandleId}:`, canConnectResult);
  };

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold">Typed Connection System Examples</h3>
      
      <div className="space-y-2">
        <button 
          onClick={findPersonJobTargets}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Find PersonJob Targets
        </button>
        
        <button 
          onClick={validateAllConnections}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Validate All Connections
        </button>
        
        <button 
          onClick={() => checkConnection('start-node:default', 'person-job:first')}
          className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
        >
          Check Specific Connection
        </button>
      </div>
      
      <div className="mt-4 p-4 bg-gray-100 rounded">
        <h4 className="font-semibold mb-2">Node Summary</h4>
        <p>Total typed nodes: {typedNodes.size}</p>
        <ul className="list-disc list-inside">
          {Array.from(typedNodes.values()).map(node => (
            <li key={node.id}>
              {node.type} - {node.id} 
              (inputs: {Object.keys(node.inputs).length}, 
              outputs: {Object.keys(node.outputs).length})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}