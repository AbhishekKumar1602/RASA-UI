from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import io
import zipfile
import yaml

from app.core.dependencies import get_db
from app.models import Project, Version, VersionLanguage, Language
from app.utils.nlu_yaml_writer import export_nlu_yaml
from app.utils.domain_yaml_writer import export_domain_yaml
from app.utils.story_yaml_writer import export_stories_yaml
from app.utils.rule_yaml_writer import export_rules_yaml


router = APIRouter(prefix="/projects", tags=["Export"])


def get_version_by_status(db: Session, project_code: str, status: str) -> Version:
    project = (
        db.query(Project)
        .filter(Project.project_code == project_code)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")

    version = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == status,
        )
        .first()
    )
    if not version:
        raise HTTPException(404, f"Version with status '{status}' not found")

    return version


def get_version_languages(db: Session, version_id: str) -> List[str]:
    results = (
        db.query(Language.language_code)
        .join(VersionLanguage, VersionLanguage.language_id == Language.id)
        .filter(VersionLanguage.version_id == version_id)
        .all()
    )
    return [r[0] for r in results]


def dict_to_yaml(data: Dict[str, Any]) -> str:
    
    def str_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data)
    
    yaml.add_representer(str, str_representer)
    
    return yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=1000
    )


def generate_config_yaml() -> str:
    config = {
        'recipe': 'default.v1',
        'language': 'en',
        'pipeline': [
            {'name': 'WhitespaceTokenizer'},
            {'name': 'RegexFeaturizer'},
            {'name': 'LexicalSyntacticFeaturizer'},
            {'name': 'CountVectorsFeaturizer'},
            {
                'name': 'CountVectorsFeaturizer',
                'analyzer': 'char_wb',
                'min_ngram': 1,
                'max_ngram': 4
            },
            {
                'name': 'DIETClassifier',
                'epochs': 100,
                'constrain_similarities': True
            },
            {'name': 'EntitySynonymMapper'},
            {
                'name': 'ResponseSelector',
                'epochs': 100,
                'constrain_similarities': True
            },
            {
                'name': 'FallbackClassifier',
                'threshold': 0.3,
                'ambiguity_threshold': 0.1
            }
        ],
        'policies': [
            {'name': 'MemoizationPolicy'},
            {'name': 'RulePolicy'},
            {
                'name': 'TEDPolicy',
                'max_history': 5,
                'epochs': 100,
                'constrain_similarities': True
            }
        ]
    }
    return dict_to_yaml(config)


def generate_endpoints_yaml() -> str:
    endpoints = {
        'action_endpoint': {
            'url': 'http://localhost:5055/webhook'
        }
    }
    return dict_to_yaml(endpoints)


def generate_credentials_yaml() -> str:
    credentials = {
        'rest': None,
        'socketio': {
            'user_message_evt': 'user_uttered',
            'bot_message_evt': 'bot_uttered',
            'session_persistence': False
        }
    }
    return dict_to_yaml(credentials)



