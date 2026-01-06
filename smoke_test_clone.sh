#!/bin/bash
# ============================================================
# SMOKE TEST: CLONE & MODIFY
# ============================================================
# This test assumes a locked version already exists
# It clones locked → draft, then modifies some data
# ============================================================

# Colors
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

extract_id() {
    echo "$1" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4
}

# ============================================================
# MAIN SCRIPT
# ============================================================

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  SMOKE TEST: CLONE LOCKED → DRAFT & MODIFY"
echo "════════════════════════════════════════════════════════════════"
echo "  Target: $BASE_URL"
echo "  Project: $PROJECT_CODE"
echo ""

# ============================================================
# 1. VERIFY LOCKED VERSION EXISTS
# ============================================================
print_header "🔍 1. VERIFY LOCKED VERSION EXISTS"

test_endpoint "Check locked version exists" "GET" "/projects/${PROJECT_CODE}/versions/locked" "200" > /dev/null
test_endpoint "Export locked domain" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/domain" "200" > /dev/null

# ============================================================
# 2. CLONE LOCKED TO DRAFT (Already happens after promotion)
# ============================================================
print_header "📋 2. VERIFY DRAFT VERSION (Cloned from Locked)"

test_endpoint "Check draft version exists" "GET" "/projects/${PROJECT_CODE}/versions/draft" "200" > /dev/null
test_endpoint "List draft intents" "GET" "/projects/${PROJECT_CODE}/versions/draft/intents" "200" > /dev/null
test_endpoint "List draft entities" "GET" "/projects/${PROJECT_CODE}/versions/draft/entities" "200" > /dev/null
test_endpoint "List draft slots" "GET" "/projects/${PROJECT_CODE}/versions/draft/slots" "200" > /dev/null
test_endpoint "List draft responses" "GET" "/projects/${PROJECT_CODE}/versions/draft/responses" "200" > /dev/null
test_endpoint "List draft actions" "GET" "/projects/${PROJECT_CODE}/versions/draft/actions" "200" > /dev/null
test_endpoint "List draft forms" "GET" "/projects/${PROJECT_CODE}/versions/draft/forms" "200" > /dev/null
test_endpoint "List draft stories" "GET" "/projects/${PROJECT_CODE}/versions/draft/stories" "200" > /dev/null
test_endpoint "List draft rules" "GET" "/projects/${PROJECT_CODE}/versions/draft/rules" "200" > /dev/null

# ============================================================
# 3. MODIFY INTENTS - Add new intent
# ============================================================
print_header "✏️ 3. MODIFY INTENTS"

test_endpoint "Add new intent (complaint_status)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents" "201" \
    '{"intent_name": "complaint_status"}' > /dev/null

test_endpoint "Add examples to new intent (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/complaint_status/examples" "200" \
    '{"language_code": "en", "examples": ["check complaint status", "complaint update", "what happened to my complaint", "complaint tracking", "track my complaint", "complaint progress", "is my complaint resolved", "complaint status please", "any update on complaint", "check my ticket"]}' > /dev/null

test_endpoint "Add examples to new intent (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/complaint_status/examples" "200" \
    '{"language_code": "hi", "examples": ["शिकायत की स्थिति", "शिकायत अपडेट", "मेरी शिकायत का क्या हुआ", "शिकायत ट्रैकिंग", "शिकायत ट्रैक करो", "शिकायत प्रगति", "क्या शिकायत हल हुई", "शिकायत स्टेटस बताओ", "शिकायत पर कोई अपडेट", "मेरा टिकट चेक करो"]}' > /dev/null

# Update existing intent - add more examples
test_endpoint "Add more examples to greet (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/greet/examples" "200" \
    '{"language_code": "en", "examples": ["hey bot", "hi bot", "hello assistant"]}' > /dev/null

# ============================================================
# 4. MODIFY ENTITIES - Add new entity
# ============================================================
print_header "🏷️ 4. MODIFY ENTITIES"

test_endpoint "Add new entity (complaint_id)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "complaint_id", "entity_type": "text", "use_regex": true}' > /dev/null

test_endpoint "Add regex for complaint_id" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes" "201" \
    '{"regex_name": "complaint_id", "entity_key": "complaint_id"}' > /dev/null

test_endpoint "Add regex pattern for complaint_id" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes/complaint_id/examples" "200" \
    '{"language_code": "en", "examples": ["CMP[0-9]{6}"]}' > /dev/null

# ============================================================
# 5. MODIFY SLOTS - Add new slot
# ============================================================
print_header "📦 5. MODIFY SLOTS"

