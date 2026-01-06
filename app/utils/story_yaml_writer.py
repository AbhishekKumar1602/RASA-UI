"""
Story YAML Writer

Exports RASA stories.yml format from database models.
Handles all story step types:
- intent (with entity annotations - NEW)
- action (custom actions, response utterances, forms)
- slot (slot_was_set events)
- active_loop
- checkpoint
- or (OR conditions for multiple intents - NEW)
"""

from sqlalchemy.orm import Session, joinedload
from collections import defaultdict

from app.models import Story, StoryStep, StorySlotEvent
from app.models.story import StoryStepEntity


def export_stories_yaml(db: Session, version_id: str) -> dict:
    """
    Export RASA stories.yml structure.

    Returns a dict that can be serialized to YAML.

    Example output:
    ```yaml
    version: "3.1"
    stories:
      - story: greet and request
        steps:
          - intent: greet
          - action: utter_greet
          - intent: inform
            entities:
              - city: Delhi
          - slot_was_set:
              - city: Delhi
          - or:
              - intent: affirm
              - intent: deny
          - action: utter_acknowledge
    ```
    """

    stories_yaml = []

    # Eager load all relationships
    stories = (
        db.query(Story)
        .options(
            joinedload(Story.steps).joinedload(StoryStep.intent),
            joinedload(Story.steps).joinedload(StoryStep.action),
            joinedload(Story.steps).joinedload(StoryStep.response),
            joinedload(Story.steps).joinedload(StoryStep.form),
            joinedload(Story.steps)
            .joinedload(StoryStep.slot_events)
            .joinedload(StorySlotEvent.slot),
            joinedload(Story.steps)
            .joinedload(StoryStep.entities)
            .joinedload(StoryStepEntity.entity),
        )
        .filter(Story.version_id == version_id)
        .order_by(Story.name)
        .all()
    )

    for story in stories:
        steps_yaml = []

        # Sort steps by timeline_index then step_order
        sorted_steps = sorted(
            story.steps, key=lambda s: (s.timeline_index, s.step_order)
        )

        # Group OR steps by or_group_id
        or_groups = defaultdict(list)
        processed_or_groups = set()

        for step in sorted_steps:
            if step.or_group_id:
                or_groups[step.or_group_id].append(step)

        for step in sorted_steps:
            # -------------------------
            # OR CONDITION (NEW)
            # -------------------------
            if step.step_type == "or" or step.or_group_id:
                if step.or_group_id and step.or_group_id not in processed_or_groups:
                    # Process the OR group
                    or_steps = or_groups[step.or_group_id]
                    or_block = []
                    for or_step in or_steps:
                        if or_step.intent:
                            intent_block = {"intent": or_step.intent.intent_name}
                            # Add entity annotations if present
                            if or_step.entities:
                                entities_list = []
                                for e in or_step.entities:
                                    if e.value is not None:
                                        entities_list.append(
                                            {e.entity.entity_key: e.value}
                                        )
                                    else:
                                        entities_list.append(e.entity.entity_key)
                                if entities_list:
                                    intent_block["entities"] = entities_list
                            or_block.append(intent_block)

                    if or_block:
                        steps_yaml.append({"or": or_block})
                    processed_or_groups.add(step.or_group_id)
                continue

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
                slot_list = []
                for event in step.slot_events:
                    if event.slot:
                        slot_list.append({event.slot.name: event.value})

                if slot_list:
                    steps_yaml.append({"slot_was_set": slot_list})

            # -------------------------
            # CHECKPOINT
            # -------------------------
            elif step.step_type == "checkpoint":
                if step.checkpoint_name:
                    steps_yaml.append({"checkpoint": step.checkpoint_name})

        # Rasa requires at least one step
        if steps_yaml:
            stories_yaml.append(
                {
                    "story": story.name,
                    "steps": steps_yaml,
                }
            )

    return {
        "version": "3.1",
        "stories": stories_yaml,
    }
