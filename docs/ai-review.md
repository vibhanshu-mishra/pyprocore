# AI Review

PyProcore can create local review packages for use with AI tools, but it does
not call AI APIs. You decide what files to share with any model or reviewer.

## Project Context Package

A project context package collects selected project sections such as RFIs,
submittals, documents, drawings, specifications, photos, and Daily Logs into a
local folder.

```bash
procore-sdk project-context --project 352338 --output ./project-context
```

## Enhanced RFI Package

Enhanced RFI packages include the target RFI plus related project context.

```bash
procore-sdk enhanced-rfi-package --project 352338 --rfi-number 15
```

## Enhanced Submittal Package

Enhanced submittal packages include the target submittal plus related project
context.

```bash
procore-sdk enhanced-submittal-package --project 352338 --submittal-number 27
```

## AI Review Export Layer

The AI review export layer turns an existing local package into files that are
easier to inspect or pass to an AI assistant:

- source index
- system context
- prompt file
- chunk files
- checklist files
- manifest

```bash
procore-sdk ai-review-export --package-dir ./rfi-package
```

## Confidentiality

Generated package folders can contain confidential project data. Review them
before uploading, emailing, or pasting them into any external service.

## Source Discipline

When using the output with an AI assistant, instruct it to use only the provided
sources, cite the source filenames, and separate facts from assumptions.

## Professional Judgment

AI output is not final legal, engineering, design, contractual, or construction
judgment. Treat it as review assistance that must be checked by qualified people.
