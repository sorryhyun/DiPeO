// Test script to check computed array functionality
import { useUnifiedStore } from './apps/web/src/core/store/unifiedStore.js';

// Get the store state
const state = useUnifiedStore.getState();

console.log('Testing computed arrays:');
console.log('======================');

// Check if Maps exist
console.log('nodes Map exists:', state.nodes instanceof Map);
console.log('arrows Map exists:', state.arrows instanceof Map);
console.log('persons Map exists:', state.persons instanceof Map);

// Check Maps sizes
console.log('\nMap sizes:');
console.log('nodes.size:', state.nodes.size);
console.log('arrows.size:', state.arrows.size);
console.log('persons.size:', state.persons.size);

// Try to access computed arrays
console.log('\nComputed arrays:');
console.log('nodesArray:', state.nodesArray);
console.log('arrowsArray:', state.arrowsArray);
console.log('personsArray:', state.personsArray);

// Check if arrays are defined
console.log('\nArray checks:');
console.log('nodesArray is Array:', Array.isArray(state.nodesArray));
console.log('arrowsArray is Array:', Array.isArray(state.arrowsArray));
console.log('personsArray is Array:', Array.isArray(state.personsArray));

// Add a test node and check arrays again
state.addNode('start', { x: 0, y: 0 });
console.log('\nAfter adding a node:');
console.log('nodes.size:', state.nodes.size);
console.log('nodesArray.length:', state.nodesArray?.length);