@router.get("/{project_code}/versions/{status}/export/nlu/{language_code}")
def export_nlu(
    project_code: str,
    status: str,
    language_code: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    return export_nlu_yaml(db=db, version_id=version.id, language_code=language_code)


@router.get("/{project_code}/versions/{status}/export/domain")
def export_domain(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    return export_domain_yaml(db, version.id)


@router.get("/{project_code}/versions/{status}/export/stories")
def export_stories(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    return export_stories_yaml(db, version.id)


@router.get("/{project_code}/versions/{status}/export/rules")
def export_rules(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    return export_rules_yaml(db, version.id)


@router.get("/{project_code}/versions/{status}/export/all")
def export_all_json(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:

    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    languages = get_version_languages(db, version.id)
    
    if not languages:
        raise HTTPException(400, "No languages configured for this version")
    
    result = {
        "project_code": project_code,
        "version_status": status,
        "version_label": version.version_label,
        "languages": languages,
        "files": {
            "domain": export_domain_yaml(db, version.id),
            "stories": export_stories_yaml(db, version.id),
            "rules": export_rules_yaml(db, version.id),
            "nlu": {},
            "config": {
                "recipe": "default.v1",
                "language": languages[0] if languages else "en",
                "pipeline": "See RASA documentation for pipeline configuration",
                "policies": "See RASA documentation for policy configuration"
            }
        }
    }
    
    for lang in languages:
        try:
            result["files"]["nlu"][lang] = export_nlu_yaml(
                db=db, 
                version_id=version.id, 
                language_code=lang
            )
        except HTTPException:
            pass
    
    return result


@router.get("/{project_code}/versions/{status}/export/zip")
def export_all_zip(
    project_code: str,
    status: str,
    include_config: bool = True,
    db: Session = Depends(get_db),
):

    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    languages = get_version_languages(db, version.id)
    
    if not languages:
        raise HTTPException(400, "No languages configured for this version")
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        try:
            domain_data = export_domain_yaml(db, version.id)
            zip_file.writestr("domain.yml", dict_to_yaml(domain_data))
        except Exception as e:
            zip_file.writestr("domain.yml", f"# Error exporting domain: {e}\nversion: '3.1'")
        
        try:
            stories_data = export_stories_yaml(db, version.id)
            zip_file.writestr("data/stories.yml", dict_to_yaml(stories_data))
        except Exception as e:
            zip_file.writestr("data/stories.yml", f"# Error exporting stories: {e}\nversion: '3.1'\nstories: []")
        
        try:
            rules_data = export_rules_yaml(db, version.id)
            zip_file.writestr("data/rules.yml", dict_to_yaml(rules_data))
        except Exception as e:
            zip_file.writestr("data/rules.yml", f"# Error exporting rules: {e}\nversion: '3.1'\nrules: []")
        
        for lang in languages:
            try:
                nlu_data = export_nlu_yaml(db=db, version_id=version.id, language_code=lang)
                zip_file.writestr(f"data/nlu_{lang}.yml", dict_to_yaml(nlu_data))
            except HTTPException as e:
                zip_file.writestr(
                    f"data/nlu_{lang}.yml", 
                    f"# No NLU data for language '{lang}'\nversion: '3.1'\nnlu: []"
                )
        
        if include_config:
            zip_file.writestr("config.yml", generate_config_yaml())
            zip_file.writestr("endpoints.yml", generate_endpoints_yaml())
            zip_file.writestr("credentials.yml", generate_credentials_yaml())
        
        readme_content = f"""# RASA Bot Export
        
Project: {project_code}
Version: {version.version_label} ({status})
Languages: {', '.join(languages)}

## Files Included

- `domain.yml` - Domain configuration (intents, entities, slots, forms, responses, actions)
- `data/stories.yml` - Conversation stories
- `data/rules.yml` - Conversation rules
- `data/nlu_*.yml` - NLU training data for each language
- `config.yml` - RASA configuration template
- `endpoints.yml` - Endpoints configuration template
- `credentials.yml` - Channel credentials template

## Getting Started

1. Install RASA: `pip install rasa`
2. Train the model: `rasa train`
3. Test in shell: `rasa shell`
4. Run the bot: `rasa run --enable-api`

## Documentation

- RASA Documentation: https://rasa.com/docs/
- Model Configuration: https://rasa.com/docs/rasa/model-configuration/
"""
        zip_file.writestr("README.md", readme_content)
    
    zip_buffer.seek(0)
    
    filename = f"{project_code}_{version.version_label}_{status}_rasa_export.zip"
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{project_code}/versions/{status}/export/nlu/{language_code}/download")
def download_nlu_yaml(
    project_code: str,
    status: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    data = export_nlu_yaml(db=db, version_id=version.id, language_code=language_code)
    
    yaml_content = dict_to_yaml(data)
    
    return StreamingResponse(
        io.BytesIO(yaml_content.encode('utf-8')),
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": f"attachment; filename=nlu_{language_code}.yml"
        }
    )


@router.get("/{project_code}/versions/{status}/export/domain/download")
def download_domain_yaml(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    data = export_domain_yaml(db, version.id)
    
    yaml_content = dict_to_yaml(data)
    
    return StreamingResponse(
        io.BytesIO(yaml_content.encode('utf-8')),
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": "attachment; filename=domain.yml"
        }
    )


@router.get("/{project_code}/versions/{status}/export/stories/download")
def download_stories_yaml(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    data = export_stories_yaml(db, version.id)
    
    yaml_content = dict_to_yaml(data)
    
    return StreamingResponse(
        io.BytesIO(yaml_content.encode('utf-8')),
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": "attachment; filename=stories.yml"
        }
    )


@router.get("/{project_code}/versions/{status}/export/rules/download")
def download_rules_yaml(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    if status not in ("draft", "locked"):
        raise HTTPException(400, "Invalid version status for export")
    
    version = get_version_by_status(db, project_code, status)
    data = export_rules_yaml(db, version.id)
    
    yaml_content = dict_to_yaml(data)
    
    return StreamingResponse(
        io.BytesIO(yaml_content.encode('utf-8')),
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": "attachment; filename=rules.yml"
        }
    )