test_endpoint "Add new slot (complaint_id)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "complaint_id", "slot_type": "text", "influence_conversation": true}' > /dev/null

test_endpoint "Add mapping for complaint_id" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/complaint_id/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "complaint_id"}' > /dev/null

# Update existing slot - add new mapping
test_endpoint "Add new mapping to request_type" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/request_type/mappings" "201" \
    '{"mapping_type": "from_intent", "intent": "complaint_status", "value": "complaint_status"}' > /dev/null

# ============================================================
# 6. MODIFY RESPONSES - Add new response
# ============================================================
print_header "💬 6. MODIFY RESPONSES"

test_endpoint "Add new response (utter_complaint_status)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses" "201" \
    '{"name": "utter_complaint_status"}' > /dev/null

test_endpoint "Add variant to new response (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses/utter_complaint_status/variants" "201" \
    '{"language_code": "en", "priority": 0, "components": [{"component_type": "text", "payload": {"text": "Your complaint {complaint_id} is currently being processed. We will update you soon."}}]}' > /dev/null

test_endpoint "Add variant to new response (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses/utter_complaint_status/variants" "201" \
    '{"language_code": "hi", "priority": 0, "components": [{"component_type": "text", "payload": {"text": "आपकी शिकायत {complaint_id} पर काम चल रहा है। हम जल्द ही अपडेट देंगे।"}}]}' > /dev/null

test_endpoint "Add new response (utter_ask_complaint_id)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses" "201" \
    '{"name": "utter_ask_complaint_id"}' > /dev/null

test_endpoint "Add variant (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses/utter_ask_complaint_id/variants" "201" \
    '{"language_code": "en", "priority": 0, "components": [{"component_type": "text", "payload": {"text": "Please provide your complaint ID (e.g., CMP123456)."}}]}' > /dev/null

# Update existing response - add new variant
test_endpoint "Add Hindi variant to utter_greet" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses/utter_greet/variants" "201" \
    '{"language_code": "hi", "priority": 1, "components": [{"component_type": "text", "payload": {"text": "नमस्कार! बिजली सेवा में आपका स्वागत है। कैसे मदद करूं?"}}]}' > /dev/null

# ============================================================
# 7. MODIFY ACTIONS - Add new action
# ============================================================
print_header "⚡ 7. MODIFY ACTIONS"

test_endpoint "Add new action (action_check_complaint)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_check_complaint", "description": "Check complaint status from database"}' > /dev/null

test_endpoint "Add new action (validate_complaint_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "validate_complaint_form", "description": "Validate complaint form inputs"}' > /dev/null

# ============================================================
# 8. MODIFY FORMS - Add new form
# ============================================================
print_header "📋 8. MODIFY FORMS"

test_endpoint "Add new form (complaint_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms" "201" \
    '{"name": "complaint_form"}' > /dev/null

test_endpoint "Add slot to complaint_form" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/complaint_form/slots" "201" \
    '{"slot_name": "complaint_id"}' > /dev/null

test_endpoint "Add mapping to complaint_form slot" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/complaint_form/slots/complaint_id/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "complaint_id"}' > /dev/null

test_endpoint "Add from_text mapping" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/complaint_form/slots/complaint_id/mappings" "201" \
    '{"mapping_type": "from_text"}' > /dev/null

# ============================================================
# 9. MODIFY STORIES - Add new story
# ============================================================
print_header "📖 9. MODIFY STORIES"

STORY=$(test_endpoint "Add new story (check complaint status)" "POST" "/projects/${PROJECT_CODE}/versions/draft/stories" "201" \
    '{"name": "check complaint status"}')
STORY_ID=$(extract_id "$STORY")

test_endpoint "Add step: intent complaint_status" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "complaint_status", "timeline_index": 0, "step_order": 0}' > /dev/null

test_endpoint "Add step: action utter_ask_complaint_id" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_ask_complaint_id", "timeline_index": 0, "step_order": 1}' > /dev/null

test_endpoint "Add step: active_loop complaint_form" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "active_loop", "form_name": "complaint_form", "timeline_index": 0, "step_order": 2}' > /dev/null

STEP=$(test_endpoint "Add step: intent inform with complaint_id" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "inform", "timeline_index": 1, "step_order": 0, "entities": [{"entity_key": "complaint_id", "value": "CMP123456"}]}')
STEP_ID=$(extract_id "$STEP")

test_endpoint "Add slot event: complaint_id" "POST" "/projects/story-steps/${STEP_ID}/slot-events" "201" \
    '{"slot_name": "complaint_id", "value": "CMP123456"}' > /dev/null

test_endpoint "Add step: active_loop null" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "active_loop", "active_loop_value": null, "timeline_index": 1, "step_order": 1}' > /dev/null

