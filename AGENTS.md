# AGENTS.md — ezplog

Fichier de référence autonome pour les agents IA travaillant sur ce repo.
Lire entièrement avant toute modification.

---

## Identité du projet

| Champ           | Valeur                                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| **Nom**         | ezplog                                                                                                     |
| **Version**     | 2.1.7                                                                                                      |
| **Python**      | ≥ 3.11                                                                                                     |
| **Licence**     | MIT                                                                                                        |
| **Description** | Framework de logging Python moderne : Rich (console) + loguru (fichier), API typée, dual-mode (lib / app). |
| **CLI**         | `ezpl` → entry point `ezplog.cli.main:cli`                                                                 |
| **PyPI**        | <https://pypi.org/project/ezplog/>                                                                         |
| **Repo**        | <https://github.com/neuraaak/ezplog>                                                                       |

---

## Architecture

### Couches hexagonales — flux descendant uniquement

```text
ezplog.cli          ← commandes utilisateur (Click)
  ↓
ezplog.handlers     ← EzPrinter (Rich), EzLogger (loguru), RichWizard
  ↓
ezplog.config       ← ConfigurationManager, valeurs par défaut
  ↓
ezplog.types        ← enums (LogLevel, Pattern), protocols (LoggerProtocol, PrinterProtocol)
  ↓
ezplog.utils        ← utilitaires partagés
  ↓
ezplog.core         ← interfaces abstraites (LoggingHandler, IndentationManager), exceptions
```

**Règle absolue :** une couche ne peut importer que les couches en dessous d'elle.
Vérification via `import-linter` (`lint-imports`).

### Cas particulier

- `src/ezpl/` — shim de rétrocompatibilité uniquement. Ne pas modifier, ne pas importer directement.
- `src/ezplog/ezpl.py` — classe `Ezpl`, façade principale (Singleton).
- `src/ezplog/lib_mode.py` — proxies passifs pour auteurs de bibliothèques.
- `src/ezplog/app_mode.py` — interception stdlib (`InterceptHandler`).

### Structure des sources

```text
src/
├── ezplog/
│   ├── __init__.py         # API publique (__all__)
│   ├── _version.py
│   ├── ezpl.py             # Classe Ezpl (Singleton, façade)
│   ├── app_mode.py
│   ├── lib_mode.py
│   ├── cli/
│   │   ├── main.py         # groupe CLI Click
│   │   ├── commands/       # _config, _docs, _info, _logs, _version
│   │   └── utils/          # _log_parser, _log_stats, _env_manager
│   ├── config/
│   │   ├── manager.py      # ConfigurationManager
│   │   └── _defaults.py
│   ├── core/
│   │   ├── interfaces.py   # ABCs + Protocol
│   │   └── exceptions.py   # EzplError, ConfigurationError, etc.
│   ├── handlers/
│   │   ├── console.py      # EzPrinter
│   │   ├── file.py         # EzLogger
│   │   └── wizard/         # RichWizard, DynamicLayeredProgress
│   ├── types/
│   │   ├── enums/          # LogLevel, Pattern, PATTERN_COLORS
│   │   └── protocols/      # LoggerProtocol, PrinterProtocol
│   └── utils/
└── ezpl/                   # shim rétrocompat (ne pas modifier)
```

---

## Dual-mode d'utilisation

**App mode** — configurer une fois au niveau application :

```python
from ezplog import Ezpl
ezpl = Ezpl(log_file="app.log", hook_logger=True, lock_config=True)
ezpl.info("démarrage")
```

**Lib mode** — proxies passifs pour bibliothèques (silencieux sans hôte) :

```python
from ezplog.lib_mode import get_logger, get_printer
log = get_logger(__name__)
printer = get_printer()
```

---

## Commandes de validation

Raccourcis `poe` (équivalents, à préférer) :

```bash
uv run poe check        # format-check + lint + typecheck + imports + test
uv run poe lint-fix     # corrige automatiquement
uv run poe test-unit    # tests unitaires seuls
uv run poe docs-build   # build mkdocs strict
```

Lancer après toute modification de `src/` :

```bash
# Linting & formatting
ruff check src/ tests/
ruff format src/ tests/

# Type checking
pyright
ty check

# Tests (coverage ≥ 70% obligatoire)
pytest
pytest -m unit          # tests unitaires uniquement
pytest -m "not slow"    # exclure les tests lents

# Sécurité
bandit -r src/

# Contrats d'import (couches)
PYTHONPATH=src lint-imports
```

Markers pytest disponibles : `unit`, `integration`, `robustness`, `slow`, `wizard`, `config`, `cli`.

---

## Conventions de code

| Règle                | Détail                                             |
| -------------------- | -------------------------------------------------- |
| **Style**            | ruff, line-length 88, quotes doubles, Python 3.11+ |
| **Modules internes** | préfixés `_` (ex : `_defaults.py`, `_console.py`)  |
| **Visibilité**       | tout module public doit déclarer `__all__`         |
| **Imports de types** | uniquement sous `TYPE_CHECKING`                    |
| **assert**           | interdit hors `tests/`                             |
| **cast()**           | éviter, préférer les type guards                   |
| **Singleton**        | pattern maintenu sur `Ezpl` — ne pas refactoriser  |
| **Commentaires**     | uniquement si le WHY est non-évident               |

---

## Règles de comportement

### Avant toute modification

- Lire les fichiers concernés avant de répondre. Pas de suppositions sur le code.
- Vérifier les contrats d'import avant d'ajouter une dépendance inter-couches.

### Pendant les modifications

- Édits chirurgicaux uniquement — pas de refactor non demandé, pas de docstrings ajoutés, pas d'abstractions supplémentaires.
- Toute modification de `src/` → relancer `pytest` et `ruff check`.
- Respecter la visibilité : ne pas exposer de symboles internes dans `__all__`.

### Commits

Conventional Commits obligatoires. Types supportés :

```text
feat, fix, docs, style, refactor, test, chore, perf, ci, build
prompt   ← modification d'instructions / prompts
agent    ← modification de policy agent
```

Format : `type(scope): message en minuscules`
Exemple : `fix(handlers): corrige le niveau de log EzPrinter`

### Actions irréversibles

Demander confirmation avant : `git push --force`, publication PyPI (`twine upload`), suppression de fichiers, modification des workflows CI.

---

## Exceptions disponibles

Toutes héritent de `EzplError` (base) :

| Classe                | Usage                    |
| --------------------- | ------------------------ |
| `ConfigurationError`  | erreur de config         |
| `LoggingError`        | erreur de logging        |
| `ValidationError`     | validation de paramètres |
| `InitializationError` | init du Singleton        |
| `FileOperationError`  | opération fichier        |
| `HandlerError`        | erreur de handler        |

---

## Ce qu'il ne faut pas faire

- Importer `src/ezpl/` directement (shim interne).
- Briser les contrats de couches (vérifier avec `lint-imports`).
- Modifier `src/ezplog/ezpl.py` pour retirer le pattern Singleton.
- Publier sur PyPI sans validation CI complète.
- Ajouter des dépendances à `dependencies` sans discussion préalable.
