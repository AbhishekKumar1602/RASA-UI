uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

alembic revision --autogenerate -m "initial_schema"

alembic upgrade head

for f in *.py; do   echo "===== $f =====";   cat "$f";   echo; done > file.txt

psql postgresql://rasa_test_a:Test1234@127.0.0.1:5432/rasa_test_a


DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    )
    LOOP
        EXECUTE format(
            'DROP TABLE IF EXISTS public.%I CASCADE',
            r.tablename
        );
    END LOOP;
END $$;



# Complete Bot Version Lifecycle Flow Diagram

## Multi-Language Chatbot Management System

### 1. High-Level Version Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           VERSION LIFECYCLE OVERVIEW                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌──────────┐      PROMOTE       ┌──────────┐      PROMOTE      ┌──────────┐  │
│    │  DRAFT   │ ─────────────────▶ │  LOCKED  │ ────────────────▶ │ ARCHIVED │  │
│    │  (v1.0)  │                    │  (v1.0)  │                   │  (v1.0)  │  │
│    └──────────┘                    └──────────┘                   └──────────┘  │
│         │                               │                              │        │
│         │ Editable                      │ Read-only                    │ Backup │
│         │ Work in progress              │ Production-ready             │ History│
│         │                               │                              │        │
│         │                               │         ROLLBACK             │        │
│         │                               │ ◀────────────────────────────┤        │
│         │                               │      (on error)              │        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Complete Project Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: PROJECT INITIALIZATION                         │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    START
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │   POST /projects            │
                        │   {                         │
                        │     "project_code": "ELEC", │
                        │     "project_name": "Elec"  │
                        │   }                         │
                        └─────────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │      Project Created        │
                        │      Draft Version v1.0     │
                        │      Auto-Created           │
                        └─────────────────────────────┘
                                      │
                                      ▼
            ┌─────────────────────────────────────────────────────┐
            │              ADD LANGUAGES TO PROJECT               │
            └─────────────────────────────────────────────────────┘
                      │                           │
                      ▼                           ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │ POST /projects/ELEC/ │    │ POST /projects/ELEC/ │
        │   languages          │    │   languages          │
        │ {"language_code":    │    │ {"language_code":    │
        │   "en"}              │    │   "hi"}              │
        └──────────────────────┘    └──────────────────────┘
                      │                           │
                      └─────────────┬─────────────┘
                                    ▼
            ┌─────────────────────────────────────────────────────┐
            │         ADD LANGUAGES TO DRAFT VERSION              │
            └─────────────────────────────────────────────────────┘
                      │                           │
                      ▼                           ▼
        ┌──────────────────────┐    ┌──────────────────────┐
        │ POST /projects/ELEC/ │    │ POST /projects/ELEC/ │
        │ versions/draft/      │    │ versions/draft/      │
        │   languages          │    │   languages          │
        │ {"language_code":    │    │ {"language_code":    │
        │   "en"}              │    │   "hi"}              │
        └──────────────────────┘    └──────────────────────┘
                      │                           │
                      └─────────────┬─────────────┘
                                    ▼
                        ┌─────────────────────────┐
                        │    Project Ready for    │
                        │     NLU Configuration   │
                        └─────────────────────────┘
                                    │
                                    ▼
                              GO TO PHASE 2
