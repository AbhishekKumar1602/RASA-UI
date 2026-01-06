#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8000/api/v1}"
PROJECT_CODE="electricity-bot"

PASS=0
FAIL=0


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
        echo -e "  ${GREEN}✅${NC} $name" >&2
        ((PASS++))
    else
        echo -e "  ${RED}❌${NC} $name (Expected: $expected_code, Got: $http_code)" >&2
        echo "     Response: $body" >&2
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
echo "  ELECTRICITY CHATBOT - COMPLETE SMOKE TEST v8"
echo "  FIXED: timeline_index + step_order for steps"
echo "════════════════════════════════════════════════════════════════"
echo "  Target: $BASE_URL"
echo "  Project: $PROJECT_CODE"
echo ""

# ============================================================
# 1. LANGUAGES
# ============================================================
print_header "📚 1. LANGUAGES"

test_endpoint "Create Language (English)" "POST" "/languages/" "201" \
    '{"language_code": "en", "language_name": "English"}' > /dev/null

test_endpoint "Create Language (Hindi)" "POST" "/languages/" "201" \
    '{"language_code": "hi", "language_name": "Hindi"}' > /dev/null

# ============================================================
# 2. PROJECT
# ============================================================
print_header "📁 2. PROJECT"

test_endpoint "Create Project" "POST" "/projects/" "201" \
    '{"project_code": "electricity-bot", "project_name": "Electricity Chatbot"}' > /dev/null

# ============================================================
# 3. PROJECT LANGUAGES
# ============================================================
print_header "🌐 3. PROJECT LANGUAGES"

test_endpoint "Add English to Project" "POST" "/projects/${PROJECT_CODE}/languages" "201" \
    '{"language_code": "en"}' > /dev/null

test_endpoint "Add Hindi to Project" "POST" "/projects/${PROJECT_CODE}/languages" "201" \
    '{"language_code": "hi"}' > /dev/null

# ============================================================
# 4. VERSION LANGUAGES
# ============================================================
print_header "🗣️ 4. VERSION LANGUAGES"

test_endpoint "Add English to Draft" "POST" "/projects/${PROJECT_CODE}/versions/draft/languages" "201" \
    '{"language_code": "en"}' > /dev/null

test_endpoint "Add Hindi to Draft" "POST" "/projects/${PROJECT_CODE}/versions/draft/languages" "201" \
    '{"language_code": "hi"}' > /dev/null

# ============================================================
# 5. SESSION CONFIG
# ============================================================
print_header "⚙️ 5. SESSION CONFIG"

test_endpoint "Set Session Config" "PUT" "/projects/${PROJECT_CODE}/versions/draft/session-config" "200" \
    '{"session_expiration_time": 60, "carry_over_slots_to_new_session": true}' > /dev/null

# ============================================================
# 6. INTENTS
# ============================================================
print_header "💡 6. INTENTS"

INTENTS=("greet" "goodbye" "thanks" "affirm" "deny" "out_of_scope" "nlu_fallback" 
         "select_language" "request_duplicate_bill" "report_power_outage" "meter_issue"
         "check_payment_status" "provide_account_number" "provide_mobile_number" 
         "provide_amount" "inform" "register")

for intent in "${INTENTS[@]}"; do
    test_endpoint "Create Intent ($intent)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents" "201" \
        "{\"intent_name\": \"$intent\"}" > /dev/null
done

# ============================================================
# 7. INTENT EXAMPLES - ENGLISH (10+ examples each)
# ============================================================
print_header "📝 7. INTENT EXAMPLES - ENGLISH"

test_endpoint "Examples: greet (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/greet/examples" "200" \
    '{"language_code": "en", "examples": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "hi there", "hello there", "greetings", "howdy"]}' > /dev/null

test_endpoint "Examples: goodbye (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/goodbye/examples" "200" \
    '{"language_code": "en", "examples": ["bye", "goodbye", "see you", "take care", "bye bye", "see you later", "good night", "farewell", "catch you later", "im leaving"]}' > /dev/null

test_endpoint "Examples: thanks (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/thanks/examples" "200" \
    '{"language_code": "en", "examples": ["thank you", "thanks", "thanks a lot", "thank you so much", "appreciate it", "thanks for your help", "many thanks", "thx", "ty", "cheers"]}' > /dev/null

test_endpoint "Examples: affirm (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/affirm/examples" "200" \
    '{"language_code": "en", "examples": ["yes", "yeah", "yep", "correct", "right", "sure", "absolutely", "of course", "yes please", "thats right"]}' > /dev/null

test_endpoint "Examples: deny (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/deny/examples" "200" \
    '{"language_code": "en", "examples": ["no", "nope", "not really", "no thanks", "wrong", "incorrect", "never", "not at all", "negative", "nah"]}' > /dev/null

test_endpoint "Examples: select_language (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/select_language/examples" "200" \
    '{"language_code": "en", "examples": ["english please", "i want english", "switch to english", "hindi please", "change to hindi", "use english", "speak english", "prefer english", "select hindi", "i speak english"]}' > /dev/null

