#!/usr/bin/env node
/**
 * Node.js Execution Runner - Uses frontend execution engine with backend API calls
 * 
 * This provides the same execution logic as the web frontend but runs in Node.js
 * for CLI usage. Server-only operations are delegated to the backend API.
 */

const fs = require('fs');
const path = require('path');

const fetch = require('node-fetch');

class ExecutionRunner {
    constructor(apiUrl = 'http://localhost:8000') {
        this.apiUrl = apiUrl;
        this.executionContext = {
            nodeOutputs: {},
            errors: {},
            totalCost: 0,
            executionOrder: []
        };
    }

    async executeDiagram(diagram) {
        console.log('🚀 Starting diagram execution...');
        
        try {
            // Store diagram reference for input resolution
            this.diagram = diagram;
            
            // Validate diagram
            this.validateDiagram(diagram);
            
            // Get execution order (proper dependency resolution)
            const executionOrder = this.getExecutionOrder(diagram);
            console.log(`📋 Execution order: ${executionOrder.join(' → ')}`);
            
            // Execute nodes in order
            for (const nodeId of executionOrder) {
                const node = diagram.nodes.find(n => n.id === nodeId);
                if (!node) continue;
                
                console.log(`  ▶️  Executing node: ${nodeId} (${node.type})`);
                
                try {
                    const result = await this.executeNode(node, diagram);
                    this.executionContext.nodeOutputs[nodeId] = result.output;
                    this.executionContext.totalCost += result.cost || 0;
                    this.executionContext.executionOrder.push(nodeId);
                    
                    console.log(`  ✅ Completed node: ${nodeId}`);
                    if (result.output && typeof result.output === 'string') {
                        const preview = result.output.substring(0, 50);
                        console.log(`     Output: ${preview}${result.output.length > 50 ? '...' : ''}`);
                    }
                } catch (error) {
                    const errorMessage = error.message || error.toString() || JSON.stringify(error);
                    console.log(`  ❌ Failed node: ${nodeId} - ${errorMessage}`);
                    this.executionContext.errors[nodeId] = errorMessage;
                    // Continue execution for other nodes
                }
            }
            
            console.log(`\n✓ Execution complete`);
            console.log(`  Total cost: $${this.executionContext.totalCost.toFixed(4)}`);
            console.log(`  Nodes executed: ${this.executionContext.executionOrder.length}`);
            console.log(`  Errors: ${Object.keys(this.executionContext.errors).length}`);
            
            return {
                success: true,
                context: this.executionContext,
                total_cost: this.executionContext.totalCost,
                messages: [] // For compatibility with existing tool.py
            };
            
        } catch (error) {
            console.log(`\n❌ Execution failed: ${error.message}`);
            return {
                success: false,
                error: error.message,
                context: this.executionContext,
                total_cost: this.executionContext.totalCost,
                messages: []
            };
        }
    }

    async executeNode(node, diagram) {
        const nodeType = node.type;
        
        switch (nodeType) {
            case 'startNode':
                return this.executeStartNode(node, diagram);
            
            case 'personJobNode':
                return this.executePersonJobNode(node, diagram);
            
            case 'dbNode':
                return this.executeDbNode(node, diagram);
            
            case 'endpointNode':
                return this.executeEndpointNode(node, diagram);
            
            case 'conditionNode':
                return this.executeConditionNode(node, diagram);
            
            case 'jobNode':
                return this.executeJobNode(node, diagram);
            
            default:
                throw new Error(`Unsupported node type: ${nodeType}`);
        }
    }

    executeStartNode(node, diagram) {
        return { output: 'started', cost: 0 };
    }

