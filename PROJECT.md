# Project Configuration

## Project Board

```json
{
  "projectId": "PVT_kwDODElOnc4BEzjB",
  "statusFieldId": "PVTSSF_lADODElOnc4BEzjBzg2UzOM",
  "statusOptions": {
    "todo": "f75ad846",
    "inProgress": "47fc9ee4"
  }
}
```

## Issue Templates

```json
{
  "source": "local",
  "basePath": ".github/ISSUE_TEMPLATE",
  "templates": {
    "small": "small_issue.md",
    "medium": "medium_issue.md",
    "large": "large_issue.md"
  }
}
```

## Labels

```json
{
  "sizes": [
    {
      "name": "!size:small",
      "description": "Single task, one file or module",
      "color": "2da44e"
    },
    {
      "name": "!size:medium",
      "description": "Multiple related changes across a few files",
      "color": "d29922"
    },
    {
      "name": "!size:large",
      "description": "Spans multiple modules or requires design decisions",
      "color": "cf222e"
    }
  ],
  "priorities": [
    { "name": "🔥 P0", "color": "B60205" },
    { "name": "⚡ P1", "color": "D93F0B" },
    { "name": "📌 P2", "color": "FBCA04" },
    { "name": "📝 P3", "color": "0E8A16" }
  ],
  "phases": [
    { "name": "Phase 1", "description": "Database & Curation Pipeline", "color": "C2E0C6" },
    { "name": "Phase 2", "description": "Public API", "color": "BFD4F2" },
    { "name": "Phase 3", "description": "MCP Server", "color": "D4C5F9" },
    { "name": "Phase 4", "description": "Website Refresh & Agent Onboarding", "color": "F9D0C4" }
  ]
}
```