```

### 3. NLU Component Configuration Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 2: NLU COMPONENT CONFIGURATION                       │
│                           (All operations on DRAFT)                             │
└─────────────────────────────────────────────────────────────────────────────────┘

                           FROM PHASE 1
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │   INTENTS   │   │  ENTITIES   │   │    SLOTS    │   │    FORMS    │        │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘        │
│        │                 │                 │                 │                │
│        ▼                 ▼                 ▼                 ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │ POST        │   │ POST        │   │ POST        │   │ POST        │        │
│  │ /intents    │   │ /entities   │   │ /slots      │   │ /forms      │        │
│  │             │   │             │   │             │   │             │        │
│  │ - greet     │   │ - account_  │   │ - account_  │   │ - request_  │        │
│  │ - goodbye   │   │   number    │   │   number    │   │   form      │        │
│  │ - affirm    │   │ - mobile_   │   │ - request_  │   │ - outage_   │        │
│  │ - deny      │   │   number    │   │   type      │   │   form      │        │
│  │ - request_  │   │ - amount    │   │ - language  │   │             │        │
│  │   duplicate │   │ - request_  │   │ - urgent    │   │             │        │
│  │   _bill     │   │   type      │   │             │   │             │        │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘        │
│        │                 │                 │                 │                │
│        │                 │                 │                 │                │
│        ▼                 ▼                 ▼                 ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │ Add Examples│   │ Add Roles/  │   │ Add Slot    │   │ Add Required│        │
│  │ per Language│   │ Groups      │   │ Mappings    │   │ Slots +     │        │
│  │             │   │             │   │             │   │ Mappings    │        │
│  │ POST        │   │ POST        │   │ POST        │   │ POST        │        │
│  │ /intents/   │   │ /entities/  │   │ /slots/     │   │ /forms/     │        │
│  │ {id}/       │   │ {key}/      │   │ {name}/     │   │ {name}/     │        │
│  │ examples    │   │ regexes     │   │ mappings    │   │ required-   │        │
│  │             │   │ lookups     │   │             │   │ slots       │        │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘        │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │  RESPONSES  │   │   ACTIONS   │   │   STORIES   │   │    RULES    │        │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘        │
│        │                 │                 │                 │                │
│        ▼                 ▼                 ▼                 ▼                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐        │
│  │ POST        │   │ POST        │   │ POST        │   │ POST        │        │
│  │ /responses  │   │ /actions    │   │ /stories    │   │ /rules      │        │
│  │             │   │             │   │             │   │             │        │
│  │ - utter_    │   │ - action_   │   │ - greet_    │   │ - greet_    │        │
│  │   greet     │   │   save_     │   │   user      │   │   rule      │        │
│  │ - utter_    │   │   request   │   │ - request_  │   │ - form_     │        │
│  │   goodbye   │   │ - action_   │   │   flow      │   │   activate  │        │
│  │ - utter_    │   │   check_    │   │ - form_     │   │ - fallback  │        │
│  │   fallback  │   │   payment   │   │   happy_    │   │   _rule     │        │
│  │             │   │             │   │   path      │   │             │        │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘        │
│        │                 │                 │                 │                │
│        ▼                 ▼                 ▼                 ▼                │
│  ┌─────────────┐                    ┌─────────────┐   ┌─────────────┐         │
│  │ Add Variants│                    │ Add Steps   │   │ Add         │         │
│  │ Conditions  │                    │ + Entities  │   │ Conditions  │         │
│  │ Components  │                    │ + OR Groups │   │ + Steps     │         │
│  │             │                    │ + Slots     │   │             │         │
│  └─────────────┘                    └─────────────┘   └─────────────┘         │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│                         ADDITIONAL NLU FEATURES                               │
│                                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                          │
│  │   REGEXES   │   │   LOOKUPS   │   │  SYNONYMS   │                          │
│  └─────────────┘   └─────────────┘   └─────────────┘                          │
│        │                 │                 │                                  │
│        ▼                 ▼                 ▼                                  │
│  POST /regexes     POST /lookups     POST /synonyms                           │
│  - account_number  - request_type    - duplicate_bill                         │
│  - mobile_number   - complaint_type  - power_outage                           │
│                                                                               │
└───────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │   DRAFT v1.0  │
                        │   COMPLETE    │
                        └───────────────┘
                                │
                                ▼
                          GO TO PHASE 3
```


### 4. Version Promotion & Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 3: VERSION PROMOTION LIFECYCLE                       │
└─────────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
                              INITIAL STATE
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           PROJECT: ELEC                                 │
    │  ┌───────────────┐                                                      │
    │  │   DRAFT v1.0  │  ◀── Only this version exists                        │
    │  │   (Editable)  │                                                      │
    │  └───────────────┘                                                      │
    └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /projects/ELEC/versions/draft/promote
                                    │ (Validate → Lock)
                                    ▼
═══════════════════════════════════════════════════════════════════════════════════
                         AFTER FIRST PROMOTION
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           PROJECT: ELEC                                 │
    │                                                                         │
    │  ┌───────────────┐         ┌───────────────┐                            │
    │  │  LOCKED v1.0  │         │   (No Draft)  │                            │
    │  │  (Read-only)  │         │               │                            │
    │  │  Production   │         │               │                            │
    │  └───────────────┘         └───────────────┘                            │
    │         │                                                               │
    │         │     Export available:                                         │
    │         │     GET /projects/ELEC/versions/locked/export/zip             │
    │         │                                                               │
    └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /projects/ELEC/versions/locked/create-draft
                                    │ (Clone locked → new draft)
                                    ▼
