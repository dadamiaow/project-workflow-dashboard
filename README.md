# Project Workflow Dashboard

A Codex skill that turns existing project progress and results into a standalone HTML dashboard. Routine refreshes update the current page. Selected milestones can be saved as dated HTML snapshots.

## Install for your user

Copy the entire [skill folder](skills/project-workflow-dashboard/) into your user-level Codex skills directory so its entrypoint is `~/.agents/skills/project-workflow-dashboard/SKILL.md`. On Windows, the directory is under your user profile. Open a project in Codex and invoke `$project-workflow-dashboard`.

> Use `$project-workflow-dashboard` to update this project's workflow dashboard from the current progress record and latest test results.

## Try the renderer

The bundled renderer uses Python 3.10 or later and the standard library. From the root of this repository, save the following as `dashboard.json`.

```json
{
  "title": "Release workflow",
  "as_of": "2026-11-24",
  "summary": "Staging is approved. Production rollout is next.",
  "stages": [
    {"title": "Tests", "status": "Passed", "detail": "118 of 120 checks passed."},
    {"title": "Production rollout", "status": "Pending"}
  ],
  "charts": [
    {"title": "Release checks", "max": 120, "values": [["Passed", 118]]}
  ]
}
```

```sh
python skills/project-workflow-dashboard/scripts/render.py dashboard.json --output docs/workflow.html
```

Open `docs/workflow.html` in a browser. To save a milestone, append `--snapshot docs/archive/workflow/2026-11-24-staging-approved.html`. Identical snapshot content is kept once.

See the [skill instructions](skills/project-workflow-dashboard/SKILL.md) for the input format, including tables, expandable details, and source references.
