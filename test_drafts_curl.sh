#!/bin/bash
# Bash script to test draft functionality using curl
# Make sure your email engine is running on http://localhost:8000

BASE_URL="http://localhost:8000"
AUTH_TOKEN=""  # Set your auth token here if needed

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Function to make authenticated requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local content_type=${4:-"application/json"}
    
    local auth_header=""
    if [ ! -z "$AUTH_TOKEN" ]; then
        auth_header="-H \"Authorization: Bearer $AUTH_TOKEN\""
    fi
    
    if [ ! -z "$data" ]; then
        eval curl -s -X "$method" \
            -H "\"Content-Type: $content_type\"" \
            $auth_header \
            -d "\"$data\"" \
            "$BASE_URL$endpoint"
    else
        eval curl -s -X "$method" \
            -H "\"Content-Type: $content_type\"" \
            $auth_header \
            "$BASE_URL$endpoint"
    fi
}

# Test functions
test_create_draft() {
    echo -e "\n${YELLOW}=== Creating Test Draft ===${NC}"
    
    local draft_data='{
        "subject": "Test Draft - Bash Debug",
        "body": "This is a test draft created via Bash for debugging.",
        "to": ["test@example.com"],
        "cc": [],
        "bcc": [],
        "attachments": []
    }'
    
    echo -e "${CYAN}Draft data:${NC}"
    echo "$draft_data" | jq . 2>/dev/null || echo "$draft_data"
    
    local result=$(make_request "POST" "/emails/compose" "$draft_data")
    local draft_id=$(echo "$result" | jq -r '.id' 2>/dev/null)
    
    if [ "$draft_id" != "null" ] && [ "$draft_id" != "" ]; then
        echo -e "${GREEN}✅ Draft created successfully with ID: $draft_id${NC}"
        echo "$draft_id"
    else
        echo -e "${RED}❌ Failed to create draft${NC}"
        echo "$result"
        echo ""
    fi
}

test_create_draft_with_attachment() {
    echo -e "\n${YELLOW}=== Creating Test Draft with Attachment ===${NC}"
    
    # Create a simple text attachment (base64 encoded)
    local text_content="This is a test attachment for debugging."
    local text_base64=$(echo -n "$text_content" | base64)
    
    local draft_data="{
        \"subject\": \"Test Draft with Attachment - Bash Debug\",
        \"body\": \"This draft has a test attachment.\",
        \"to\": [\"test@example.com\"],
        \"cc\": [],
        \"bcc\": [],
        \"attachments\": [
            {
                \"filename\": \"test_attachment.txt\",
                \"content_base64\": \"$text_base64\",
                \"content_type\": \"text/plain\"
            }
        ]
    }"
    
    echo "Creating draft with attachment..."
    
    local result=$(make_request "POST" "/emails/compose" "$draft_data")
    local draft_id=$(echo "$result" | jq -r '.id' 2>/dev/null)
    
    if [ "$draft_id" != "null" ] && [ "$draft_id" != "" ]; then
        echo -e "${GREEN}✅ Draft with attachment created successfully with ID: $draft_id${NC}"
        echo "$draft_id"
    else
        echo -e "${RED}❌ Failed to create draft with attachment${NC}"
        echo "$result"
        echo ""
    fi
}

test_get_drafts() {
    echo -e "\n${YELLOW}=== Getting Drafts ===${NC}"
    
    local result=$(make_request "GET" "/emails/drafts")
    local total=$(echo "$result" | jq -r '.total' 2>/dev/null)
    
    if [ "$total" != "null" ] && [ "$total" != "" ]; then
        echo -e "${GREEN}✅ Retrieved drafts: $total total${NC}"
        echo "$result" | jq . 2>/dev/null || echo "$result"
    else
        echo -e "${RED}❌ Failed to get drafts${NC}"
        echo "$result"
    fi
}

test_debug_all_emails() {
    echo -e "\n${YELLOW}=== Getting Debug Information ===${NC}"
    
    local result=$(make_request "GET" "/emails/debug/all-emails")
    local total=$(echo "$result" | jq -r '.total_emails' 2>/dev/null)
    
    if [ "$total" != "null" ] && [ "$total" != "" ]; then
        local folders=$(echo "$result" | jq -r '.folders | join(", ")' 2>/dev/null)
        local drafts_count=$(echo "$result" | jq -r '.drafts_count' 2>/dev/null)
        echo -e "${GREEN}✅ Debug info - Total emails: $total${NC}"
        echo "   Folders: $folders"
        echo "   Drafts count: $drafts_count"
        echo "$result" | jq . 2>/dev/null || echo "$result"
    else
        echo -e "${RED}❌ Failed to get debug info${NC}"
        echo "$result"
    fi
}