    async executePersonJobNode(node, diagram) {
        const nodeData = node.data || {};
        const personId = nodeData.personId;
        
        if (!personId) {
            throw new Error('PersonJob node missing personId');
        }
        
        // Get person configuration
        const person = this.getPersonById(diagram, personId);
        if (!person) {
            throw new Error(`Person ${personId} not found`);
        }
        
        // Get prompts and determine which to use
        const defaultPrompt = nodeData.defaultPrompt || '';
        const firstOnlyPrompt = nodeData.firstOnlyPrompt || '';
        
        // For now, use default prompt (could add first-only logic later)
        const prompt = firstOnlyPrompt || defaultPrompt;
        
        if (!prompt) {
            throw new Error('No prompt available for PersonJob node');
        }
        
        // Get inputs and substitute variables
        const inputs = this.getNodeInputs(node.id);
        const finalPrompt = this.substituteVariables(prompt, inputs);
        
        // Call backend API
        const response = await fetch(`${this.apiUrl}/api/nodes/personjob/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                person: person,
                prompt: finalPrompt,
                inputs: inputs,
                node_config: nodeData
            })
        });
        
        if (!response.ok) {
            let errorText;
            try {
                const errorJson = await response.json();
                errorText = errorJson.error || errorJson.detail || JSON.stringify(errorJson);
            } catch (e) {
                errorText = await response.text().catch(() => 'Unknown error');
            }
            throw new Error(`API call failed (${response.status}): ${errorText}`);
        }
        
        const result = await response.json();
        return {
            output: result.output || "",
            cost: result.cost || 0,
            metadata: result.metadata
        };
    }

    async executeDbNode(node, diagram) {
        const nodeData = node.data || {};
        const subType = nodeData.subType || 'file';
        const sourceDetails = nodeData.sourceDetails || '';
        
        // Call backend API
        const response = await fetch(`${this.apiUrl}/api/nodes/db/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sub_type: subType,
                source_details: sourceDetails
            })
        });
        
        if (!response.ok) {
            let errorText;
            try {
                const errorJson = await response.json();
                errorText = errorJson.error || errorJson.detail || JSON.stringify(errorJson);
            } catch (e) {
                errorText = await response.text().catch(() => 'Unknown error');
            }
            throw new Error(`API call failed (${response.status}): ${errorText}`);
        }
        
        const result = await response.json();
        return {
            output: result.output,
            cost: 0,
            metadata: result.metadata
        };
    }

    async executeEndpointNode(node, diagram) {
        const nodeData = node.data || {};
        const inputs = this.getNodeInputs(node.id);
        const inputValues = Object.values(inputs);
        // For now, take the last input which should be from the previous node in the flow
        const content = inputValues[inputValues.length - 1] || '';
        
        // Call backend API
        const response = await fetch(`${this.apiUrl}/api/nodes/endpoint/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                save_to_file: nodeData.saveToFile || false,
                file_path: nodeData.filePath || '',
                file_format: nodeData.fileFormat || 'text'
            })
        });
        
        if (!response.ok) {
            let errorText;
            try {
                const errorJson = await response.json();
                errorText = errorJson.error || errorJson.detail || JSON.stringify(errorJson);
            } catch (e) {
                errorText = await response.text().catch(() => 'Unknown error');
            }
            throw new Error(`API call failed (${response.status}): ${errorText}`);
        }
        
        const result = await response.json();
        return {
            output: result.output,
            cost: 0,
            metadata: result.metadata
        };
    }

    executeConditionNode(node, diagram) {
        const nodeData = node.data || {};
        const conditionType = nodeData.conditionType || 'expression';
        
        if (conditionType === 'max_iterations') {
            const maxIterations = nodeData.maxIterations || 1;
            // Simplified: always return true for now
            return { output: true, cost: 0 };
        }
        
        // For other condition types, default to true
        return { output: true, cost: 0 };
    }

    async executeJobNode(node, diagram) {
        const nodeData = node.data || {};
        const subType = nodeData.subType || 'code';
        
        if (subType === 'code') {
            const code = nodeData.code || '';
            const inputs = this.getNodeInputs(node.id);
            
            // Call backend API for safe code execution
            const response = await fetch(`${this.apiUrl}/api/nodes/code/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    inputs: Object.values(inputs)
                })
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(error.error || `API call failed: ${response.status}`);
            }
            
            const result = await response.json();
            return {
                output: result.output,
                cost: 0,
                metadata: result.metadata
            };
        }
        
        // For other job types, return empty output
        return { output: '', cost: 0 };
    }

    validateDiagram(diagram) {
        if (!diagram.nodes || !Array.isArray(diagram.nodes)) {
            throw new Error('Diagram must have nodes array');
        }
        
        // Check for start nodes
        const startNodes = diagram.nodes.filter(n => n.type === 'startNode');
        if (startNodes.length === 0) {
            throw new Error('Diagram must have at least one start node');
        }
    }

    getExecutionOrder(diagram) {
        // Build dependency graph from arrows
        const arrows = diagram.arrows || [];
        const nodes = diagram.nodes || [];
        
        // Create adjacency list for dependencies
        const dependencies = {}; // nodeId -> [prerequisite nodeIds]
        const dependents = {};   // nodeId -> [dependent nodeIds]
        
        // Initialize all nodes
        nodes.forEach(node => {
            dependencies[node.id] = [];
            dependents[node.id] = [];
        });
        
        // Build dependency graph
        arrows.forEach(arrow => {
            dependencies[arrow.target].push(arrow.source);
            dependents[arrow.source].push(arrow.target);
        });
        
        // Topological sort using Kahn's algorithm
        const executionOrder = [];
        const queue = [];
        const inDegree = {};
        
        // Calculate in-degrees
        nodes.forEach(node => {
            inDegree[node.id] = dependencies[node.id].length;
            if (inDegree[node.id] === 0) {
                queue.push(node.id);
            }
        });
        
        // Process nodes in dependency order
        while (queue.length > 0) {
            const nodeId = queue.shift();
            executionOrder.push(nodeId);
            
            // Update dependent nodes
            dependents[nodeId].forEach(dependentId => {
                inDegree[dependentId]--;
                if (inDegree[dependentId] === 0) {
                    queue.push(dependentId);
                }
            });
        }
        
        // Check for cycles
        if (executionOrder.length !== nodes.length) {
            throw new Error('Diagram contains cycles - cannot determine execution order');
        }
        
        return executionOrder;
    }

    getPersonById(diagram, personId) {
        const persons = diagram.persons || [];
        
        if (Array.isArray(persons)) {
            return persons.find(p => p.id === personId);
        } else if (typeof persons === 'object') {
            return persons[personId];
        }
        
        return null;
    }

    getNodeInputs(nodeId) {
        // Get inputs from connected source nodes via arrows
        const arrows = this.diagram.arrows || [];
        const inputs = {};
        
        // Find all arrows pointing to this node
        const incomingArrows = arrows.filter(arrow => arrow.target === nodeId);
        
        incomingArrows.forEach((arrow, index) => {
            const sourceNodeId = arrow.source;
            const sourceOutput = this.executionContext.nodeOutputs[sourceNodeId];
            
            if (sourceOutput !== undefined) {
                // Primary key: use arrow ID or label if available
                const arrowKey = arrow.label || arrow.id || `arrow_${index}`;
                inputs[arrowKey] = sourceOutput;
                
                // Secondary keys for flexibility
                const sourceNode = this.diagram.nodes.find(n => n.id === sourceNodeId);
                if (sourceNode) {
                    const nodeKey = `${sourceNode.type.replace('Node', '')}_${sourceNode.id.split('-')[1] || index}`;
                    inputs[nodeKey] = sourceOutput;
                }
                
                // Backward compatibility
                inputs[`input_${index}`] = sourceOutput;
                inputs[sourceNodeId] = sourceOutput;
            }
        });
        
        return inputs;
    }

    substituteVariables(template, variables) {
        let result = template;
        
        // Log variable substitution for debugging
        console.log(`    🔄 Substituting variables in template:`);
        console.log(`       Template: ${template}`);
        console.log(`       Variables:`, variables);
        
        for (const [key, value] of Object.entries(variables)) {
            const doublePattern = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
            const singlePattern = new RegExp(`\\{${key}\\}`, 'g');
            
            result = result.replace(doublePattern, String(value));
            result = result.replace(singlePattern, String(value));
        }
        
        console.log(`       Result: ${result}`);
        return result;
    }
}

// CLI interface
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length < 1) {
        console.log('Usage: node execution_runner.js <diagram.json>');
        process.exit(1);
    }
    
    const diagramPath = args[0];
    
    try {
        const diagramData = JSON.parse(fs.readFileSync(diagramPath, 'utf8'));
        const runner = new ExecutionRunner();
        
        runner.executeDiagram(diagramData).then(result => {
            console.log('\n📊 Execution Summary:');
            console.log(`  Success: ${result.success}`);
            if (result.error) {
                console.log(`  Error: ${result.error}`);
            }
            
            // Save results
            const resultsPath = 'results.json';
            fs.writeFileSync(resultsPath, JSON.stringify(result, null, 2));
            console.log(`  Results saved to: ${resultsPath}`);
            
            process.exit(result.success ? 0 : 1);
        }).catch(error => {
            console.error('Execution error:', error);
            process.exit(1);
        });
        
    } catch (error) {
        console.error('Failed to load diagram:', error.message);
        process.exit(1);
    }
}

module.exports = ExecutionRunner;