test_endpoint "Examples: request_duplicate_bill (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/request_duplicate_bill/examples" "200" \
    '{"language_code": "en", "examples": ["i need a duplicate bill", "can i get a copy of my bill", "duplicate bill please", "send me my bill again", "i lost my bill", "need another copy", "resend my bill", "bill copy required", "reprint my bill", "get duplicate bill"]}' > /dev/null

test_endpoint "Examples: report_power_outage (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/report_power_outage/examples" "200" \
    '{"language_code": "en", "examples": ["there is no power", "power outage in my area", "electricity is gone", "power cut", "no electricity", "blackout", "light went off", "power failure", "no current", "electricity outage"]}' > /dev/null

test_endpoint "Examples: meter_issue (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/meter_issue/examples" "200" \
    '{"language_code": "en", "examples": ["my meter is not working", "meter problem", "faulty meter", "meter showing wrong reading", "meter is broken", "issue with my meter", "meter defective", "meter stopped", "wrong meter reading", "meter malfunction"]}' > /dev/null

test_endpoint "Examples: check_payment_status (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/check_payment_status/examples" "200" \
    '{"language_code": "en", "examples": ["check my payment", "payment status", "did my payment go through", "is my bill paid", "verify payment", "payment confirmation", "check if paid", "payment received", "bill payment status", "payment enquiry"]}' > /dev/null

test_endpoint "Examples: provide_account_number (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_account_number/examples" "200" \
    '{"language_code": "en", "examples": ["my account number is [12345678](account_number)", "account [87654321](account_number)", "[11223344](account_number)", "the account is [99887766](account_number)", "account number [55443322](account_number)", "its [12341234](account_number)", "number is [98769876](account_number)", "acc no [45674567](account_number)", "[11111111](account_number)", "account id [22222222](account_number)"]}' > /dev/null

test_endpoint "Examples: provide_mobile_number (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_mobile_number/examples" "200" \
    '{"language_code": "en", "examples": ["my mobile is [9876543210](mobile_number)", "phone [8765432109](mobile_number)", "[7654321098](mobile_number)", "contact me at [6543210987](mobile_number)", "mobile number [9988776655](mobile_number)", "call me on [8877665544](mobile_number)", "number is [7766554433](mobile_number)", "[6655443322](mobile_number) is my phone", "reach me at [9123456789](mobile_number)", "phone number [8234567890](mobile_number)"]}' > /dev/null

test_endpoint "Examples: provide_amount (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_amount/examples" "200" \
    '{"language_code": "en", "examples": ["the amount is [500](amount)", "[1000](amount) rupees", "pay [2500](amount)", "bill amount [750](amount)", "[1500](amount)", "amount [3000](amount)", "[250](amount) rs", "total is [5000](amount)", "[100](amount) only", "its [2000](amount)"]}' > /dev/null

test_endpoint "Examples: out_of_scope (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/out_of_scope/examples" "200" \
    '{"language_code": "en", "examples": ["what is the weather", "tell me a joke", "who is the president", "play music", "order food", "book a flight", "whats the time", "calculate 2+2", "translate hello", "search google"]}' > /dev/null

test_endpoint "Examples: inform (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/inform/examples" "200" \
    '{"language_code": "en", "examples": ["i live in [Delhi](city)", "my city is [Mumbai](city)", "my email is [test@example.com](email)", "[Bangalore](city)", "located in [Chennai](city)", "from [Kolkata](city)", "[user@gmail.com](email)", "email [contact@test.com](email)", "i am a [registered](user_type) user", "[guest](user_type) user"]}' > /dev/null

test_endpoint "Examples: register (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/register/examples" "200" \
    '{"language_code": "en", "examples": ["i want to register", "new registration", "sign me up", "create account", "register me", "new user registration", "open new account", "signup", "create new account", "enroll me"]}' > /dev/null

test_endpoint "Examples: nlu_fallback (EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/nlu_fallback/examples" "200" \
    '{"language_code": "en", "examples": ["asdfgh", "qwerty", "xyz123", "random text here", "jklmno", "gibberish", "aaaaaa", "123abc456", "nothing useful", "blahblah"]}' > /dev/null

# ============================================================
# 8. INTENT EXAMPLES - HINDI (10+ examples each)
# ============================================================
print_header "📝 8. INTENT EXAMPLES - HINDI"

test_endpoint "Examples: greet (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/greet/examples" "200" \
    '{"language_code": "hi", "examples": ["नमस्ते", "नमस्कार", "हेलो", "हाय", "सुप्रभात", "शुभ संध्या", "प्रणाम", "राम राम", "जय हिंद", "आदाब"]}' > /dev/null

