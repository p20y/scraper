#!/bin/bash

# Function to test health check
test_health() {
    echo -e "\nTesting health check"
    echo "=================================================="
    
    response=$(curl -s -w "\n%{http_code}" http://localhost:5001/health)
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" -eq 200 ]; then
        echo "✅ Health check successful"
        echo "Response: $body"
    else
        echo "❌ Health check failed: $status_code"
        echo "Response: $body"
    fi
}

# Function to test search
test_search() {
    local search_term="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local filename="test_results_${timestamp}.md"
    
    echo -e "\nTesting search for: $search_term"
    echo "=================================================="
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "Content-Type: application/json" \
        -d "{\"search_term\":\"$search_term\"}" \
        http://localhost:5001/search)
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$status_code" -eq 200 ]; then
        echo "$body" > "$filename"
        echo "✅ Success! Results saved to $filename"
    else
        echo "❌ Error: $status_code"
        echo "Response: $body"
    fi
}

# Main execution
test_health

# Test different search terms
test_terms=(
    "Lavender oils"
    "Wireless headphones"
    "Laptop stand"
)

for term in "${test_terms[@]}"; do
    test_search "$term"
    echo -e "\n==================================================\n"
done 