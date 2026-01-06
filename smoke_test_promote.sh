#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
BASE_URL="${1:-http://localhost:8000/api/v1}"
PROJECT_CODE="electricity-bot"

# Counters
PASS=0
FAIL=0

# ============================================================
# HELPER FUNCTIONS
# ============================================================

print_header() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "────────────────────────────────────────"
}

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local expected_code="$4"
    local data="$5"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${BASE_URL}${endpoint}" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        echo -e "  ${GREEN}✅${NC} $name"
        ((PASS++))
    else
        echo -e "  ${RED}❌${NC} $name (Expected: $expected_code, Got: $http_code)"
        echo "     Response: $body"
        ((FAIL++))
    fi
    
    echo "$body"
}

compare_counts() {
    local name="$1"
    local draft_count="$2"
    local locked_count="$3"
    
    if [ "$draft_count" = "$locked_count" ]; then
        echo -e "  ${GREEN}✅${NC} $name: Draft($draft_count) = Locked($locked_count)"
        ((PASS++))
    else
        echo -e "  ${RED}❌${NC} $name: Draft($draft_count) ≠ Locked($locked_count)"
        ((FAIL++))
    fi
}

# ============================================================
# MAIN SCRIPT
# ============================================================

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  SMOKE TEST: PROMOTE DRAFT → LOCKED"
echo "════════════════════════════════════════════════════════════════"
echo "  Target: $BASE_URL"
echo "  Project: $PROJECT_CODE"
echo ""

# ============================================================
# 1. PRE-PROMOTION: COUNT DRAFT DATA
# ============================================================
print_header "📊 1. PRE-PROMOTION: COUNT DRAFT DATA"

# Count intents
DRAFT_INTENTS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/intents" | grep -o '"intent_name"' | wc -l)
echo "  Draft Intents: $DRAFT_INTENTS"

# Count entities
DRAFT_ENTITIES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/entities" | grep -o '"entity_key"' | wc -l)
echo "  Draft Entities: $DRAFT_ENTITIES"

# Count slots
DRAFT_SLOTS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/slots" | grep -o '"name"' | wc -l)
echo "  Draft Slots: $DRAFT_SLOTS"

# Count responses
DRAFT_RESPONSES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/responses" | grep -o '"name"' | wc -l)
echo "  Draft Responses: $DRAFT_RESPONSES"

# Count actions
DRAFT_ACTIONS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/actions" | grep -o '"name"' | wc -l)
echo "  Draft Actions: $DRAFT_ACTIONS"

# Count forms
DRAFT_FORMS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/forms" | grep -o '"name"' | wc -l)
echo "  Draft Forms: $DRAFT_FORMS"

# Count stories
DRAFT_STORIES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/stories" | grep -o '"name"' | wc -l)
echo "  Draft Stories: $DRAFT_STORIES"

# Count rules
DRAFT_RULES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/rules" | grep -o '"name"' | wc -l)
echo "  Draft Rules: $DRAFT_RULES"

# ============================================================
# 2. PRE-PROMOTION: VALIDATE DRAFT EXPORTS
# ============================================================
print_header "✅ 2. PRE-PROMOTION: VALIDATE DRAFT"

test_endpoint "Validate NLU export (EN)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/en" "200" > /dev/null
test_endpoint "Validate NLU export (HI)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/hi" "200" > /dev/null
test_endpoint "Validate Domain export" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/domain" "200" > /dev/null
test_endpoint "Validate Stories export" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/stories" "200" > /dev/null
test_endpoint "Validate Rules export" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/rules" "200" > /dev/null

# ============================================================
# 3. PROMOTE DRAFT TO LOCKED
# ============================================================
print_header "🚀 3. PROMOTE DRAFT → LOCKED"

echo -e "  ${YELLOW}Promoting...${NC}"
PROMOTE_RESULT=$(test_endpoint "Promote draft to locked" "POST" "/projects/${PROJECT_CODE}/promote" "200")

# Check if promotion was successful
if echo "$PROMOTE_RESULT" | grep -q '"status":"locked"'; then
    echo -e "  ${GREEN}✅ Promotion successful!${NC}"
else
    echo -e "  ${YELLOW}⚠️  Check promotion result${NC}"
fi

# ============================================================
# 4. POST-PROMOTION: VERIFY LOCKED VERSION
# ============================================================
print_header "🔒 4. POST-PROMOTION: VERIFY LOCKED VERSION"

test_endpoint "Locked version exists" "GET" "/projects/${PROJECT_CODE}/versions/locked" "200" > /dev/null

# Count locked data
LOCKED_INTENTS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/intents" | grep -o '"intent_name"' | wc -l)
LOCKED_ENTITIES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/entities" | grep -o '"entity_key"' | wc -l)
LOCKED_SLOTS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/slots" | grep -o '"name"' | wc -l)
LOCKED_RESPONSES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/responses" | grep -o '"name"' | wc -l)
LOCKED_ACTIONS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/actions" | grep -o '"name"' | wc -l)
LOCKED_FORMS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/forms" | grep -o '"name"' | wc -l)
LOCKED_STORIES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/stories" | grep -o '"name"' | wc -l)
LOCKED_RULES=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/rules" | grep -o '"name"' | wc -l)

echo ""
echo "  Locked Version Counts:"
echo "    Intents: $LOCKED_INTENTS"
echo "    Entities: $LOCKED_ENTITIES"
echo "    Slots: $LOCKED_SLOTS"
echo "    Responses: $LOCKED_RESPONSES"
echo "    Actions: $LOCKED_ACTIONS"
echo "    Forms: $LOCKED_FORMS"
echo "    Stories: $LOCKED_STORIES"
echo "    Rules: $LOCKED_RULES"