═══════════════════════════════════════════════════════════════════════════════════
                      AFTER CREATING NEW DRAFT FROM LOCKED
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           PROJECT: ELEC                                 │
    │                                                                         │
    │  ┌───────────────┐         ┌───────────────┐                            │
    │  │  LOCKED v1.0  │         │   DRAFT v2.0  │  ◀── Cloned from v1.0      │
    │  │  (Read-only)  │         │   (Editable)  │                            │
    │  │  Production   │         │   Work in     │                            │
    │  │               │         │   Progress    │                            │
    │  └───────────────┘         └───────────────┘                            │
    │                                    │                                    │
    │                                    │ Make changes:                      │
    │                                    │ - Add new intents                  │
    │                                    │ - Update responses                 │
    │                                    │ - Add new stories                  │
    │                                    ▼                                    │
    └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /projects/ELEC/versions/draft/promote
                                    │ (Validate → Lock draft → Archive old locked)
                                    ▼
═══════════════════════════════════════════════════════════════════════════════════
                       AFTER SECOND PROMOTION (v2.0)
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                           PROJECT: ELEC                                 │
    │                                                                         │
    │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐              │
    │  │ ARCHIVED v1.0 │   │  LOCKED v2.0  │   │   (No Draft)  │              │
    │  │   (Backup)    │   │  (Read-only)  │   │               │              │
    │  │   History     │   │  Production   │   │               │              │
    │  └───────────────┘   └───────────────┘   └───────────────┘              │
    │         │                   │                                           │
    │         │                   │     New production version                │
    │         │                   │                                           │
    │         │   ROLLBACK        │                                           │
    │         │◀──────────────────│  POST /projects/ELEC/versions/rollback    │
    │         │   (on error)      │  (If v2.0 has issues)                     │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Continue development cycle)
                                    ▼
═══════════════════════════════════════════════════════════════════════════════════
                            ROLLBACK SCENARIO
═══════════════════════════════════════════════════════════════════════════════════

    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      BEFORE ROLLBACK (Error in v2.0)                    │
    │                                                                         │
    │  ┌───────────────┐   ┌───────────────┐                                  │
    │  │ ARCHIVED v1.0 │   │  LOCKED v2.0  │  ◀── Has bugs/issues             │
    │  │   (Backup)    │   │  (Read-only)  │                                  │
    │  └───────────────┘   └───────────────┘                                  │
    │                                                                         │
    └─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /projects/ELEC/versions/rollback
                                    ▼
    ┌─────────────────────────────────────────────────────────────────────────┐
    │                      AFTER ROLLBACK                                     │
    │                                                                         │
    │  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐              │
    │  │ ARCHIVED v2.0 │   │  LOCKED v1.0  │   │   (No Draft)  │              │
    │  │   (Failed)    │   │  (Restored)   │   │               │              │
    │  │               │   │  Production   │   │               │              │
    │  └───────────────┘   └───────────────┘   └───────────────┘              │
    │         │                   │                                           │
    │         │                   │     v1.0 is now production again          │
    │         │                   │                                           │
    └─────────────────────────────────────────────────────────────────────────┘
```

### 5. Complete State Machine Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         VERSION STATE MACHINE                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   CREATE    │
                              │   PROJECT   │
                              └──────┬──────┘
                                     │
                                     │ Auto-create
                                     ▼
                    ┌────────────────────────────────────┐
                    │                                    │
                    │             DRAFT                  │
                    │                                    │
                    │  • Editable                        │
                    │  • One per project                 │
                    │  • Add/Update/Delete all NLU       │
                    │                                    │
                    └────────────────┬───────────────────┘
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                    validate()            clone_from_locked()
                          │                     │
                          ▼                     │
                    ┌───────────┐               │
                    │ VALIDATE  │               │
                    │  • Min 10 examples/intent │
                    │  • All slots have mappings│
                    │  • Forms have req slots   │
                    └─────┬─────┘               │
                          │                     │
                   ┌──────┴──────┐              │
                   │             │              │
               SUCCESS        FAIL              │
                   │             │              │
                   ▼             ▼              │
             promote()     return errors        │
                   │                            │
                   ▼                            │
    ┌────────────────────────────────────┐      │
    │                                    │      │
    │             LOCKED                 │◀──-──┘
    │                                    │
    │  • Read-only                       │
    │  • One per project                 │
    │  • Production-ready                │
    │  • Exportable to RASA              │
    │                                    │
    └────────────────┬───────────────────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
    create_draft() promote()  rollback()
          │          │          │
          │          ▼          │
          │    (Archives        │
          │     current         │
          │     locked)         │
          │          │          │
          │          ▼          │
          │  ┌────────────────────────────────────┐
          │  │                                    │
          │  │           ARCHIVED                 │◀─────┐
          │  │                                    │      │
          │  │  • Read-only                       │      │
          │  │  • Multiple per project (history)  │      │
          │  │  • Backup/Audit trail              │      │
          │  │  • Can be restored via rollback    │      │
          │  │                                    │      │
          │  └────────────────┬───────────────────┘      │
          │                   │                          │
          │              rollback()                      │
          │                   │                          │
          │                   ▼                          │
          │           (Swap with locked)                 │
          │                   │                          │
          └───────────────────┴──────────────────────────┘
```