test_endpoint "Examples: goodbye (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/goodbye/examples" "200" \
    '{"language_code": "hi", "examples": ["अलविदा", "फिर मिलेंगे", "बाय", "शुभ रात्रि", "चलता हूं", "नमस्ते फिर से", "टाटा", "बाय बाय", "फिर मिलते हैं", "जाता हूं"]}' > /dev/null

test_endpoint "Examples: thanks (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/thanks/examples" "200" \
    '{"language_code": "hi", "examples": ["धन्यवाद", "शुक्रिया", "बहुत धन्यवाद", "थैंक यू", "आभार", "बहुत शुक्रिया", "मेहरबानी", "थैंक्स", "आपका धन्यवाद", "बड़ी मेहरबानी"]}' > /dev/null

test_endpoint "Examples: affirm (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/affirm/examples" "200" \
    '{"language_code": "hi", "examples": ["हां", "हाँ", "जी हां", "बिल्कुल", "सही है", "ठीक है", "जरूर", "अवश्य", "हां जी", "बिल्कुल सही"]}' > /dev/null

test_endpoint "Examples: deny (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/deny/examples" "200" \
    '{"language_code": "hi", "examples": ["नहीं", "ना", "जी नहीं", "गलत है", "नहीं चाहिए", "बिल्कुल नहीं", "कभी नहीं", "नो", "गलत", "ऐसा नहीं है"]}' > /dev/null

test_endpoint "Examples: select_language (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/select_language/examples" "200" \
    '{"language_code": "hi", "examples": ["हिंदी में बात करो", "हिंदी चाहिए", "भाषा बदलो", "हिंदी सेलेक्ट करो", "मुझे हिंदी में चाहिए", "हिंदी भाषा", "हिंदी में बोलो", "अंग्रेजी में", "इंग्लिश में बात करो", "भाषा हिंदी करो"]}' > /dev/null

test_endpoint "Examples: request_duplicate_bill (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/request_duplicate_bill/examples" "200" \
    '{"language_code": "hi", "examples": ["डुप्लीकेट बिल चाहिए", "बिल की कॉपी दो", "बिल फिर से भेजो", "मेरा बिल खो गया", "बिल की नकल", "दोबारा बिल भेजो", "बिल कॉपी", "फिर से बिल दो", "डुप्लीकेट बिल बनाओ", "बिल दुबारा"]}' > /dev/null

test_endpoint "Examples: report_power_outage (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/report_power_outage/examples" "200" \
    '{"language_code": "hi", "examples": ["बिजली नहीं है", "लाइट गई है", "पावर कट है", "बिजली चली गई", "करंट नहीं आ रहा", "बिजली गुल है", "लाइट नहीं है", "पावर नहीं है", "बिजली की समस्या", "आउटेज है"]}' > /dev/null

test_endpoint "Examples: meter_issue (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/meter_issue/examples" "200" \
    '{"language_code": "hi", "examples": ["मीटर खराब है", "मीटर में समस्या है", "मीटर काम नहीं कर रहा", "मीटर की रीडिंग गलत है", "मीटर टूट गया", "मीटर बंद है", "मीटर में दिक्कत", "मीटर सही नहीं है", "मीटर चेक करो", "मीटर की शिकायत"]}' > /dev/null

test_endpoint "Examples: check_payment_status (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/check_payment_status/examples" "200" \
    '{"language_code": "hi", "examples": ["पेमेंट स्टेटस बताओ", "भुगतान हुआ या नहीं", "पैसे कटे या नहीं", "बिल भरा है या नहीं", "पेमेंट चेक करो", "भुगतान की स्थिति", "क्या पेमेंट हो गया", "पैसे मिले या नहीं", "बिल पेमेंट स्टेटस", "भुगतान वेरीफाई करो"]}' > /dev/null

test_endpoint "Examples: provide_account_number (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_account_number/examples" "200" \
    '{"language_code": "hi", "examples": ["मेरा अकाउंट नंबर [12345678](account_number) है", "अकाउंट [87654321](account_number)", "[11223344](account_number) है मेरा", "खाता संख्या [99887766](account_number)", "नंबर है [55443322](account_number)", "[12341234](account_number) यह है", "अकाउंट आईडी [98769876](account_number)", "[45674567](account_number)", "मेरा नंबर [11111111](account_number)", "[22222222](account_number) अकाउंट"]}' > /dev/null

test_endpoint "Examples: provide_mobile_number (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_mobile_number/examples" "200" \
    '{"language_code": "hi", "examples": ["मेरा मोबाइल [9876543210](mobile_number) है", "फोन नंबर [8765432109](mobile_number)", "[7654321098](mobile_number) पर कॉल करो", "मोबाइल [6543210987](mobile_number)", "[9988776655](mobile_number) है नंबर", "फोन [8877665544](mobile_number)", "[7766554433](mobile_number)", "नंबर [6655443322](mobile_number) है", "मोबाइल नंबर [9123456789](mobile_number)", "[8234567890](mobile_number)"]}' > /dev/null

