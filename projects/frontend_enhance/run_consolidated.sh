#!/bin/bash

# Run the consolidated frontend generator with intelligent memory selection
echo "Starting Consolidated Frontend Generator with memorize_to feature..."
echo "This will process sections sequentially with intelligent context building."
echo ""

# Run the consolidated generator
dipeo run projects/frontend_enhance/consolidated_generator --light --debug --timeout=120

echo ""
echo "Generation complete! Check the results at:"
echo "  - projects/frontend_enhance/generated/consolidated_results.json"
echo "  - projects/frontend_enhance/generated/consolidated_section_*.json"
echo ""
echo "Monitor the progress at: http://localhost:3000/?monitor=true"