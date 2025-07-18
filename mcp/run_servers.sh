#!/bin/bash
# Script to run MCP servers for local testing

echo "Starting IASO MCP Servers..."
echo "============================"

# Check if RUNPOD_API_KEY is set
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "Error: RUNPOD_API_KEY environment variable not set"
    echo "Please run: export RUNPOD_API_KEY=your_api_key"
    exit 1
fi

# Set default endpoint IDs if not already set
export WHISPER_ENDPOINT_ID=${WHISPER_ENDPOINT_ID:-"rntxttrdl8uv3i"}
export PHI4_ENDPOINT_ID=${PHI4_ENDPOINT_ID:-"tmmwa4q8ax5sg4"}

echo "Configuration:"
echo "- WHISPER_ENDPOINT_ID: $WHISPER_ENDPOINT_ID"
echo "- PHI4_ENDPOINT_ID: $PHI4_ENDPOINT_ID"
echo ""

# Function to run server in background
run_server() {
    local name=$1
    local script=$2
    echo "Starting $name..."
    python $script > logs/${name}.log 2>&1 &
    echo "$name started with PID $!"
}

# Create logs directory
mkdir -p logs

# Start servers
run_server "Whisper MCP Server" "whisper_mcp_server.py"
run_server "Phi-4 MCP Server" "phi4_mcp_server.py"
run_server "IASO Orchestrator" "iaso_orchestrator.py"

echo ""
echo "All servers started. Logs available in ./logs/"
echo "To stop all servers: pkill -f 'mcp_server.py|orchestrator.py'"
echo ""
echo "Test with: python test_integration.py"