test_endpoint "Examples: provide_amount (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/provide_amount/examples" "200" \
    '{"language_code": "hi", "examples": ["राशि [500](amount) है", "[1000](amount) रुपये", "[2500](amount) भरने हैं", "बिल [750](amount) का है", "[1500](amount) देने हैं", "अमाउंट [3000](amount)", "[250](amount) रुपए", "टोटल [5000](amount)", "[100](amount) ही है", "[2000](amount) है बिल"]}' > /dev/null

test_endpoint "Examples: out_of_scope (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/out_of_scope/examples" "200" \
    '{"language_code": "hi", "examples": ["मौसम कैसा है", "चुटकुला सुनाओ", "प्रधानमंत्री कौन है", "गाना बजाओ", "खाना ऑर्डर करो", "फ्लाइट बुक करो", "टाइम क्या हुआ", "2+2 कितना होता है", "हिंदी में ट्रांसलेट करो", "गूगल पर खोजो"]}' > /dev/null

test_endpoint "Examples: inform (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/inform/examples" "200" \
    '{"language_code": "hi", "examples": ["मैं [दिल्ली](city) में रहता हूं", "शहर [मुंबई](city) है", "[बैंगलोर](city)", "[चेन्नई](city) से हूं", "[कोलकाता](city) में", "ईमेल [test@example.com](email) है", "[user@gmail.com](email)", "मेल [contact@test.com](email)", "मैं [registered](user_type) यूजर हूं", "[guest](user_type) हूं"]}' > /dev/null

test_endpoint "Examples: register (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/register/examples" "200" \
    '{"language_code": "hi", "examples": ["रजिस्टर करना है", "नया पंजीकरण", "साइन अप करो", "अकाउंट बनाओ", "मुझे रजिस्टर करो", "नया यूजर पंजीकरण", "नया खाता खोलो", "साइनअप", "नया अकाउंट बनाना है", "मुझे जोड़ो"]}' > /dev/null

test_endpoint "Examples: nlu_fallback (HI)" "POST" "/projects/${PROJECT_CODE}/versions/draft/intents/nlu_fallback/examples" "200" \
    '{"language_code": "hi", "examples": ["असदफघ", "क्वेर्टी", "एक्सवाईजेड", "कुछ भी रैंडम", "जेकेएलएम", "बकवास", "आआआआ", "123एबीसी", "कुछ नहीं", "फालतू"]}' > /dev/null


# ============================================================
# 9. ENTITIES
# ============================================================
print_header "🏷️ 9. ENTITIES"

test_endpoint "Create Entity (account_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "account_number", "entity_type": "text", "use_regex": true}' > /dev/null

test_endpoint "Create Entity (mobile_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "mobile_number", "entity_type": "text", "use_regex": true}' > /dev/null

test_endpoint "Create Entity (amount)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "amount", "entity_type": "numeric"}' > /dev/null

test_endpoint "Create Entity (request_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "request_type", "entity_type": "text", "use_lookup": true}' > /dev/null

test_endpoint "Create Entity (complaint_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "complaint_type", "entity_type": "text", "use_lookup": true}' > /dev/null

test_endpoint "Create Entity (language)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "language", "entity_type": "text"}' > /dev/null

test_endpoint "Create Entity (city)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "city", "entity_type": "text"}' > /dev/null

test_endpoint "Create Entity (email)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "email", "entity_type": "text"}' > /dev/null

test_endpoint "Create Entity (user_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/entities" "201" \
    '{"entity_key": "user_type", "entity_type": "text"}' > /dev/null

# ============================================================
# 10. REGEX PATTERNS
# ============================================================
print_header "🔤 10. REGEX PATTERNS"

test_endpoint "Create Regex (account_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes" "201" \
    '{"regex_name": "account_number", "entity_key": "account_number"}' > /dev/null

test_endpoint "Regex Examples: account_number" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes/account_number/examples" "200" \
    '{"language_code": "en", "examples": ["\\d{8,12}"]}' > /dev/null

test_endpoint "Create Regex (mobile_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes" "201" \
    '{"regex_name": "mobile_number", "entity_key": "mobile_number"}' > /dev/null

test_endpoint "Regex Examples: mobile_number" "POST" "/projects/${PROJECT_CODE}/versions/draft/regexes/mobile_number/examples" "200" \
    '{"language_code": "en", "examples": ["[6-9]\\d{9}"]}' > /dev/null

# ============================================================
# 11. LOOKUP TABLES
# ============================================================
print_header "📖 11. LOOKUP TABLES"

test_endpoint "Create Lookup (request_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/lookups" "201" \
    '{"lookup_name": "request_type", "entity_key": "request_type"}' > /dev/null

test_endpoint "Lookup Examples: request_type" "POST" "/projects/${PROJECT_CODE}/versions/draft/lookups/request_type/examples" "200" \
    '{"language_code": "en", "examples": ["duplicate bill", "bill copy", "outage report", "power cut"]}' > /dev/null

