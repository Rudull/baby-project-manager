# AGENTS.md

Guía para agentes de IA y contribuidores. Documentación completa en [README.md](README.md) y [STRUCTURE.md](STRUCTURE.md).

## Entorno

```powershell
conda env create -f environment_windows.yaml  # Linux: environment_linux.yaml
conda activate baby
python src/main.py
```

## Comandos de verificación

```powershell
ruff check src/ tests/   # lint (mismo comando que CI)
pytest                   # suite automática (config en pyproject.toml)
```

- CI (`.github/workflows/ci.yml`): lint + tests en Python 3.11/3.12 con `QT_QPA_PLATFORM=offscreen`.
- Tests manuales/e2e: `scratch/` — ver [scratch/readme.md](scratch/readme.md).
- Hooks locales: `pre-commit install` (ruff lint/format + checks básicos).

## Build

```powershell
python build_system/build_to_distribution.py          # interactivo (recomendado)
python build_system/build_nuitka_windows.py --clean   # Nuitka directo
```

## Convenciones

- `src/`: `core/` (lógica sin Qt), `ui/` (PySide6), `utils/` (transversal), `updater/`.
- Config de ruff/pytest/mypy en `pyproject.toml` (Python 3.11, line-length 100).
- Documentación en español.

## Índice de documentación

- [README.md](README.md) — inicio rápido e instalación
- [BUILD.md](BUILD.md) — compilación y distribución
- [STRUCTURE.md](STRUCTURE.md) — arquitectura y árbol de directorios
- [COMMANDS.md](COMMANDS.md) — sistema Undo/Redo
- [ALERTS.md](ALERTS.md) — sistema de alertas
- [ROADMAP.md](ROADMAP.md) — pendientes
- [CHANGELOG.md](CHANGELOG.md) — historial de versiones
