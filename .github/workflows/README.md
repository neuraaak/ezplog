# CI/CD Pipeline

The numbered reusable workflows have one responsibility each. Their names
express the execution order.

```text
00-install-deps  ← warms the uv cache
01-ci            ← quality gate for pull requests and releases
02-tag-sync      ← CI gate, tag decision, then calls 03 and 04
03-publish       ← builds always; publishes on create only
04-docs          ← builds always; deploys according to tag_action
```

## Release modes

`02-tag-sync.yml` reads the version from `pyproject.toml`; it never bumps it.

| `tag_action` | Condition                     | Tag                                    | Publish       | Docs                 |
| ------------ | ----------------------------- | -------------------------------------- | ------------- | -------------------- |
| `create`     | `main` and a new version      | Creates `vX.Y.Z` and moves `vX-latest` | PyPI via OIDC | Version and `latest` |
| `skip`       | `main` and tag already exists | None                                   | Not called    | Refreshes `dev`      |
| `preview`    | Manual run outside `main`     | None                                   | Build only    | Build only           |

The release tag is immutable. Only the major `vX-latest` alias is moved.

## Safety properties

- `01-ci.yml` is called by `02-tag-sync.yml`, so tags and publication wait for
  linting, typing, import contracts, security checks and tests.
- Manual publication and documentation runs default to `preview`.
- Publishing uses PyPI Trusted Publishing through OIDC; no registry secret is
  stored in the repository.
- `03-publish.yml` and `04-docs.yml` gate release side effects on the
  `tag_action` input, not `github.event_name`, because reusable workflows
  inherit the caller event.

## Local equivalents

```bash
uv sync --group dev
uv run poe check
uv run poe security
uv run poe docs-build
uv run poe build
uv run twine check dist/*
```

The release workflows are intentionally not run locally: tag creation, PyPI
publication and documentation deployment are remote side effects.