test_endpoint "Create Lookup (complaint_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/lookups" "201" \
    '{"lookup_name": "complaint_type", "entity_key": "complaint_type"}' > /dev/null

test_endpoint "Lookup Examples: complaint_type" "POST" "/projects/${PROJECT_CODE}/versions/draft/lookups/complaint_type/examples" "200" \
    '{"language_code": "en", "examples": ["power outage", "voltage fluctuation", "meter fault", "billing error"]}' > /dev/null

# ============================================================
# 12. SYNONYMS
# ============================================================
print_header "🔄 12. SYNONYMS"

test_endpoint "Create Synonym (duplicate_bill EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/synonyms" "201" \
    '{"entity_key": "request_type", "canonical_value": "duplicate_bill", "language_code": "en", "examples": ["bill copy", "copy of bill", "duplicate"]}' > /dev/null

test_endpoint "Create Synonym (power_outage EN)" "POST" "/projects/${PROJECT_CODE}/versions/draft/synonyms" "201" \
    '{"entity_key": "complaint_type", "canonical_value": "power_outage", "language_code": "en", "examples": ["no power", "blackout", "power cut"]}' > /dev/null

# ============================================================
# 13. SLOTS
# ============================================================
print_header "📦 13. SLOTS"

test_endpoint "Create Slot (account_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "account_number", "slot_type": "text", "influence_conversation": true}' > /dev/null

test_endpoint "Create Slot (mobile_number)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "mobile_number", "slot_type": "text", "influence_conversation": false}' > /dev/null

test_endpoint "Create Slot (request_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "request_type", "slot_type": "categorical", "influence_conversation": true, "values": ["duplicate_bill", "outage_report", "meter_issue", "payment_status"]}' > /dev/null

test_endpoint "Create Slot (language)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "language", "slot_type": "categorical", "influence_conversation": true, "values": ["en", "hi"]}' > /dev/null

test_endpoint "Create Slot (amount)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "amount", "slot_type": "float", "influence_conversation": false, "min_value": 0.0, "max_value": 1000000.0}' > /dev/null

test_endpoint "Create Slot (urgent)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "urgent", "slot_type": "bool", "influence_conversation": true}' > /dev/null

test_endpoint "Create Slot (city)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "city", "slot_type": "text", "influence_conversation": true}' > /dev/null

test_endpoint "Create Slot (email)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "email", "slot_type": "text", "influence_conversation": false}' > /dev/null

test_endpoint "Create Slot (user_type)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots" "201" \
    '{"name": "user_type", "slot_type": "categorical", "influence_conversation": true, "values": ["registered", "guest"]}' > /dev/null

# ============================================================
# 14. SLOT MAPPINGS
# ============================================================
print_header "🔗 14. SLOT MAPPINGS"

test_endpoint "Mapping: account_number (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/account_number/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "account_number"}' > /dev/null

test_endpoint "Mapping: account_number (from_text)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/account_number/mappings" "201" \
    '{"mapping_type": "from_text", "conditions": [{"active_loop": "request_form"}, {"active_loop": "outage_form"}]}' > /dev/null

test_endpoint "Mapping: request_type (from_intent)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/request_type/mappings" "201" \
    '{"mapping_type": "from_intent", "intent": "request_duplicate_bill", "value": "duplicate_bill"}' > /dev/null

test_endpoint "Mapping: request_type (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/request_type/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "request_type"}' > /dev/null

test_endpoint "Mapping: language (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/language/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "language"}' > /dev/null

test_endpoint "Mapping: amount (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/amount/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "amount"}' > /dev/null

test_endpoint "Mapping: urgent (from_intent affirm)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/urgent/mappings" "201" \
    '{"mapping_type": "from_intent", "intent": "affirm", "value": "true"}' > /dev/null

test_endpoint "Mapping: city (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/city/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "city"}' > /dev/null

test_endpoint "Mapping: email (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/email/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "email"}' > /dev/null

test_endpoint "Mapping: user_type (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/slots/user_type/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "user_type"}' > /dev/null

# ============================================================
# 15. CUSTOM ACTIONS
# ============================================================
print_header "⚡ 15. CUSTOM ACTIONS"

test_endpoint "Create Action (action_save_request_to_db)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_save_request_to_db"}' > /dev/null

test_endpoint "Create Action (action_handle_outage_report)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_handle_outage_report"}' > /dev/null

test_endpoint "Create Action (action_check_payment_status)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_check_payment_status"}' > /dev/null

test_endpoint "Create Action (validate_request_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "validate_request_form"}' > /dev/null

test_endpoint "Create Action (validate_outage_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "validate_outage_form"}' > /dev/null

test_endpoint "Create Action (action_submit_registration)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_submit_registration"}' > /dev/null

test_endpoint "Create Action (action_default_fallback)" "POST" "/projects/${PROJECT_CODE}/versions/draft/actions" "201" \
    '{"name": "action_default_fallback"}' > /dev/null