### 6. API Endpoints for Version Management

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      VERSION MANAGEMENT API ENDPOINTS                           │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│ ACTION                    │ METHOD │ ENDPOINT                                   │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Create Project            │ POST   │ /projects                                  │
│ (auto-creates draft)      │        │ Body: {project_code, project_name}         │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Add Language to Project   │ POST   │ /projects/{code}/languages                 │
│                           │        │ Body: {language_code}                      │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Add Language to Draft     │ POST   │ /projects/{code}/versions/draft/languages  │
│                           │        │ Body: {language_code}                      │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ List Versions             │ GET    │ /projects/{code}/versions                  │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Validate Draft            │ POST   │ /projects/{code}/versions/draft/validate   │
│                           │        │ Returns: validation errors or success      │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Promote Draft → Locked    │ POST   │ /projects/{code}/versions/draft/promote    │
│ (archives old locked)     │        │ Returns: new locked version                │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Create Draft from Locked  │ POST   │ /projects/{code}/versions/locked/clone     │
│                           │        │ Returns: new draft version                 │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Rollback to Archive       │ POST   │ /projects/{code}/versions/rollback         │
│                           │        │ Body: {archive_version_id}                 │
│                           │        │ Returns: restored locked version           │
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ Export Locked Version     │ GET    │ /projects/{code}/versions/locked/export/zip│
├───────────────────────────┼────────┼────────────────────────────────────────────┤
│ List Archived Versions    │ GET    │ /projects/{code}/versions/archived         │
└───────────────────────────┴────────┴────────────────────────────────────────────┘
```

### 7. Complete Lifecycle Timeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE LIFECYCLE TIMELINE                          │
└─────────────────────────────────────────────────────────────────────────────┘

TIME ─────────────────────────────────────────────────────────────────────────▶

     DAY 1              DAY 2-30            DAY 31           DAY 32-60
       │                   │                   │                 │
       ▼                   ▼                   ▼                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CREATE    │    │  CONFIGURE  │    │   PROMOTE   │    │   CREATE    │
│   PROJECT   │───▶│    DRAFT    │───▶│  DRAFT TO   │───▶│  NEW DRAFT  │
│             │    │    v1.0     │    │   LOCKED    │    │    v2.0     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                                    ┌─────────────┐
                                    │  EXPORT &   │
                                    │   DEPLOY    │
                                    │  TO RASA    │
                                    └─────────────┘

     DAY 61             DAY 62             DAY 63             DAY 64+
       │                   │                   │                  │
       ▼                   ▼                   ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PROMOTE   │    │  DISCOVER   │    │  ROLLBACK   │    │  FIX & RE-  │
│  DRAFT v2.0 │───▶│    BUG IN   │───▶│  TO v1.0    │───▶│   PROMOTE   │
│  TO LOCKED  │    │    v2.0     │    │  (ARCHIVE   │    │    v2.1     │
│             │    │             │    │   v2.0)     │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐
│  v1.0 MOVES │
│ TO ARCHIVED │
└─────────────┘


══════════════════════════════════════════════════════════════════════════════
                     VERSION HISTORY AFTER DAY 64+
══════════════════════════════════════════════════════════════════════════════

    PROJECT: ELEC
    ├── DRAFT v2.1 (current working version)
    ├── LOCKED v1.0 (production - restored)
    └── ARCHIVED
        ├── v2.0 (failed - rolled back)
        └── (older versions...)
```

### 8. Database State Transitions