test_debug_drafts_detailed() {
    echo -e "\n${YELLOW}=== Getting Detailed Draft Information ===${NC}"
    
    local result=$(make_request "GET" "/emails/debug/drafts-detailed")
    local total=$(echo "$result" | jq -r '.total_drafts' 2>/dev/null)
    
    if [ "$total" != "null" ] && [ "$total" != "" ]; then
        echo -e "${GREEN}✅ Detailed draft info - Total drafts: $total${NC}"
        echo "$result" | jq . 2>/dev/null || echo "$result"
    else
        echo -e "${RED}❌ Failed to get detailed draft info${NC}"
        echo "$result"
    fi
}

test_get_draft_detail() {
    local draft_id=$1
    echo -e "\n${YELLOW}=== Getting Draft $draft_id Details ===${NC}"
    
    local result=$(make_request "GET" "/emails/$draft_id?folder=drafts")
    local id=$(echo "$result" | jq -r '.id' 2>/dev/null)
    
    if [ "$id" != "null" ] && [ "$id" != "" ]; then
        echo -e "${GREEN}✅ Retrieved draft $draft_id details${NC}"
        echo "$result" | jq . 2>/dev/null || echo "$result"
    else
        echo -e "${RED}❌ Failed to get draft $draft_id details${NC}"
        echo "$result"
    fi
}

run_full_test() {
    echo -e "${MAGENTA}$(printf '=%.0s' {1..60})${NC}"
    echo -e "${MAGENTA}EMAIL ENGINE DRAFT DEBUG TEST (Bash)${NC}"
    echo -e "${MAGENTA}$(printf '=%.0s' {1..60})${NC}"
    
    # Step 1: Check current state
    echo -e "\n${CYAN}1. Checking current drafts...${NC}"
    test_get_drafts > /dev/null
    
    # Step 2: Get debug information
    echo -e "\n${CYAN}2. Getting debug information...${NC}"
    test_debug_all_emails > /dev/null
    
    # Step 3: Create test draft
    echo -e "\n${CYAN}3. Creating test draft...${NC}"
    local new_draft_id=$(test_create_draft)
    
    # Step 4: Create draft with attachment
    echo -e "\n${CYAN}4. Creating test draft with attachment...${NC}"
    local new_draft_with_attachment_id=$(test_create_draft_with_attachment)
    
    # Step 5: Check drafts again
    echo -e "\n${CYAN}5. Checking drafts after creation...${NC}"
    test_get_drafts > /dev/null
    
    # Step 6: Get detailed draft information
    echo -e "\n${CYAN}6. Getting detailed draft information...${NC}"
    test_debug_drafts_detailed > /dev/null
    
    # Step 7: Test specific draft retrieval
    if [ ! -z "$new_draft_id" ] && [ "$new_draft_id" != "" ]; then
        echo -e "\n${CYAN}7. Getting details for draft $new_draft_id...${NC}"
        test_get_draft_detail "$new_draft_id" > /dev/null
    fi
    
    echo -e "\n${MAGENTA}$(printf '=%.0s' {1..60})${NC}"
    echo -e "${MAGENTA}TEST COMPLETE${NC}"
    echo -e "${MAGENTA}$(printf '=%.0s' {1..60})${NC}"
}

show_menu() {
    echo -e "\n${GREEN}Email Engine Draft Debugger (Bash)${NC}"
    echo -e "${GREEN}$(printf '=%.0s' {1..40})${NC}"
    echo "Make sure your email engine is running on http://localhost:8000"
    echo "You may need to set an authentication token if your API requires it."
    
    echo -e "\n${YELLOW}Choose an option:${NC}"
    echo "1. Run full test"
    echo "2. Create simple test draft"
    echo "3. Create test draft with attachment"
    echo "4. Get current drafts"
    echo "5. Get debug information"
    echo "6. Get detailed draft information"
    echo "7. Exit"
}

# Main execution
if [ -z "$AUTH_TOKEN" ]; then
    read -p "Enter your auth token (press Enter if not needed): " input_token
    if [ ! -z "$input_token" ]; then
        AUTH_TOKEN="$input_token"
    fi
fi

while true; do
    show_menu
    read -p $'\nEnter your choice (1-7): ' choice
    
    case $choice in
        1) run_full_test ;;
        2) test_create_draft > /dev/null ;;
        3) test_create_draft_with_attachment > /dev/null ;;
        4) test_get_drafts ;;
        5) test_debug_all_emails ;;
        6) test_debug_drafts_detailed ;;
        7) echo -e "${GREEN}Exiting...${NC}"; break ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
done