# ============================================================
# 16. RESPONSES
# ============================================================
print_header "💬 16. RESPONSES"

RESPONSES=("utter_greet" "utter_choose_language" "utter_select_service" "utter_help_topics"
           "utter_fallback" "utter_submit_request" "utter_selected_language" "utter_confirm_city"
           "utter_acknowledge" "utter_start_registration" "utter_registration_complete"
           "utter_welcome_back" "utter_email_received" "utter_ask_continue")

for resp in "${RESPONSES[@]}"; do
    test_endpoint "Create Response ($resp)" "POST" "/projects/${PROJECT_CODE}/versions/draft/responses" "201" \
        "{\"name\": \"$resp\"}" > /dev/null
done

# ============================================================
# 16b. RESPONSE VARIANTS
# ============================================================
print_header "💬 16b. RESPONSE VARIANTS"

add_text_variant() {
    local response_name="$1"
    local lang="$2"
    local text="$3"
    
    result=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/responses/${response_name}/variants" \
        -H "Content-Type: application/json" \
        -d "{\"language_code\": \"${lang}\", \"priority\": 0, \"components\": [{\"component_type\": \"text\", \"payload\": {\"text\": \"${text}\"}}]}" 2>/dev/null)
    
    http_code=$(echo "$result" | tail -n1)
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "  ${GREEN}✅${NC} Variant: ${response_name} (${lang})"
        ((PASS++))
    else
        echo -e "  ${RED}❌${NC} Variant: ${response_name} (${lang}) - Code: $http_code"
        ((FAIL++))
    fi
}

add_button_variant() {
    local response_name="$1"
    local lang="$2"
    local text="$3"
    local buttons="$4"
    
    result=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/projects/${PROJECT_CODE}/versions/draft/responses/${response_name}/variants" \
        -H "Content-Type: application/json" \
        -d "{\"language_code\": \"${lang}\", \"priority\": 0, \"components\": [{\"component_type\": \"text\", \"payload\": {\"text\": \"${text}\"}}, {\"component_type\": \"buttons\", \"payload\": {\"buttons\": ${buttons}}}]}" 2>/dev/null)
    
    http_code=$(echo "$result" | tail -n1)
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "  ${GREEN}✅${NC} Variant+Buttons: ${response_name} (${lang})"
        ((PASS++))
    else
        echo -e "  ${RED}❌${NC} Variant+Buttons: ${response_name} (${lang}) - Code: $http_code"
        ((FAIL++))
    fi
}

add_text_variant "utter_greet" "en" "Hello! Welcome to our Electricity Service. How can I help you today?"
add_text_variant "utter_greet" "hi" "नमस्ते! हमारी बिजली सेवा में आपका स्वागत है।"
add_button_variant "utter_choose_language" "en" "Please select your preferred language:" \
    '[{"title": "English", "payload": "/select_language"}, {"title": "Hindi", "payload": "/select_language"}]'
add_button_variant "utter_select_service" "en" "What would you like to do?" \
    '[{"title": "Duplicate Bill", "payload": "/request_duplicate_bill"}, {"title": "Report Outage", "payload": "/report_power_outage"}]'
add_text_variant "utter_help_topics" "en" "I can help you with: billing, outage reports, meter issues, and payment status."
add_text_variant "utter_fallback" "en" "I am sorry, I did not understand that. Could you please rephrase?"
add_text_variant "utter_fallback" "hi" "मुझे खेद है, मैं समझ नहीं पाया।"
add_text_variant "utter_submit_request" "en" "Your request has been submitted successfully."
add_text_variant "utter_selected_language" "en" "You have selected English."
add_text_variant "utter_confirm_city" "en" "You are located in {city}. Is that correct?"
add_text_variant "utter_acknowledge" "en" "Got it, thank you!"
add_text_variant "utter_start_registration" "en" "Let us get you registered."
add_text_variant "utter_registration_complete" "en" "Registration complete! Your account has been created."
add_text_variant "utter_welcome_back" "en" "Welcome back! Good to see you again."
add_text_variant "utter_email_received" "en" "Thank you! I have noted your email as {email}."
add_button_variant "utter_ask_continue" "en" "Would you like to continue?" \
    '[{"title": "Yes", "payload": "/affirm"}, {"title": "No", "payload": "/deny"}]'

# ============================================================
# 17. FORMS
# ============================================================
print_header "📋 17. FORMS"

test_endpoint "Create Form (request_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms" "201" \
    '{"name": "request_form"}' > /dev/null

test_endpoint "Create Form (outage_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms" "201" \
    '{"name": "outage_form"}' > /dev/null

test_endpoint "Create Form (registration_form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms" "201" \
    '{"name": "registration_form"}' > /dev/null

# ============================================================
# 18. FORM SLOTS & MAPPINGS
# ============================================================
print_header "📝 18. FORM SLOTS & MAPPINGS"

test_endpoint "Form Slot: request_form/account_number" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/request_form/slots" "201" \
    '{"slot_name": "account_number"}' > /dev/null

