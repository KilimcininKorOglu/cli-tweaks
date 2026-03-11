# Add Subcommand

When `$task-plan add` is executed, add a new feature to the project.

## Usage

```bash
$task-plan add "kullanici kayit sistemi"       # Inline description
$task-plan add @docs/webhook-spec.md           # From file
```

## Input Methods

### Inline Description
Analyze the description, automatically determine priority and effort estimates,
break it down into logical tasks.

### File Input (@file)
Read the file and extract: feature name/description, requirements/goals,
technical details, acceptance criteria. Supports any text-based file (.md, .txt, etc.).
Use free-form analysis - no specific template required.

## Implementation Steps

1. **Find highest Feature ID**: Scan `tasks/XXX-*.md` files, find highest FXXX
2. **Find highest Task ID**: Scan all feature files, find highest TXXX
3. **Analyze feature**: Break down into logical tasks
4. **Create feature file**: `tasks/XXX-feature-name.md` using [feature template](../assets/feature.md)
5. **Update Status Tracker**: Update `tasks/tasks-status.md`
6. **Update Execution Plan**: Update or create `tasks/task-execution-plan.md`

## Output

```
Feature added!

  Feature ID: F001
  File:       tasks/001-kullanici-kayit-sistemi.md
  Name:       Kullanici Kayit Sistemi
  Priority:   P2
  Tasks:      5 (T001-T005)
  Effort:     4 days (total)
```

## Adding to Existing Projects

IDs always continue from highest existing:
```bash
$task-plan add "kullanici kayit sistemi"   # F001, T001-T005
$task-plan add "sifre sifirlama"           # F002, T006-T008
$task-plan add "email dogrulama"           # F003, T009-T012
```

Auto-creates `tasks/` directory if it doesn't exist.
