"""
Lecture/écriture des paramètres propriétaires dans /app/files/params.yaml.
Le fichier est dans le volume Docker persisté (./files:/app/files).

Structure YAML :
  owners:
    "1":
      rentReceiptDay: 1   # jour du mois pour la génération des quittances
    "2":
      rentReceiptDay: 5
"""
from pathlib import Path

import yaml

PARAMS_FILE = Path("/app/files/params.yaml")


def _load() -> dict:
    if not PARAMS_FILE.exists():
        return {"owners": {}}
    with PARAMS_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if "owners" not in data:
        data["owners"] = {}
    return data


def _save(data: dict) -> None:
    PARAMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PARAMS_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=True)


DEFAULTS = {
    "rentReceiptDay": 25,
}


def get_owner_params(owner_id: int) -> dict:
    data = _load()
    stored = data["owners"].get(str(owner_id), {})
    return {**DEFAULTS, **stored}


def set_owner_params(owner_id: int, params: dict) -> dict:
    data = _load()
    # Merge : on ne remplace que les clés fournies
    current = data["owners"].get(str(owner_id), {})
    current.update({k: v for k, v in params.items() if v is not None})
    data["owners"][str(owner_id)] = current
    _save(data)
    return current


def get_all_params() -> dict[str, dict]:
    """Retourne les params de tous les propriétaires (usage admin)."""
    return dict(_load()["owners"])