test_endpoint "Form Slot: request_form/request_type" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/request_form/slots" "201" \
    '{"slot_name": "request_type"}' > /dev/null

test_endpoint "Form Mapping: request_form/account_number (from_entity)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/request_form/slots/account_number/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "account_number"}' > /dev/null

test_endpoint "Form Mapping: request_form/account_number (from_text)" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/request_form/slots/account_number/mappings" "201" \
    '{"mapping_type": "from_text"}' > /dev/null

test_endpoint "Form Slot: outage_form/account_number" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/outage_form/slots" "201" \
    '{"slot_name": "account_number"}' > /dev/null

test_endpoint "Form Slot: outage_form/urgent" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/outage_form/slots" "201" \
    '{"slot_name": "urgent"}' > /dev/null

test_endpoint "Form Mapping: outage_form/account_number" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/outage_form/slots/account_number/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "account_number"}' > /dev/null

test_endpoint "Form Mapping: outage_form/urgent" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/outage_form/slots/urgent/mappings" "201" \
    '{"mapping_type": "from_intent", "intent": "affirm", "value": "true"}' > /dev/null

test_endpoint "Form Slot: registration_form/email" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/registration_form/slots" "201" \
    '{"slot_name": "email"}' > /dev/null

test_endpoint "Form Mapping: registration_form/email" "POST" "/projects/${PROJECT_CODE}/versions/draft/forms/registration_form/slots/email/mappings" "201" \
    '{"mapping_type": "from_entity", "entity_key": "email"}' > /dev/null

# ============================================================
# 19. STORIES (FIXED: Added timeline_index and step_order)
# ============================================================
print_header "📖 19. STORIES"

# Story 1: greet user
STORY1=$(test_endpoint "Create Story (greet user)" "POST" "/projects/${PROJECT_CODE}/versions/draft/stories" "201" \
    '{"name": "greet user"}')
STORY1_ID=$(extract_id "$STORY1")

test_endpoint "Step 1: intent greet" "POST" "/projects/stories/${STORY1_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "greet", "timeline_index": 0, "step_order": 0}' > /dev/null

test_endpoint "Step 2: action utter_greet" "POST" "/projects/stories/${STORY1_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_greet", "timeline_index": 0, "step_order": 1}' > /dev/null

test_endpoint "Step 3: action utter_choose_language" "POST" "/projects/stories/${STORY1_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_choose_language", "timeline_index": 0, "step_order": 2}' > /dev/null

test_endpoint "Step 4: intent select_language" "POST" "/projects/stories/${STORY1_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "select_language", "timeline_index": 1, "step_order": 0}' > /dev/null

test_endpoint "Step 5: action utter_select_service" "POST" "/projects/stories/${STORY1_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_select_service", "timeline_index": 1, "step_order": 1}' > /dev/null

# Story 2: user provides city (with entity)
STORY2=$(test_endpoint "Create Story (user provides city)" "POST" "/projects/${PROJECT_CODE}/versions/draft/stories" "201" \
    '{"name": "user provides city"}')
STORY2_ID=$(extract_id "$STORY2")

STEP2_1=$(test_endpoint "Step: intent inform with city" "POST" "/projects/stories/${STORY2_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "inform", "timeline_index": 0, "step_order": 0, "entities": [{"entity_key": "city", "value": "Delhi"}]}')
STEP2_1_ID=$(extract_id "$STEP2_1")

test_endpoint "Slot event: city" "POST" "/projects/story-steps/${STEP2_1_ID}/slot-events" "201" \
    '{"slot_name": "city", "value": "Delhi"}' > /dev/null

test_endpoint "Step: action utter_confirm_city" "POST" "/projects/stories/${STORY2_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_confirm_city", "timeline_index": 0, "step_order": 1}' > /dev/null

# Story 3: registration flow
STORY3=$(test_endpoint "Create Story (registration flow)" "POST" "/projects/${PROJECT_CODE}/versions/draft/stories" "201" \
    '{"name": "registration flow"}')
STORY3_ID=$(extract_id "$STORY3")

test_endpoint "Step: intent register" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "register", "timeline_index": 0, "step_order": 0}' > /dev/null

test_endpoint "Step: action utter_start_registration" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_start_registration", "timeline_index": 0, "step_order": 1}' > /dev/null

test_endpoint "Step: active_loop registration_form" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "active_loop", "form_name": "registration_form", "timeline_index": 0, "step_order": 2}' > /dev/null

STEP3_4=$(test_endpoint "Step: intent inform with email" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "inform", "timeline_index": 1, "step_order": 0, "entities": [{"entity_key": "email", "value": "test@example.com"}]}')
STEP3_4_ID=$(extract_id "$STEP3_4")

test_endpoint "Slot event: email" "POST" "/projects/story-steps/${STEP3_4_ID}/slot-events" "201" \
    '{"slot_name": "email", "value": "test@example.com"}' > /dev/null

