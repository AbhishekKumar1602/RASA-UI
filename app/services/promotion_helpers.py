from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
from app.models import (
    VersionLanguage,
    SessionConfig,
    Entity,
    EntityRole,
    EntityGroup,
    Intent,
    IntentLocalization,
    IntentExample,
    Slot,
    SlotMapping,
    Form,
    FormRequiredSlot,
    FormSlotMapping,
    Action,
    Response,
    ResponseVariant,
    ResponseCondition,
    ResponseComponent,
    Story,
    StoryStep,
    StorySlotEvent,
    Rule,
    RuleStep,
    RuleSlotEvent,
    RuleCondition,
    Regex,
    RegexExample,
    Lookup,
    LookupExample,
    Synonym,
    SynonymExample,
    StoryStepEntity,
    RuleStepEntity,
)


def delete_version_data(db: Session, version_id: str):


    # ================================================================
    # PHASE 1: Delete rule step children first
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM rule_step_entities
        WHERE rule_step_id IN (
            SELECT rs.id
            FROM rule_steps rs
            JOIN rules r ON r.id = rs.rule_id
            WHERE r.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM rule_slot_events
        WHERE rule_step_id IN (
            SELECT rs.id
            FROM rule_steps rs
            JOIN rules r ON r.id = rs.rule_id
            WHERE r.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 2: Delete story step children
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM story_step_entities
        WHERE story_step_id IN (
            SELECT ss.id
            FROM story_steps ss
            JOIN stories s ON s.id = ss.story_id
            WHERE s.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM story_slot_events
        WHERE story_step_id IN (
            SELECT ss.id
            FROM story_steps ss
            JOIN stories s ON s.id = ss.story_id
            WHERE s.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 3: Delete steps (these have FK to responses/actions/forms/intents)
    # MUST be deleted BEFORE responses, actions, forms, intents
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM rule_steps
        WHERE rule_id IN (
            SELECT id FROM rules WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM story_steps
        WHERE story_id IN (
            SELECT id FROM stories WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 4: Delete rule conditions and parent tables (rules, stories)
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM rule_conditions
        WHERE rule_id IN (
            SELECT id FROM rules WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM rules WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM stories WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 5: Delete forms and their children
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM form_slot_mappings
        WHERE form_required_slot_id IN (
            SELECT frs.id
            FROM form_required_slots frs
            JOIN forms f ON f.id = frs.form_id
            WHERE f.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM form_required_slots
        WHERE form_id IN (
            SELECT id FROM forms WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM forms WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 6: Delete responses and their children
    # NOW SAFE - rule_steps and story_steps already deleted
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM response_components
        WHERE response_variant_id IN (
            SELECT rv.id
            FROM response_variants rv
            JOIN responses r ON r.id = rv.response_id
            WHERE r.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM response_conditions
        WHERE response_variant_id IN (
            SELECT rv.id
            FROM response_variants rv
            JOIN responses r ON r.id = rv.response_id
            WHERE r.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM response_variants
        WHERE response_id IN (
            SELECT id FROM responses WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM responses WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 7: Delete actions
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM actions WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 8: Delete slots and mappings
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM slot_mappings
        WHERE slot_id IN (
            SELECT id FROM slots WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM slots WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 9: Delete regex/lookup/synonym (these reference entities!)
    # MUST be deleted BEFORE entities
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM regex_examples
        WHERE regex_id IN (
            SELECT id FROM regexes WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM regexes WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM lookup_examples
        WHERE lookup_id IN (
            SELECT id FROM lookups WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM lookups WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM synonym_examples
        WHERE synonym_id IN (
            SELECT id FROM synonyms WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM synonyms WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 10: Delete entities and their children
    # NOW SAFE - regexes, lookups, synonyms already deleted
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM entity_roles
        WHERE entity_id IN (
            SELECT id FROM entities WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM entity_groups
        WHERE entity_id IN (
            SELECT id FROM entities WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM entities WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 11: Delete intents and their children
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM intent_examples
        WHERE intent_localization_id IN (
            SELECT il.id
            FROM intent_localizations il
            JOIN intents i ON i.id = il.intent_id
            WHERE i.version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM intent_localizations
        WHERE intent_id IN (
            SELECT id FROM intents WHERE version_id = :vid
        )
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM intents WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    # ================================================================
    # PHASE 12: Delete version config
    # ================================================================
    db.execute(
        text(
            """
        DELETE FROM version_languages WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )

    db.execute(
        text(
            """
        DELETE FROM session_configs WHERE version_id = :vid
    """
        ),
        {"vid": version_id},
    )


def clone_version_data(db: Session, source_id: str, target_id: str):

    entity_map = {}
    intent_map = {}
    slot_map = {}
    form_map = {}
    action_map = {}
    response_map = {}

    for vl in (
        db.query(VersionLanguage).filter(VersionLanguage.version_id == source_id).all()
    ):
        db.add(
            VersionLanguage(
                version_id=target_id,
                language_id=vl.language_id,
                is_default=vl.is_default,
            )
        )

    sc = db.query(SessionConfig).filter(SessionConfig.version_id == source_id).first()
    if sc:
        db.add(
            SessionConfig(
                version_id=target_id,
                session_expiration_time=sc.session_expiration_time,
                carry_over_slots_to_new_session=sc.carry_over_slots_to_new_session,
            )
        )

    for entity in db.query(Entity).filter(Entity.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        entity_map[entity.id] = new_id

        db.add(
            Entity(
                id=new_id,
                version_id=target_id,
                entity_key=entity.entity_key,
                entity_type=entity.entity_type,
                use_regex=entity.use_regex,
                use_lookup=entity.use_lookup,
                influence_conversation=entity.influence_conversation,
            )
        )

        for role in (
            db.query(EntityRole).filter(EntityRole.entity_id == entity.id).all()
        ):
            db.add(EntityRole(entity_id=new_id, role=role.role))

        for group in (
            db.query(EntityGroup).filter(EntityGroup.entity_id == entity.id).all()
        ):
            db.add(EntityGroup(entity_id=new_id, group_name=group.group_name))

    for intent in db.query(Intent).filter(Intent.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        intent_map[intent.id] = new_id

        db.add(
            Intent(
                id=new_id,
                version_id=target_id,
                intent_name=intent.intent_name,
            )
        )

        for loc in (
            db.query(IntentLocalization)
            .filter(IntentLocalization.intent_id == intent.id)
            .all()
        ):
            new_loc_id = str(uuid.uuid4())
            db.add(
                IntentLocalization(
                    id=new_loc_id,
                    intent_id=new_id,
                    language_id=loc.language_id,
                )
            )

            for ex in (
                db.query(IntentExample)
                .filter(IntentExample.intent_localization_id == loc.id)
                .all()
            ):
                db.add(
                    IntentExample(
                        intent_localization_id=new_loc_id,
                        example=ex.example,
                    )
                )

    for slot in db.query(Slot).filter(Slot.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        slot_map[slot.id] = new_id

        db.add(
            Slot(
                id=new_id,
                version_id=target_id,
                name=slot.name,
                slot_type=slot.slot_type,
                influence_conversation=slot.influence_conversation,
                initial_value=slot.initial_value,
                values=slot.values,
                min_value=slot.min_value,
                max_value=slot.max_value,
            )
        )

        for mapping in (
            db.query(SlotMapping).filter(SlotMapping.slot_id == slot.id).all()
        ):
            db.add(
                SlotMapping(
                    slot_id=new_id,
                    mapping_type=mapping.mapping_type,
                    entity_id=(
                        entity_map.get(mapping.entity_id) if mapping.entity_id else None
                    ),
                    role=mapping.role,
                    group=mapping.group,
                    intent=mapping.intent,
                    not_intent=mapping.not_intent,
                    value=mapping.value,
                    conditions=mapping.conditions,
                    active_loop=mapping.active_loop,
                    priority=mapping.priority,
                )
            )

    for form in db.query(Form).filter(Form.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        form_map[form.id] = new_id

        db.add(
            Form(
                id=new_id,
                version_id=target_id,
                name=form.name,
                ignored_intents=form.ignored_intents,
            )
        )

        for frs in (
            db.query(FormRequiredSlot).filter(FormRequiredSlot.form_id == form.id).all()
        ):
            new_frs_id = str(uuid.uuid4())
            db.add(
                FormRequiredSlot(
                    id=new_frs_id,
                    form_id=new_id,
                    slot_id=slot_map.get(frs.slot_id),
                    order=frs.order,
                    required=frs.required,
                )
            )

            for fsm in (
                db.query(FormSlotMapping)
                .filter(FormSlotMapping.form_required_slot_id == frs.id)
                .all()
            ):
                db.add(
                    FormSlotMapping(
                        form_required_slot_id=new_frs_id,
                        mapping_type=fsm.mapping_type,
                        entity_id=(
                            entity_map.get(fsm.entity_id) if fsm.entity_id else None
                        ),
                        intent=fsm.intent,
                        not_intent=fsm.not_intent,
                        value=fsm.value,
                    )
                )

    for action in db.query(Action).filter(Action.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        action_map[action.id] = new_id

        db.add(
            Action(
                id=new_id,
                version_id=target_id,
                name=action.name,
                description=action.description,
            )
        )

    for response in db.query(Response).filter(Response.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        response_map[response.id] = new_id

        db.add(
            Response(
                id=new_id,
                version_id=target_id,
                name=response.name,
            )
        )

        for variant in (
            db.query(ResponseVariant)
            .filter(ResponseVariant.response_id == response.id)
            .all()
        ):
            new_var_id = str(uuid.uuid4())
            db.add(
                ResponseVariant(
                    id=new_var_id,
                    response_id=new_id,
                    language_id=variant.language_id,
                    priority=variant.priority,
                )
            )

            for cond in (
                db.query(ResponseCondition)
                .filter(ResponseCondition.response_variant_id == variant.id)
                .all()
            ):
                db.add(
                    ResponseCondition(
                        response_variant_id=new_var_id,
                        condition_type=cond.condition_type,
                        slot_name=cond.slot_name,
                        slot_value=cond.slot_value,
                        order_index=cond.order_index,
                    )
                )

            for comp in (
                db.query(ResponseComponent)
                .filter(ResponseComponent.response_variant_id == variant.id)
                .all()
            ):
                db.add(
                    ResponseComponent(
                        response_variant_id=new_var_id,
                        component_type=comp.component_type,
                        payload=comp.payload,
                        order_index=comp.order_index,
                    )
                )

    or_group_map = {}

    for story in db.query(Story).filter(Story.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        db.add(
            Story(
                id=new_id,
                version_id=target_id,
                name=story.name,
            )
        )

        for step in db.query(StoryStep).filter(StoryStep.story_id == story.id).all():
            new_step_id = str(uuid.uuid4())
            new_or_group_id = None

            if step.or_group_id:
                if step.or_group_id not in or_group_map:
                    or_group_map[step.or_group_id] = str(uuid.uuid4())
                new_or_group_id = or_group_map[step.or_group_id]

            db.add(
                StoryStep(
                    id=new_step_id,
                    story_id=new_id,
                    timeline_index=step.timeline_index,
                    step_order=step.step_order,
                    step_type=step.step_type,
                    intent_id=(
                        intent_map.get(step.intent_id) if step.intent_id else None
                    ),
                    action_id=(
                        action_map.get(step.action_id) if step.action_id else None
                    ),
                    response_id=(
                        response_map.get(step.response_id) if step.response_id else None
                    ),
                    form_id=form_map.get(step.form_id) if step.form_id else None,
                    active_loop_value=step.active_loop_value,
                    checkpoint_name=step.checkpoint_name,
                    or_group_id=new_or_group_id,
                )
            )

            for event in (
                db.query(StorySlotEvent)
                .filter(StorySlotEvent.story_step_id == step.id)
                .all()
            ):
                db.add(
                    StorySlotEvent(
                        story_step_id=new_step_id,
                        slot_id=slot_map.get(event.slot_id),
                        value=event.value,
                    )
                )

            for step_entity in (
                db.query(StoryStepEntity)
                .filter(StoryStepEntity.story_step_id == step.id)
                .all()
            ):
                db.add(
                    StoryStepEntity(
                        story_step_id=new_step_id,
                        entity_id=entity_map.get(step_entity.entity_id),
                        value=step_entity.value,
                        role=step_entity.role,
                        group=step_entity.group,
                    )
                )

    for rule in db.query(Rule).filter(Rule.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        db.add(
            Rule(
                id=new_id,
                version_id=target_id,
                name=rule.name,
            )
        )

        for cond in (
            db.query(RuleCondition).filter(RuleCondition.rule_id == rule.id).all()
        ):
            db.add(
                RuleCondition(
                    rule_id=new_id,
                    condition_type=cond.condition_type,
                    slot_name=cond.slot_name,
                    slot_value=cond.slot_value,
                    active_loop=cond.active_loop,
                    order_index=cond.order_index,
                )
            )

        for step in db.query(RuleStep).filter(RuleStep.rule_id == rule.id).all():
            new_step_id = str(uuid.uuid4())
            db.add(
                RuleStep(
                    id=new_step_id,
                    rule_id=new_id,
                    step_order=step.step_order,
                    step_type=step.step_type,
                    intent_id=(
                        intent_map.get(step.intent_id) if step.intent_id else None
                    ),
                    action_id=(
                        action_map.get(step.action_id) if step.action_id else None
                    ),
                    response_id=(
                        response_map.get(step.response_id) if step.response_id else None
                    ),
                    form_id=form_map.get(step.form_id) if step.form_id else None,
                    active_loop_value=step.active_loop_value,
                )
            )

            for event in (
                db.query(RuleSlotEvent)
                .filter(RuleSlotEvent.rule_step_id == step.id)
                .all()
            ):
                db.add(
                    RuleSlotEvent(
                        rule_step_id=new_step_id,
                        slot_id=slot_map.get(event.slot_id),
                        value=event.value,
                    )
                )

            for step_entity in (
                db.query(RuleStepEntity)
                .filter(RuleStepEntity.rule_step_id == step.id)
                .all()
            ):
                db.add(
                    RuleStepEntity(
                        rule_step_id=new_step_id,
                        entity_id=entity_map.get(step_entity.entity_id),
                        value=step_entity.value,
                        role=step_entity.role,
                        group=step_entity.group,
                    )
                )

    for regex in db.query(Regex).filter(Regex.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        db.add(
            Regex(
                id=new_id,
                version_id=target_id,
                regex_name=regex.regex_name,
                entity_id=entity_map.get(regex.entity_id),
            )
        )

        for ex in (
            db.query(RegexExample).filter(RegexExample.regex_id == regex.id).all()
        ):
            db.add(
                RegexExample(
                    regex_id=new_id,
                    language_id=ex.language_id,
                    example=ex.example,
                )
            )

    for lookup in db.query(Lookup).filter(Lookup.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        db.add(
            Lookup(
                id=new_id,
                version_id=target_id,
                lookup_name=lookup.lookup_name,
                entity_id=entity_map.get(lookup.entity_id),
            )
        )

        for ex in (
            db.query(LookupExample).filter(LookupExample.lookup_id == lookup.id).all()
        ):
            db.add(
                LookupExample(
                    lookup_id=new_id,
                    language_id=ex.language_id,
                    example=ex.example,
                )
            )

    for synonym in db.query(Synonym).filter(Synonym.version_id == source_id).all():
        new_id = str(uuid.uuid4())
        db.add(
            Synonym(
                id=new_id,
                version_id=target_id,
                canonical_value=synonym.canonical_value,
                entity_id=entity_map.get(synonym.entity_id),
            )
        )

        for ex in (
            db.query(SynonymExample)
            .filter(SynonymExample.synonym_id == synonym.id)
            .all()
        ):
            db.add(
                SynonymExample(
                    synonym_id=new_id,
                    language_id=ex.language_id,
                    example=ex.example,
                )
            )

    db.flush()

    return {
        "entity_map": entity_map,
        "intent_map": intent_map,
        "slot_map": slot_map,
        "form_map": form_map,
        "action_map": action_map,
        "response_map": response_map,
    }


def increment_version_label(label: str) -> str:
    if label.startswith("v") and label[1:].isdigit():
        return f"v{int(label[1:]) + 1}"
    return label
