"""
Rule YAML Writer

Exports RASA rules.yml format from database models.
Handles all rule components:
- conditions (slot, active_loop)
- steps (intent, action, active_loop, slot)
- entity annotations in intent steps (NEW)
- action steps can reference: custom actions, response utterances, forms
"""

from sqlalchemy.orm import Session, joinedload

from app.models import Rule, RuleCondition, RuleStep, RuleSlotEvent
from app.models.rule import RuleStepEntity


def export_rules_yaml(db: Session, version_id: str) -> dict:
    """
    Export RASA rules.yml structure.

    Returns a dict that can be serialized to YAML.

    Example output:
    ```yaml
    version: "3.1"
    rules:
      - rule: greet user
        steps:
          - intent: greet
          - action: utter_greet

      - rule: user provides email
        steps:
          - intent: inform
            entities:
              - email: user@test.com
          - slot_was_set:
              - email: user@test.com
          - action: utter_email_received

      - rule: activate request form
        steps:
          - intent: request_duplicate_bill
          - action: request_form
          - active_loop: request_form

      - rule: submit request form
        condition:
          - active_loop: request_form
        steps:
          - action: request_form
          - active_loop: null
          - slot_was_set:
              - request_type: duplicate_bill
          - action: utter_submit_request
    ```
    """

    rules_yaml = []

    # Eager load all relationships
    rules = (
        db.query(Rule)
        .options(
            joinedload(Rule.conditions),
            joinedload(Rule.steps).joinedload(RuleStep.intent),
            joinedload(Rule.steps).joinedload(RuleStep.action),
            joinedload(Rule.steps).joinedload(RuleStep.response),
            joinedload(Rule.steps).joinedload(RuleStep.form),
            joinedload(Rule.steps)
            .joinedload(RuleStep.slot_events)
            .joinedload(RuleSlotEvent.slot),
            joinedload(Rule.steps)
            .joinedload(RuleStep.entities)
            .joinedload(RuleStepEntity.entity),
        )
        .filter(Rule.version_id == version_id)
        .order_by(Rule.name)
        .all()
    )

    for rule in rules:
        rule_block = {
            "rule": rule.name,
        }

        # -------------------------------------------------
        # CONDITIONS
        # -------------------------------------------------
        if rule.conditions:
            conditions_yaml = []

            # Sort conditions by order_index
            sorted_conditions = sorted(rule.conditions, key=lambda c: c.order_index)

            for condition in sorted_conditions:
                if condition.condition_type == "active_loop":
                    # active_loop can be null or a form name
                    conditions_yaml.append({"active_loop": condition.active_loop})

                elif condition.condition_type == "slot":
                    if condition.slot_name is not None:
                        # FIXED: Use list format for slot_was_set
                        conditions_yaml.append(
                            {
                                "slot_was_set": [
                                    {condition.slot_name: condition.slot_value}
                                ]
                            }
                        )

            if conditions_yaml:
                rule_block["condition"] = conditions_yaml

        # -------------------------------------------------
        # STEPS
        # -------------------------------------------------
        steps_yaml = []

        # Sort steps by step_order
        sorted_steps = sorted(rule.steps, key=lambda s: s.step_order)

        for step in sorted_steps:
            # -------------------------
            # INTENT (with entities - NEW)
            # -------------------------
            if step.step_type == "intent" and step.intent:
                intent_block = {"intent": step.intent.intent_name}

                # Add entity annotations if present (NEW)
                if step.entities:
                    entities_list = []
                    for e in step.entities:
                        if e.value is not None:
                            entity_entry = {e.entity.entity_key: e.value}
                        else:
                            entity_entry = e.entity.entity_key
                        entities_list.append(entity_entry)

                    if entities_list:
                        intent_block["entities"] = entities_list

                steps_yaml.append(intent_block)

            # -------------------------
            # ACTION (custom action, response utterance, or form)
            # -------------------------
            elif step.step_type == "action":
                # Priority: action > response > form
                if step.action:
                    steps_yaml.append({"action": step.action.name})
                elif step.response:
                    steps_yaml.append({"action": step.response.name})
                elif step.form:
                    steps_yaml.append({"action": step.form.name})

            # -------------------------
            # ACTIVE LOOP
            # -------------------------
            elif step.step_type == "active_loop":
                # active_loop can be null (to deactivate) or a form name
                steps_yaml.append({"active_loop": step.active_loop_value})

            # -------------------------
            # SLOT EVENT
            # -------------------------
            elif step.step_type == "slot":
                # FIXED: Use list format for slot_was_set
                slot_list = []
                for event in step.slot_events:
                    if event.slot:
                        slot_list.append({event.slot.name: event.value})

                if slot_list:
                    steps_yaml.append({"slot_was_set": slot_list})

        # Only add rule if it has steps (Rasa requirement)
        if steps_yaml:
            rule_block["steps"] = steps_yaml
            rules_yaml.append(rule_block)

    return {
        "version": "3.1",
        "rules": rules_yaml,
    }
