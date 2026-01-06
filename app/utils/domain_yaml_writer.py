from sqlalchemy.orm import Session, joinedload

from app.models import (
    Intent,
    Entity,
    EntityRole,
    EntityGroup,
    Slot,
    SlotMapping,
    Form,
    FormRequiredSlot,
    FormSlotMapping,
    Response,
    ResponseVariant,
    ResponseCondition,
    ResponseComponent,
    Action,
    SessionConfig,
)


def export_domain_yaml(db: Session, version_id: str) -> dict:
    """
    Export complete RASA domain.yml structure.

    Returns a dict that can be serialized to YAML.
    """

    domain = {
        "version": "3.1",
        "intents": [],
        "entities": [],
        "slots": {},
        "forms": {},
        "responses": {},
        "actions": [],
    }

    # =========================================================
    # SESSION CONFIG
    # =========================================================
    session_config = (
        db.query(SessionConfig).filter(SessionConfig.version_id == version_id).first()
    )

    if session_config:
        domain["session_config"] = {
            "session_expiration_time": session_config.session_expiration_time,
            "carry_over_slots_to_new_session": session_config.carry_over_slots_to_new_session,
        }

    # =========================================================
    # INTENTS
    # =========================================================
    intents = (
        db.query(Intent)
        .filter(Intent.version_id == version_id)
        .order_by(Intent.intent_name)
        .all()
    )
    domain["intents"] = [i.intent_name for i in intents]

    # =========================================================
    # ENTITIES (with roles and groups)
    # =========================================================
    entities = (
        db.query(Entity)
        .options(
            joinedload(Entity.roles),
            joinedload(Entity.groups),
        )
        .filter(Entity.version_id == version_id)
        .order_by(Entity.entity_key)
        .all()
    )

    for entity in entities:
        roles = [r.role for r in entity.roles]
        groups = [g.group_name for g in entity.groups]

        if roles or groups:
            entity_def = {}
            if roles:
                entity_def["roles"] = roles
            if groups:
                entity_def["groups"] = groups

            domain["entities"].append({entity.entity_key: entity_def})
        else:
            domain["entities"].append(entity.entity_key)

    # =========================================================
    # SLOTS (with mappings, conditions, and values)
    # =========================================================
    slots = (
        db.query(Slot)
        .options(
            joinedload(Slot.mappings).joinedload(SlotMapping.entity),
        )
        .filter(Slot.version_id == version_id)
        .order_by(Slot.name)
        .all()
    )

    for slot in slots:
        slot_def = {
            "type": slot.slot_type,
            "influence_conversation": slot.influence_conversation,
        }

        if slot.initial_value is not None:
            slot_def["initial_value"] = slot.initial_value

        if slot.values:
            slot_def["values"] = slot.values

        if slot.slot_type == "float":
            if slot.min_value is not None:
                slot_def["min_value"] = slot.min_value
            if slot.max_value is not None:
                slot_def["max_value"] = slot.max_value

        # Build mappings
        mappings = []
        sorted_mappings = sorted(slot.mappings, key=lambda m: m.priority, reverse=True)

        for m in sorted_mappings:
            mapping = {"type": m.mapping_type}

            # Entity reference
            if m.entity_id and m.entity:
                mapping["entity"] = m.entity.entity_key

            # Entity role and group
            if m.role:
                mapping["role"] = m.role
            if m.group:
                mapping["group"] = m.group

            # Intent filters
            if m.intent:
                mapping["intent"] = m.intent
            if m.not_intent:
                mapping["not_intent"] = m.not_intent

            # Value for from_intent mapping (NEW)
            if m.value:
                mapping["value"] = m.value

            # Conditions - prefer new conditions field, fall back to legacy active_loop
            if m.conditions:
                # New format: array of condition objects
                mapping["conditions"] = m.conditions
            elif m.active_loop:
                # Legacy format: single active_loop
                mapping["conditions"] = [{"active_loop": m.active_loop}]

            mappings.append(mapping)

        if mappings:
            slot_def["mappings"] = mappings

        domain["slots"][slot.name] = slot_def

    # =========================================================
    # FORMS (with required slots, mappings, and values)
    # =========================================================
    forms = (
        db.query(Form)
        .options(
            joinedload(Form.required_slots).joinedload(FormRequiredSlot.slot),
            joinedload(Form.required_slots)
            .joinedload(FormRequiredSlot.mappings)
            .joinedload(FormSlotMapping.entity),
        )
        .filter(Form.version_id == version_id)
        .order_by(Form.name)
        .all()
    )

    for form in forms:
        form_def = {}

        if form.ignored_intents:
            form_def["ignored_intents"] = form.ignored_intents

        required_slots = {}

        sorted_frs = sorted(form.required_slots, key=lambda frs: frs.order)

        for frs in sorted_frs:
            mappings = []

            for m in frs.mappings:
                mapping = {"type": m.mapping_type}

                # Entity reference
                if m.entity_id and m.entity:
                    mapping["entity"] = m.entity.entity_key

                # Intent filters
                if m.intent:
                    mapping["intent"] = m.intent
                if m.not_intent:
                    mapping["not_intent"] = m.not_intent

                # Value for from_intent mapping (NEW)
                if m.value:
                    mapping["value"] = m.value

                mappings.append(mapping)

            required_slots[frs.slot.name] = mappings

        form_def["required_slots"] = required_slots
        domain["forms"][form.name] = form_def

    # =========================================================
    # RESPONSES (with variants, conditions, and components)
    # =========================================================
    responses = (
        db.query(Response)
        .options(
            joinedload(Response.variants).joinedload(ResponseVariant.conditions),
            joinedload(Response.variants).joinedload(ResponseVariant.components),
            joinedload(Response.variants).joinedload(ResponseVariant.language),
        )
        .filter(Response.version_id == version_id)
        .order_by(Response.name)
        .all()
    )

    for response in responses:
        variants_yaml = []

        sorted_variants = sorted(
            response.variants, key=lambda v: v.priority, reverse=True
        )

        for variant in sorted_variants:
            variant_def = {}

            # Conditions
            if variant.conditions:
                sorted_conditions = sorted(
                    variant.conditions, key=lambda c: c.order_index
                )
                condition_list = []

                for cond in sorted_conditions:
                    if cond.condition_type == "slot":
                        condition_list.append(
                            {
                                "type": "slot",
                                "name": cond.slot_name,
                                "value": cond.slot_value,
                            }
                        )
                    elif cond.condition_type == "active_loop":
                        condition_list.append(
                            {
                                "type": "active_loop",
                                "name": cond.slot_name,
                            }
                        )

                if condition_list:
                    variant_def["condition"] = condition_list

            # Components
            sorted_components = sorted(variant.components, key=lambda c: c.order_index)

            for comp in sorted_components:
                if comp.component_type == "text":
                    if isinstance(comp.payload, str):
                        variant_def["text"] = comp.payload
                    elif isinstance(comp.payload, dict) and "text" in comp.payload:
                        variant_def["text"] = comp.payload["text"]
                    else:
                        variant_def["text"] = str(comp.payload) if comp.payload else ""

                elif comp.component_type == "buttons":
                    if isinstance(comp.payload, list):
                        variant_def["buttons"] = comp.payload
                    elif isinstance(comp.payload, dict) and "buttons" in comp.payload:
                        variant_def["buttons"] = comp.payload["buttons"]

                elif comp.component_type == "image":
                    if isinstance(comp.payload, str):
                        variant_def["image"] = comp.payload
                    elif isinstance(comp.payload, dict) and "url" in comp.payload:
                        variant_def["image"] = comp.payload["url"]

                elif comp.component_type == "attachment":
                    if isinstance(comp.payload, dict):
                        variant_def["attachment"] = comp.payload

                elif comp.component_type == "custom":
                    if isinstance(comp.payload, dict):
                        variant_def["custom"] = comp.payload

            if variant_def:
                variants_yaml.append(variant_def)

        domain["responses"][response.name] = variants_yaml if variants_yaml else []

    # =========================================================
    # ACTIONS
    # =========================================================
    actions = (
        db.query(Action)
        .filter(Action.version_id == version_id)
        .order_by(Action.name)
        .all()
    )

    # Only include custom actions, not utterances (those are in responses)
    domain["actions"] = [a.name for a in actions]

    # =========================================================
    # CLEAN UP EMPTY SECTIONS
    # =========================================================
    if not domain["intents"]:
        del domain["intents"]
    if not domain["entities"]:
        del domain["entities"]
    if not domain["slots"]:
        del domain["slots"]
    if not domain["forms"]:
        del domain["forms"]
    if not domain["responses"]:
        del domain["responses"]
    if not domain["actions"]:
        del domain["actions"]

    return domain
