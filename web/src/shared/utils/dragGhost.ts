import { NodeKind } from '@/features/diagram-editor/types/node-kinds';
import { getNodeConfig } from '@/core/config/helpers';

/**
 * Creates a drag ghost image element for a node type
 * This generates an HTML element that looks like the node preview
 * to be used with dataTransfer.setDragImage()
 */
export function createNodeDragGhost(nodeType: NodeKind, label?: string): HTMLElement {
  const config = getNodeConfig(nodeType);
  
  // Create container element
  const ghost = document.createElement('div');
  ghost.className = 'bg-white rounded-lg shadow-lg border-2 border-gray-300 p-3 min-w-[180px] max-w-[280px]';
  ghost.style.cssText = `
    position: absolute;
    top: -1000px;
    left: -1000px;
    background-color: ${config.color || '#ffffff'};
    opacity: 0.8;
    transform: scale(0.9);
  `;
  
  // Create header
  const header = document.createElement('div');
  header.className = 'flex items-center gap-2 mb-2';
  header.innerHTML = `
    <span class="text-lg">${config.icon}</span>
    <span class="font-medium text-sm">
      ${label || config.label}
    </span>
  `;
  
  ghost.appendChild(header);
  
  // Add to document temporarily (needed for setDragImage to work)
  document.body.appendChild(ghost);
  
  // Clean up after a short delay to ensure drag image is captured
  setTimeout(() => {
    if (ghost.parentNode) {
      document.body.removeChild(ghost);
    }
  }, 1); // Increased delay to ensure drag image is properly captured
  
  return ghost;
}