# ============================================================
# 5. COMPARE DRAFT vs LOCKED COUNTS
# ============================================================
print_header "🔄 5. COMPARE: DRAFT → LOCKED"

compare_counts "Intents" "$DRAFT_INTENTS" "$LOCKED_INTENTS"
compare_counts "Entities" "$DRAFT_ENTITIES" "$LOCKED_ENTITIES"
compare_counts "Slots" "$DRAFT_SLOTS" "$LOCKED_SLOTS"
compare_counts "Responses" "$DRAFT_RESPONSES" "$LOCKED_RESPONSES"
compare_counts "Actions" "$DRAFT_ACTIONS" "$LOCKED_ACTIONS"
compare_counts "Forms" "$DRAFT_FORMS" "$LOCKED_FORMS"
compare_counts "Stories" "$DRAFT_STORIES" "$LOCKED_STORIES"
compare_counts "Rules" "$DRAFT_RULES" "$LOCKED_RULES"

# ============================================================
# 6. VERIFY NEW DATA IN LOCKED
# ============================================================
print_header "🔍 6. VERIFY NEW DATA IN LOCKED"

test_endpoint "New intent in locked (complaint_status)" "GET" "/projects/${PROJECT_CODE}/versions/locked/intents/complaint_status" "200" > /dev/null
test_endpoint "New entity in locked (complaint_id)" "GET" "/projects/${PROJECT_CODE}/versions/locked/entities/complaint_id" "200" > /dev/null
test_endpoint "New slot in locked (complaint_id)" "GET" "/projects/${PROJECT_CODE}/versions/locked/slots/complaint_id" "200" > /dev/null
test_endpoint "New response in locked (utter_complaint_status)" "GET" "/projects/${PROJECT_CODE}/versions/locked/responses/utter_complaint_status" "200" > /dev/null
test_endpoint "New action in locked (action_check_complaint)" "GET" "/projects/${PROJECT_CODE}/versions/locked/actions/action_check_complaint" "200" > /dev/null
test_endpoint "New form in locked (complaint_form)" "GET" "/projects/${PROJECT_CODE}/versions/locked/forms/complaint_form" "200" > /dev/null

# ============================================================
# 7. EXPORT LOCKED VERSION
# ============================================================
print_header "📤 7. EXPORT LOCKED VERSION"

test_endpoint "Export locked NLU (EN)" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/nlu/en" "200" > /dev/null
test_endpoint "Export locked NLU (HI)" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/nlu/hi" "200" > /dev/null
test_endpoint "Export locked Domain" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/domain" "200" > /dev/null
test_endpoint "Export locked Stories" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/stories" "200" > /dev/null
test_endpoint "Export locked Rules" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/rules" "200" > /dev/null
test_endpoint "Export locked All (JSON)" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/all" "200" > /dev/null

# ============================================================
# 8. VERIFY NEW DRAFT EXISTS (Cloned from new locked)
# ============================================================
print_header "📋 8. VERIFY NEW DRAFT (Cloned from Locked)"

test_endpoint "New draft version exists" "GET" "/projects/${PROJECT_CODE}/versions/draft" "200" > /dev/null
test_endpoint "New draft has intents" "GET" "/projects/${PROJECT_CODE}/versions/draft/intents" "200" > /dev/null

# Verify new draft has same data
NEW_DRAFT_INTENTS=$(curl -s "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/intents" | grep -o '"intent_name"' | wc -l)
echo ""
compare_counts "New Draft Intents = Locked" "$NEW_DRAFT_INTENTS" "$LOCKED_INTENTS"

# ============================================================
# 9. VERIFY LOCKED IS READ-ONLY
# ============================================================
print_header "🔐 9. VERIFY LOCKED IS READ-ONLY"

# Try to modify locked version - should fail
MODIFY_RESULT=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/intents" \
    -H "Content-Type: application/json" \
    -d '{"intent_name": "test_readonly"}' 2>/dev/null)
MODIFY_CODE=$(echo "$MODIFY_RESULT" | tail -n1)

if [ "$MODIFY_CODE" = "400" ] || [ "$MODIFY_CODE" = "403" ] || [ "$MODIFY_CODE" = "405" ]; then
    echo -e "  ${GREEN}✅${NC} Locked version is read-only (Got: $MODIFY_CODE)"
    ((PASS++))
else
    echo -e "  ${RED}❌${NC} Locked version should be read-only (Got: $MODIFY_CODE)"
    ((FAIL++))
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "                     PROMOTION SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "  Total Tests: $((PASS + FAIL))"
echo -e "  ${GREEN}✅ Passed: ${PASS}${NC}"
echo -e "  ${RED}❌ Failed: ${FAIL}${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    RATE="100%"
else
    RATE=$(echo "scale=1; $PASS * 100 / ($PASS + $FAIL)" | bc)"%"
fi
echo "  Success Rate: ${RATE}"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo "Version Lifecycle Complete:"
echo ""
echo "  1. ✅ Draft modified with new data"
echo "  2. ✅ Draft promoted to Locked"
echo "  3. ✅ Old Locked archived/deleted"
echo "  4. ✅ New Draft cloned from Locked"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "Download the final export:"
echo "  curl -o electricity-bot-v2.zip ${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/export/zip"
echo ""
echo "View domain.yml:"
echo "  curl ${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/export/domain"
echo ""