test_endpoint "Step: active_loop null" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "active_loop", "active_loop_value": null, "timeline_index": 1, "step_order": 1}' > /dev/null

test_endpoint "Step: action action_submit_registration" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "action", "action_name": "action_submit_registration", "timeline_index": 1, "step_order": 2}' > /dev/null

test_endpoint "Step: action utter_registration_complete" "POST" "/projects/stories/${STORY3_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_registration_complete", "timeline_index": 1, "step_order": 3}' > /dev/null

# ============================================================
# 20. RULES (FIXED: Added step_order)
# ============================================================
print_header "📜 20. RULES"

# Rule 1: greet rule
RULE1=$(test_endpoint "Create Rule (greet rule)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "greet rule"}')
RULE1_ID=$(extract_id "$RULE1")

test_endpoint "Rule Step: intent greet" "POST" "/projects/rules/${RULE1_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "greet", "step_order": 0}' > /dev/null

test_endpoint "Rule Step: action utter_greet" "POST" "/projects/rules/${RULE1_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_greet", "step_order": 1}' > /dev/null

# Rule 2: registered user greeting (with condition)
RULE2=$(test_endpoint "Create Rule (registered user greeting)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "registered user greeting"}')
RULE2_ID=$(extract_id "$RULE2")

test_endpoint "Rule Condition: user_type = registered" "POST" "/projects/rules/${RULE2_ID}/conditions" "201" \
    '{"condition_type": "slot", "slot_name": "user_type", "slot_value": "registered"}' > /dev/null

test_endpoint "Rule Step: intent greet" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "greet", "step_order": 0}' > /dev/null

test_endpoint "Rule Step: action utter_welcome_back" "POST" "/projects/rules/${RULE2_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_welcome_back", "step_order": 1}' > /dev/null

# Rule 3: activate registration form
RULE3=$(test_endpoint "Create Rule (activate registration form)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "activate registration form"}')
RULE3_ID=$(extract_id "$RULE3")

test_endpoint "Rule Step: intent register" "POST" "/projects/rules/${RULE3_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "register", "step_order": 0}' > /dev/null

test_endpoint "Rule Step: action utter_start_registration" "POST" "/projects/rules/${RULE3_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_start_registration", "step_order": 1}' > /dev/null

test_endpoint "Rule Step: active_loop registration_form" "POST" "/projects/rules/${RULE3_ID}/steps" "201" \
    '{"step_type": "active_loop", "form_name": "registration_form", "step_order": 2}' > /dev/null

# Rule 4: nlu fallback
RULE4=$(test_endpoint "Create Rule (nlu fallback)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "nlu fallback"}')
RULE4_ID=$(extract_id "$RULE4")

test_endpoint "Rule Step: intent nlu_fallback" "POST" "/projects/rules/${RULE4_ID}/steps" "201" \
    '{"step_type": "intent", "intent_name": "nlu_fallback", "step_order": 0}' > /dev/null

test_endpoint "Rule Step: action utter_fallback" "POST" "/projects/rules/${RULE4_ID}/steps" "201" \
    '{"step_type": "action", "response_name": "utter_fallback", "step_order": 1}' > /dev/null

# Rule 5: core fallback
RULE5=$(test_endpoint "Create Rule (core fallback)" "POST" "/projects/${PROJECT_CODE}/versions/draft/rules" "201" \
    '{"name": "core fallback"}')
RULE5_ID=$(extract_id "$RULE5")

test_endpoint "Rule Step: action action_default_fallback" "POST" "/projects/rules/${RULE5_ID}/steps" "201" \
    '{"step_type": "action", "action_name": "action_default_fallback", "step_order": 0}' > /dev/null

# ============================================================
# 21. EXPORT & VALIDATION
# ============================================================
print_header "📤 21. EXPORT & VALIDATION"

test_endpoint "Export NLU (English)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/en" "200" > /dev/null
test_endpoint "Export NLU (Hindi)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/nlu/hi" "200" > /dev/null
test_endpoint "Export Domain" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/domain" "200" > /dev/null
test_endpoint "Export Stories" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/stories" "200" > /dev/null
test_endpoint "Export Rules" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/rules" "200" > /dev/null
test_endpoint "Export All (JSON)" "GET" "/projects/${PROJECT_CODE}/versions/draft/export/all" "200" > /dev/null

# ============================================================
# 22. VERSION PROMOTION
# ============================================================
print_header "🚀 22. VERSION PROMOTION"

test_endpoint "Promote Draft to Locked" "POST" "/projects/${PROJECT_CODE}/promote" "200" > /dev/null
test_endpoint "Export Locked Version (All)" "GET" "/projects/${PROJECT_CODE}/versions/locked/export/all" "200" > /dev/null

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "                        TEST SUMMARY"
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
echo "Download exports:"
echo "  curl -o electricity-bot.zip ${BASE_URL}/projects/${PROJECT_CODE}/versions/locked/export/zip"
echo ""