```
┌────────────────────────────────────────────────────────────────────────────┐
│                    DATABASE STATE AT EACH PHASE                            │
└────────────────────────────────────────────────────────────────────────────┘


PHASE 1: After Project Creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ projects                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_code │ project_name          │ created_at             │
│ uuid-001    │ ELEC         │ Electricity Chatbot   │ 2026-01-04             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ versions                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_id │ version_label │ status  │ parent_version_id      │
│ ver-001     │ uuid-001   │ v1.0          │ draft   │ NULL                   │
└─────────────────────────────────────────────────────────────────────────────┘


PHASE 2: After First Promotion (Draft → Locked)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ versions                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_id │ version_label │ status  │ parent_version_id      │
│ ver-001     │ uuid-001   │ v1.0          │ locked  │ NULL                   │ ◀── Changed
└─────────────────────────────────────────────────────────────────────────────┘


PHASE 3: After Creating Draft from Locked
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ versions                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_id │ version_label │ status  │ parent_version_id      │
│ ver-001     │ uuid-001   │ v1.0          │ locked  │ NULL                   │
│ ver-002     │ uuid-001   │ v2.0          │ draft   │ ver-001                │ ◀── NEW (cloned)
└─────────────────────────────────────────────────────────────────────────────┘


PHASE 4: After Second Promotion
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ versions                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_id │ version_label │ status   │ parent_version_id     │
│ ver-001     │ uuid-001   │ v1.0          │ archived │ NULL                  │ ◀── Archived
│ ver-002     │ uuid-001   │ v2.0          │ locked   │ ver-001               │ ◀── Now locked
└─────────────────────────────────────────────────────────────────────────────┘


PHASE 5: After Rollback (Error Recovery)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────────────┐
│ versions                                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ id          │ project_id │ version_label │ status   │ parent_version_id     │
│ ver-001     │ uuid-001   │ v1.0          │ locked   │ NULL                  │ ◀── Restored
│ ver-002     │ uuid-001   │ v2.0          │ archived │ ver-001               │ ◀── Now archived
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9. Error Handling & Validation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    VALIDATION & ERROR HANDLING FLOW                         │
└─────────────────────────────────────────────────────────────────────────────┘

                        ┌─────────────────────┐
                        │  REQUEST: PROMOTE   │
                        │  DRAFT → LOCKED     │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   VALIDATE DRAFT    │
                        └──────────┬──────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Check Intents   │      │ Check Slots     │      │ Check Forms     │
│                 │      │                 │      │                 │
│ • Min 10        │      │ • Has mappings  │      │ • Has required  │
│   examples      │      │ • Valid types   │      │   slots         │
│ • Valid names   │      │                 │      │ • Valid refs    │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                        ┌─────────┴──────────┐
                        │                    │
                   ALL PASS              ANY FAIL
                        │                    │
                        ▼                    ▼
              ┌─────────────────┐  ┌─────────────────────────┐
              │    PROMOTE      │  │   RETURN ERRORS         │
              │                 │  │                         │
              │ 1. Archive old  │  │ {                       │
              │    locked       │  │   "errors": [           │
              │ 2. Change draft │  │     {                   │
              │    to locked    │  │       "type": "intent", │
              │                 │  │       "name": "greet",  │
              │                 │  │       "message": "Only  │
              │                 │  │         5 examples,     │
              │                 │  │         need 10"        │
              │                 │  │     }                   │
              │                 │  │   ]                     │
              │                 │  │ }                       │
              └─────────────────┘  └─────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │    SUCCESS      │
              │                 │
              │ {               │
              │   "version":    │
              │     "v1.0",     │
              │   "status":     │
              │     "locked"    │
              │ }               │
              └─────────────────┘
```

### 10. Summary: Single Page Reference

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    QUICK REFERENCE: VERSION LIFECYCLE                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   STATUS      │ ALLOWED OPERATIONS           │ COUNT PER PROJECT                │
│   ────────────┼──────────────────────────────┼────────────────────────────────  │
│   DRAFT       │ Create, Read, Update, Delete │ 0 or 1                           │
│   LOCKED      │ Read, Export, Clone          │ 0 or 1                           │
│   ARCHIVED    │ Read, Restore (rollback)     │ 0 to many                        │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   TRANSITION          │ FROM     │ TO       │ SIDE EFFECTS                      │
│   ────────────────────┼──────────┼──────────┼────────────────────────────────── │
│   promote             │ draft    │ locked   │ Old locked → archived             │
│   clone               │ locked   │ draft    │ Creates new draft                 │
│   rollback            │ archived │ locked   │ Current locked → archived         │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   RULE: Only ONE draft and ONE locked version can exist at any time             │
│   RULE: Archived versions are historical backups for audit/rollback             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

*Document Version: 1.0 | Created: January 2026*