test_endpoint "Add step: action action_check_complaint" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "action", "action_name": "action_check_complaint", "timeline_index": 1, "step_order": 2}' > /dev/null

test_endpoint "Add step: action utter_complaint_status" "POST" "/projects/stories/${STORY_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_complaint_status", "timeline_index": 1, "step_order": 3}' > /dev/null

# ============================================================
# 10. MODIFY RULES - Add new rule
# ============================================================
print_header "📜 10. MODIFY RULES"

RULE=$(test_endpoint "Add new rule (activate complaint form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "activate complaint form"}')
RULE_ID=$(extract_id "$RULE")

test_endpoint "Add rule step: intent complaint_status" "POST" "/projects/rules/${RULE_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "complaint_status", "step_order": 0}' > /dev/null

test_endpoint "Add rule step: action utter_ask_complaint_id" "POST" "/projects/rules/${RULE_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_ask_complaint_id", "step_order": 1}' > /dev/null

test_endpoint "Add rule step: active_loop complaint_form" "POST" "/projects/rules/${RULE_ID}/steps" "201" \
    '{"step_type": "active_loop", "form_name": "complaint_form", "step_order": 2}' > /dev/null

# Rule with condition
RULE2=$(test_endpoint "Add rule (submit complaint form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "submit complaint form"}')
RULE2_ID=$(extract_id "$RULE2")

test_endpoint "Add rule condition: active_loop = complaint_form" "POST" "/projects/rules/${RULE2_ID}/conditions" "201" \
    '{"condition_type": "active_loop", "active_loop": "complaint_form"}' > /dev/null

test_endpoint "Add rule step: active_loop complaint_form" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "active_loop", "form_name": "complaint_form", "step_order": 0}' > /dev/null

test_endpoint "Add rule step: active_loop null" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "active_loop", "active_loop_value": null, "step_order": 1}' > /dev/null

test_endpoint "Add rule step: action action_check_complaint" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "action", "action_name": "action_check_complaint", "step_order": 2}' > /dev/null

test_endpoint "Add rule step: action utter_complaint_status" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_complaint_status", "step_order": 3}' > /dev/null

# ============================================================
# 11. DELETE SOME DATA (Optional modifications)
# ============================================================
print_header "🗑️ 11. DELETE SOME DATA"

# Delete an existing synonym (if exists)
test_endpoint "Delete synonym (power_outage EN)" "DELETE" "/projects/${PROJECT_CODE}/versions/draft/synonyms/complaint_type/power_outage/en" "200" > /dev/null

# ============================================================
# 12. VERIFY MODIFICATIONS
# ============================================================
print_header "✅ 12. VERIFY MODIFICATIONS"

test_endpoint "Verify new intent exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/intents/complaint_status" "200" > /dev/null
test_endpoint "Verify new entity exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/entities/complaint_id" "200" > /dev/null
test_endpoint "Verify new slot exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/slots/complaint_id" "200" > /dev/null
test_endpoint "Verify new response exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/responses/utter_complaint_status" "200" > /dev/null
test_endpoint "Verify new action exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/actions/action_check_complaint" "200" > /dev/null
test_endpoint "Verify new form exists" "GET" "/projects/${PROJECT_CODE}/versions/draft/forms/complaint_form" "200" > /dev/null

# ============================================================
# 13. EXPORT DRAFT (Verify it's valid)
# ============================================================
print_header "📤 13. EXPORT DRAFT"

test_endpoint "Export draft NLU (EN)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/en" "200" > /dev/null
test_endpoint "Export draft NLU (HI)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/hi" "200" > /dev/null
test_endpoint "Export draft Domain" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/domain" "200" > /dev/null
test_endpoint "Export draft Stories" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/stories" "200" > /dev/null
test_endpoint "Export draft Rules" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/rules" "200" > /dev/null

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "                     CLONE & MODIFY SUMMARY"
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
echo "Modifications Made:"
echo "  • Added intent: complaint_status (with EN/HI examples)"
echo "  • Added entity: complaint_id (with regex)"
echo "  • Added slot: complaint_id (with mapping)"
echo "  • Added responses: utter_complaint_status, utter_ask_complaint_id"
echo "  • Added actions: action_check_complaint, validate_complaint_form"
echo "  • Added form: complaint_form (with slot mappings)"
echo "  • Added story: check complaint status (8 steps)"
echo "  • Added rules: activate complaint form, submit complaint form"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo -e "${YELLOW}Ready to promote! Run:${NC}"
echo "  ./smoke_test_promote.sh $BASE_URL"
echo ""