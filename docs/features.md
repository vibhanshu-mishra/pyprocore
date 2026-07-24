# Feature Inventory

This page inventories the meaningful capabilities added to PyProcore from its
initial SDK foundation through Phase 18F. It covers features for SDK users,
automation authors, maintainers, CLI users, and documentation contributors.

PyProcore `2.3.0` is the latest published stable release. The repository is
prepared at `2.4.0`; features marked as local maintenance, catalog, trust,
analytics, or template tooling are included in that prepared release.

## Safety Boundaries

- Procore write and mutation actions are not enabled.
- MCP remains discovery-only.
- Agent and Procore tool execution remains disabled.
- AI workflows are local examples only and do not call external AI or model
  services.
- Maintenance workflows are local-only and human-review-first.
- Starter templates are copied files only; PyProcore does not host or run them.
- PyProcore does not automatically publish packages, create commits, open pull
  requests, or certify production compatibility.

## Initial SDK Foundation

| Feature | Technical description | Simple description |
|---|---|---|
| OAuth authorization flow | OAuth2 authorization-code token exchange support | Complete the standard Procore sign-in flow without rebuilding OAuth handling. |
| Automatic token renewal | Expiry-aware refresh token lifecycle management | The SDK refreshes expired access tokens so normal requests can continue. |
| Persistent token storage | Local JSON token persistence abstraction | Save OAuth tokens locally between CLI and SDK sessions. Token values are never printed by diagnostics. |
| Reusable HTTP client | Session-based authenticated REST request client | Make authenticated Procore requests through one reusable client with shared behavior. |
| Core resource services | Typed company project RFI submittal services | List and retrieve the first supported Procore resources through focused service modules. |
| Attachment downloads | Streaming signed attachment download helpers | Download RFI and submittal attachments to local folders with safe filenames. |
| Typed response models | Pydantic resource validation and serialization | Work with attributes such as `rfi.questions` while retaining JSON serialization. |
| Structured logging | Centralized request and error file logging | Review request timing and failures without exposing tokens or authorization headers. |
| Production CLI | Argparse command-line resource access interface | Run common SDK operations from a terminal without writing a Python program. |
| Mocked unit tests | Credential-free HTTP behavior test suite | Validate SDK behavior locally without contacting Procore. |

## Phase 1 — Core Polish

| Feature | Technical description | Simple description |
|---|---|---|
| Coverage configuration | Cross-machine coverage exclusion and reporting rules | Run consistent coverage reports without counting tests, caches, or entry-point guards. |
| Static analysis toolchain | Black isort flake8 formatting enforcement | Keep code style and imports consistent across contributors and machines. |
| Type checking | Mypy validation for public SDK surfaces | Catch incompatible types before changes reach SDK users. |
| Installable package | PEP 517 pyproject package configuration | Install PyProcore in editable or normal mode as a standard Python package. |
| Developer Makefile | Repeatable test lint format maintenance commands | Use short, documented commands for everyday development checks. |
| Custom exception hierarchy | Context-rich SDK-specific custom failure types | Handle authentication, authorization, configuration, missing resources, and API failures clearly. |
| Google-style docstrings | Consistent public API documentation conventions | Understand public classes and functions directly from editor help. |
| Repository hygiene | Cache artifact and secret exclusions | Keep generated files, local credentials, and temporary output out of source control. |

## Phase 2 — Workflow Automation

| Feature | Technical description | Simple description |
|---|---|---|
| Human-friendly resolvers | Case-insensitive exact and partial resource search | Find companies and projects by names or numbers instead of manually locating IDs. |
| Duplicate detection | Typed ambiguous search result exceptions | Receive a clear error when a lookup matches more than one resource. |
| RFI resolver | Project-scoped RFI number lookup helper | Find an RFI using the number people see in Procore. |
| Submittal resolver | Project-scoped submittal number lookup helper | Find a submittal by its familiar project number. |
| Workflow packages | Serializable resolved-resource workflow package model | Bundle metadata, raw records, and downloaded files for downstream work. |
| Package CLI commands | Resolved RFI and submittal package commands | Create repeatable RFI or submittal packages from the command line. |

## Phase 3 — Expanded API Coverage

| Feature | Technical description | Simple description |
|---|---|---|
| Document access | Read-only folder and document services | Browse supported Procore document folders and retrieve document metadata. |
| Drawing access | Drawing-area scoped read and download helpers | List drawing areas first, then inspect or download drawings safely. |
| Specification access | Read-only specification section retrieval services | Retrieve specification sections and their available files for local review. |
| Photo access | Read-only album and photo services | Browse project photo albums and photo metadata without changing Procore. |
| Daily Log access | Read-only supported Daily Log services | Retrieve supported Daily Log entries for reporting and field review. |
| Flexible resource models | Extra-field tolerant Pydantic response models | Preserve useful fields even when Procore payloads vary between tools or environments. |
| Resource exports | CSV and JSONL read-data exporters | Move supported project records into simple local analysis formats. |
| Object client groups | Resource-oriented grouped Procore client namespaces | Discover services through organized properties on the `Procore` client. |

## Phase 4 — AI-ready Project Intelligence

| Feature | Technical description | Simple description |
|---|---|---|
| Project context packages | Multi-resource local project context builder | Collect selected project records into one review-ready local package. |
| Enhanced RFI packages | RFI context attachment source packaging | Build a richer RFI review bundle with related context and source references. |
| Enhanced submittal packages | Submittal context attachment source packaging | Build a richer submittal review bundle for downstream human or AI-assisted review. |
| AI review exports | Local model-neutral review export builder | Prepare structured review material without selecting or calling an AI provider. |
| Prompt packs | Local prompt checklist and source bundles | Generate reusable prompts, instructions, and source indexes for external review workflows. |
| Source manifests | Package file and provenance tracking | See which local records and files were included in each generated package. |
| JSON model export | Typed model JSON serialization examples | Export SDK objects into portable JSON for other local tools. |

## Phase 5 — Automation and Integrations Foundation

| Feature | Technical description | Simple description |
|---|---|---|
| Workflow plan runner | Validated local JSON workflow orchestration | Define repeatable SDK workflows in a readable plan file and run them locally. |
| Placeholder resolution | Deterministic plan value interpolation support | Reuse defaults and outputs from earlier workflow steps without custom glue code. |
| Dependency ordering | Explicit workflow step dependency validation | Ensure a step runs only after the local outputs it needs are ready. |
| Dry-run planning | Non-executing local workflow validation summaries | Review what a plan intends to do before running its SDK workflows. |
| Scheduled examples | Cron launchd Task Scheduler templates | Learn how to schedule local plans on common operating systems. |
| GitHub Actions template | Scheduled workflow artifact example configuration | Adapt a documented CI template while supplying your own secure token strategy. |
| Webhook helpers | Local fixture signature and parsing utilities | Develop and test webhook-shaped workflows locally without hosting an endpoint. |
| Docker templates | Optional local container deployment examples | Use documented starter files for containerized automation without changing the SDK runtime. |

## Phase 6 — Production Polish

| Feature | Technical description | Simple description |
|---|---|---|
| Release metadata | Complete package publishing metadata configuration | Present accurate package, license, Python, dependency, and project-link information. |
| Contributor guidance | Public contribution setup and review documentation | Help new contributors install the project, run checks, and submit safe changes. |
| Community templates | Structured issues and pull request checklists | Collect useful bug and feature details without asking users to expose secrets. |
| Security policy | Vulnerability and credential handling guidance | Explain how to report security issues and protect OAuth credentials. |
| MkDocs site | Strict-build public project documentation website | Browse getting-started, API, workflow, recipe, security, and release guidance as a site. |
| Secrets audit | Local repository credential pattern scanner | Detect common accidental secret patterns before release. |
| Documentation truth audit | Release and safety claim consistency checks | Catch stale version claims or wording that incorrectly enables unsafe behavior. |
| Release readiness checks | Local metadata and repository audit script | Verify required release files and package metadata before publishing manually. |
| Release candidate verification | Clean wheel build and install validation | Build and test package artifacts in an isolated environment without publishing them. |

## Phase 7 — Open Agent API Layer

| Feature | Technical description | Simple description |
|---|---|---|
| Agent tool registry | Read-only local capability metadata registry | Inspect which SDK capabilities could support an assistant while execution remains disabled. |
| Local discovery server | Localhost HTTP metadata discovery API | Explore agent metadata through a local server that cannot execute Procore tools. |
| OpenAPI export | Agent discovery OpenAPI schema generation | Export a machine-readable description of the local discovery API. |
| JSON Schema export | Typed agent model schema generation | Share agent metadata shapes with local developer tools. |
| Run logs | Opt-in sanitized local agent records | Record discovery interactions locally without storing authorization secrets. |
| Replay inspection | Local deterministic recorded-run metadata replay | Review a saved interaction deterministically without calling Procore. |
| Agent eval harness | Deterministic local registry behavior evaluation | Check discovery metadata and safety boundaries without external models. |
| Execution lockout | Agent tool invocation explicitly disabled | Assistants can inspect capabilities but cannot perform Procore operations. |

## Phase 8 — Expanded Procore API Coverage

| Feature | Technical description | Simple description |
|---|---|---|
| Field observations | Read-only observation list get find | Retrieve and locate project observations without changing their status. |
| Punch items | Read-only punch item retrieval helpers | Review punch-list records without creating, closing, or editing items. |
| Correspondence | Generic Tool correspondence read services | Read configured correspondence items through flexible Generic Tool metadata. |
| Client credentials auth | Data Connection App authentication mode | Authenticate supported enterprise integrations without changing the existing authorization-code default. |
| Meetings and inspections | Read-only meeting inspection checklist services | Retrieve meeting and inspection records for local reporting. |
| Incident records | Read-only incident configuration metadata retrieval | Review incidents and supported project incident configuration metadata. |
| Directory resources | Company project user vendor directory services | Read users, vendors, departments, distribution groups, and locations. |
| Financial coverage | Read-only change budget commitment resources | Export supported financial and change-management records without approvals or mutations. |
| Contract and billing coverage | Read-only contracts invoices payments metadata | Inspect supported contract, billing, invoice, and payment records without financial writes. |
| Project management extras | Read-only schedule task form services | Retrieve schedule metadata, tasks, calendars, coordination issues, forms, and action plans. |
| CLI and exports | Resource-specific read commands and exporters | Access the expanded resources through consistent CLI, CSV, and JSONL patterns. |

## Phase 9 — Enterprise Auth and Data Access Hardening

| Feature | Technical description | Simple description |
|---|---|---|
| Auth strategy diagnostics | Mode-aware OAuth configuration validation guidance | Understand whether authorization-code or client-credentials settings are complete. |
| Friendly access errors | Sanitized 401 and 403 explanations | Distinguish expired credentials from company connection, project context, or permission problems. |
| Scheduled export planning | Local enterprise export configuration validation | Review scheduled export settings and output paths without running a live export. |
| Token-store backends | File and memory token storage abstractions | Choose an appropriate local token storage strategy and inspect it without revealing tokens. |
| Rotation guidance | Local credential renewal checklist generation | Follow a practical process when rotating client credentials or token stores. |
| Private deployment patterns | Local enterprise deployment readiness templates | Plan private workers, folders, logs, and operational ownership without provisioning infrastructure. |
| Production runbook | Operational startup recovery security guidance | Give maintainers a clear checklist for operating private deployments. |
| Enterprise readiness CLI | Local-only enterprise deployment configuration checks | Identify missing operational settings before an integration is scheduled. |

## Phase 10 — Async API and Export Support

| Feature | Technical description | Simple description |
|---|---|---|
| Async client | Read-oriented asynchronous Procore client foundation | Retrieve supported resources concurrently in applications that use `asyncio`. |
| Mock async transport | Credential-free deterministic async request transport | Test async code without network access or Procore credentials. |
| Async pagination | Automatic asynchronous multi-page result collection | Retrieve all available pages without manually requesting each page. |
| Async retries | Bounded transient asynchronous failure recovery | Recover from temporary read failures using bounded retry behavior. |
| Async exports | Concurrent CSV and JSONL exporters | Export supported resources efficiently while keeping operations read-only. |
| Download manifests | Local async download planning records | Track intended and completed local downloads with serializable summaries. |
| Concurrency controls | Conservative async workload limiting controls | Avoid overwhelming APIs or local machines during batch reads. |
| Multi-project batches | Validated async project batch plans | Plan and collect supported resources across several projects with per-resource results. |
| Expanded async coverage | Field financial directory project resource reads | Use async helpers across the broader read-oriented service catalog. |
| Async batch CLI | Local validation and dry-run commands | Inspect multi-project batch configuration without making live calls. |

## Phase 11 — Plugin Architecture

| Feature | Technical description | Simple description |
|---|---|---|
| Plugin manifests | Typed local plugin metadata models | Describe a plugin's identity and capabilities without loading its code. |
| Safe local registry | In-memory metadata-only local plugin registration | Browse explicitly registered plugin descriptions without remote discovery. |
| Manifest validation | Local JSON plugin metadata validation | Catch malformed or unsafe plugin declarations before anyone reviews implementation code. |
| Explicit local hooks | In-process callable hook registration only | Applications may register trusted local functions directly; manifests cannot execute them. |
| Sanitized hook contexts | Secret-filtered local hook input models | Keep credential-like values out of local extension inputs and results. |
| Plugin configuration | JSON-only preference and capability metadata | Store local plugin preferences without turning configuration into executable code. |
| Extension packs | Local grouped extension metadata manifests | Describe related local extensions without installing or importing packages. |
| Developer scaffolding | Static plugin template planning and copying | Generate starter files locally with dry-run and overwrite controls. |
| Remote loading lockout | No registry fetch install or import | Plugin metadata cannot download, install, import, or execute remote code. |

## Phase 12 — AI Workflow Examples

| Feature | Technical description | Simple description |
|---|---|---|
| RFI review workflow | Local model-neutral RFI review package | Prepare RFI sources and review instructions for a separately chosen analysis tool. |
| Submittal review workflow | Local model-neutral submittal review package | Assemble submittal context without calling an AI provider. |
| Project Q&A context | Local source-grounded project question package | Organize project records so people can build their own grounded Q&A workflow. |
| Drawing specification comparison | Local comparison prompt and source package | Prepare drawing and specification references for manual or external comparison. |
| Engineering context | Local engineering review context builder | Gather relevant records and limitations for engineering-oriented review. |
| Field issue summaries | Local field record summary prompt package | Prepare field information for a separate summarization workflow. |
| Change risk review | Local change review context package | Organize change-related records for human-owned risk review. |
| Vector export manifests | Local text chunk metadata preparation | Prepare chunks and source labels for a vector system without adding a vector database. |
| Provider neutrality | No external model API integration | Users choose any external model separately; PyProcore makes no model calls. |

## Phase 13 — Golden Datasets and Evals

| Feature | Technical description | Simple description |
|---|---|---|
| Golden datasets | Typed local deterministic evaluation fixtures | Keep known example inputs and expected outcomes for repeatable checks. |
| Workflow eval suites | Resource-specific deterministic workflow output scoring | Check RFI, submittal, async, plugin, and package outputs against explicit rules. |
| Safety scoring | Forbidden action and phrase detection | Detect outputs that suggest writes, execution, or unsupported behavior. |
| Eval baselines | Local deterministic score baseline snapshots | Save expected evaluation results for later comparison. |
| Regression reports | JSON and Markdown baseline comparisons | See whether a change improves, preserves, or reduces expected behavior. |
| Eval history | Local timestamped evaluation result tracking | Review how deterministic checks changed across local development runs. |
| Model-response fixtures | Offline saved response quality evaluation | Evaluate sample AI-style text without contacting a model provider. |
| Grounding checks | Citation limitation and hallucination-risk scoring | Check whether saved responses identify sources and disclose uncertainty. |
| No model judge | Rule-based deterministic local evaluation only | Evaluation remains reproducible and does not depend on another AI service. |

## Phase 15 — MCP Discovery

| Feature | Technical description | Simple description |
|---|---|---|
| MCP resources | Discovery-only local capability resource metadata | Let compatible clients inspect SDK capabilities without running them. |
| MCP prompts | Local review prompt template metadata | Browse prompt templates for review workflows without calling a model. |
| Capability summaries | MCP-safe feature and boundary descriptions | Explain available metadata and the actions that remain disabled. |
| Kind filters | Resource and prompt metadata filtering | Narrow discovery results to the type of local artifact a client needs. |
| Stdio adapter | Discovery-only local MCP protocol surface | Connect a compatible local client for metadata inspection only. |
| Contract validation | Deterministic MCP discovery shape checks | Confirm discovery responses follow the documented compatibility contract. |
| Discovery snapshots | Local MCP metadata state snapshots | Save and compare discovery metadata without remote services. |
| Compatibility reports | JSON and Markdown MCP change reports | Review discovery contract changes before updating an integration. |
| Safe error fixtures | Disabled and unknown response examples | Test client handling for unsupported execution, resources, and prompts. |
| MCP execution lockout | Protocol execution pathways remain disabled | MCP clients can discover metadata but cannot invoke Procore operations. |

## Phase 16A — Project Tools Read Coverage

| Feature | Technical description | Simple description |
|---|---|---|
| Project Tools listing | Read-only project tool metadata retrieval | See which tools are associated with a project without configuring them. |
| Project Tool details | Read-only individual tool metadata lookup | Inspect one supported tool record by identifier. |
| Project Tool search | Local name and identifier matching | Find tool metadata with familiar values after retrieving the read-only list. |
| Tool metadata exports | Local CSV and JSONL tool exports | Save Project Tool metadata for review or inventory work. |
| Tool CLI commands | Read-only Project Tools terminal interface | Inspect and export tool metadata from the command line. |
| Configuration lockout | No tool enablement or mutation methods | The SDK cannot enable, disable, configure, or execute project tools. |

## Phase 16B — Trusted Plugin Ecosystem Foundation

| Feature | Technical description | Simple description |
|---|---|---|
| Publisher metadata | Trusted publisher identity declaration fields | Record who claims to publish a local plugin manifest for human review. |
| Compatibility ranges | Minimum maximum PyProcore version metadata | Describe which PyProcore versions a plugin claims to support. |
| Capability categories | Policy-controlled local plugin capability declarations | Limit acceptable manifest capabilities to locally approved categories. |
| Safety declarations | Explicit plugin boundary metadata fields | Require manifests to state whether risky behaviors are requested. |
| Trust policies | JSON-only local allowlist policy models | Define allowed publishers, names, and capabilities in a reviewable local file. |
| Trust reports | JSON and Markdown policy finding reports | Explain why local metadata passes or fails a chosen trust policy. |
| Checksum metadata | Syntactic local checksum declaration validation | Validate checksum formatting without claiming remote artifact verification. |
| Signature metadata | Syntactic signature metadata validation only | Record signature-shaped metadata without claiming cryptographic trust. |
| Default denial | Execution import installation disabled defaults | Trust validation never installs, imports, or runs plugin code. |

## Phase 17A — OAS-backed Safe Endpoint Catalog

| Feature | Technical description | Simple description |
|---|---|---|
| Local OAS loading | User-provided local JSON OAS parsing | Inspect an OpenAPI file already on disk without downloading anything. |
| Endpoint inventory | Method path parameter catalog models | Turn local specification paths into a searchable endpoint list. |
| Method summaries | Endpoint counts grouped by HTTP method | Quickly understand how much of a local API description is read or write shaped. |
| Area summaries | Endpoint counts grouped by path area | See which Procore resource areas appear in the local specification. |
| Safety classification | Deterministic method and keyword risk rules | Separate likely reads from risky, write, and unknown endpoint candidates. |
| Coverage comparison | Catalog areas compared with SDK support | Identify areas already represented in PyProcore and possible read-only gaps. |
| Catalog reports | Local JSON and Markdown endpoint reports | Share catalog findings without generating or executing an API client. |
| Remote fetch lockout | Local paths accepted without network retrieval | The catalog never downloads OAS files or contacts Procore. |

## Phase 17B — Discovery Router Metadata Layer

| Feature | Technical description | Simple description |
|---|---|---|
| Capability search | Deterministic local capability text matching | Search for SDK capabilities using a practical intent such as overdue RFIs. |
| Route suggestions | Ranked metadata-only capability route candidates | Receive possible SDK routes with reasons, not executed actions. |
| Capability descriptions | Human-readable feature and safety summaries | Understand what a suggested capability does and what it cannot do. |
| OAS enrichment | Optional local catalog discovery context | Include candidates from a local OAS file without fetching remote data. |
| Discovery reports | Local JSON and Markdown routing reports | Save search and suggestion results for review or integration planning. |
| Execution lockout | Suggested routes never invoke SDK operations | Routing remains metadata-only and cannot call Procore or MCP tools. |

## Phase 17C — Integration Blueprint Layer

| Feature | Technical description | Simple description |
|---|---|---|
| Integration blueprints | Local architecture metadata template catalog | Review starter designs for common read-oriented integration patterns. |
| Sync worker blueprint | Read-only synchronization worker design template | Plan a worker that copies supported data into a system you control. |
| Webhook receiver blueprint | Local webhook receiver design template | Understand the pieces needed for a receiver without hosting one through PyProcore. |
| Read API blueprint | Internal read-only API design template | Plan a private read API around exported data without adding a server dependency. |
| Dashboard bridge blueprint | Local dashboard data bridge template | Outline how exported project records could feed an internal dashboard. |
| Sync run records | Local JSON and JSONL run metadata | Track planned or completed integration runs in simple local files. |
| Webhook fixtures | Sanitized local signature test helpers | Test webhook handling concepts locally without contacting Procore. |
| Readiness reports | Local configuration and path safety checks | Identify missing paths, environment settings, or secret-handling decisions. |
| Infrastructure lockout | No hosting scheduling database provisioning | Blueprints explain architecture but do not deploy or run infrastructure. |

## Phase 17D — Local Project Health Analytics Recipes

| Feature | Technical description | Simple description |
|---|---|---|
| Local data loaders | JSON JSONL CSV record ingestion | Analyze previously exported or sample records without calling Procore. |
| RFI aging risk | Deterministic local RFI aging heuristics | Highlight RFIs that may deserve attention based on locally available dates and status. |
| Submittal delay risk | Deterministic local submittal delay heuristics | Flag submittals whose local records suggest schedule review may be useful. |
| Change exposure | Deterministic local change record heuristics | Summarize locally exported change records that may need closer review. |
| Daily Log completeness | Deterministic local log completeness checks | Identify dates or categories with potentially incomplete local Daily Log data. |
| Combined health report | Multi-signal local project review summary | Bring available heuristic signals into one human-readable project review. |
| Analytics reports | Local JSON Markdown CSV outputs | Save deterministic findings in formats suitable for review and sharing. |
| Heuristic disclaimer | Scores are not predictive guarantees | Treat scores as review prompts, not automated decisions or certified outcomes. |

## Phase 17E — FastAPI Starter Template

| Feature | Technical description | Simple description |
|---|---|---|
| Starter metadata | Local FastAPI template description models | Inspect what the optional starter contains before copying it. |
| Dry-run planning | Non-writing local template copy preview | Review destination files and conflicts before anything is copied. |
| Safe template copy | Bounded local starter file copying | Copy a small read API starter into a chosen local directory. |
| Overwrite controls | Explicit local existing-file replacement safeguards | Avoid replacing local files unless the user deliberately allows it. |
| Read API example | Optional read-oriented FastAPI starter files | Start from a documented local skeleton for serving already available data. |
| Dependency isolation | FastAPI excluded from runtime dependencies | PyProcore users do not install FastAPI unless they choose to use the starter. |
| Runtime lockout | No automatic server or deployment execution | Copying the template never installs packages, starts servers, or hosts an app. |

## Phase 18A — Self-maintaining API Coverage Assistant

| Feature | Technical description | Simple description |
|---|---|---|
| OAS drift reports | Local specification endpoint change classification | Compare local specification files and see added, removed, or changed endpoints. |
| Coverage gap reports | Read-only candidates compared against SDK coverage | Identify local OAS areas that may merit future human-reviewed SDK support. |
| Maintenance plans | Prioritized local coverage maintenance recommendations | Turn catalog findings into a reviewable maintainer task list. |
| Safe scaffold planning | Read-only endpoint draft scaffold plans | Preview bounded service scaffolds only for likely read-only candidates. |
| Draft scaffold copying | Human-reviewed local read scaffold artifacts | Copy draft files for maintainer review without registering executable tools. |
| Risk exclusions | Write-shaped endpoints excluded from scaffolding | Prevent risky endpoint candidates from entering the read-only draft workflow. |
| Automation lockout | No commits PRs publishing or execution | The assistant produces local reports and drafts but performs no repository automation. |

## Phase 18B — Customer Codebase Impact Scanner

| Feature | Technical description | Simple description |
|---|---|---|
| Bounded folder scan | User-selected local source tree inspection | Inspect only the local folder a user explicitly selects. |
| Import detection | Python AST PyProcore import discovery | Find where a local codebase imports PyProcore without importing that customer code. |
| Call detection | Python AST SDK call discovery | Locate likely PyProcore calls for migration review. |
| CLI reference detection | Lexical local command usage scanning | Find `procore-sdk` command references in selected text files. |
| Capability mapping | Usage grouped by SDK capability family | Summarize which broad PyProcore areas a local project appears to use. |
| Drift correlation | Optional local OAS impact comparison | Relate detected usage to changes from user-provided local specifications. |
| Redacted reports | Sanitized JSON and Markdown impact output | Share possible-impact findings without exposing likely credential values. |
| Scanner lockout | No execution import editing or fetching | Scanning never runs customer code, changes files, or clones repositories. |

## Phase 18C — Migration Patch Planner

| Feature | Technical description | Simple description |
|---|---|---|
| Usage-specific planning | Local findings converted into migration suggestions | Turn scanner findings into conservative, relevant review steps. |
| Suggested diffs | Documentation-only non-applied local change previews | Show what a change might look like without editing customer files. |
| Review checklists | Human-owned migration verification task lists | Give maintainers a practical checklist before they make any change themselves. |
| Patch plan artifacts | Optional bounded local planning files | Save migration suggestions to a selected output directory for review. |
| Risk summaries | Conservative finding severity and rationale | Explain why a possible migration concern deserves attention. |
| Apply lockout | No patch git or repository mutation | Plans never apply changes, run git, or create commits and branches. |

## Phase 18D — Local PR Draft Pack

| Feature | Technical description | Simple description |
|---|---|---|
| Draft titles | Conservative local pull request titles | Suggest a concise title that a maintainer can edit before use. |
| Draft bodies | Human-review local change summary drafts | Prepare a possible PR description from local migration findings. |
| Review checklists | Local reviewer verification checklist generation | Include checks a human reviewer should complete before accepting a migration. |
| Test plans | Local safe verification plan generation | Suggest relevant local tests without running customer code or remote services. |
| Risk grouping | Findings organized by migration risk | Help reviewers focus first on the most consequential possible impacts. |
| Bounded artifacts | Optional local draft pack files | Write review materials only to an explicitly selected local output folder. |
| PR lockout | No GitHub API or git operations | Draft packs never open pull requests, push branches, or create commits. |

## Phase 18E — API Compatibility Contract Files

| Feature | Technical description | Simple description |
|---|---|---|
| Compatibility contracts | Deterministic local SDK capability declarations | Record supported families, local-only features, gaps, and safety boundaries. |
| Contract validation | Local schema and consistency checks | Catch incomplete or contradictory compatibility contract metadata. |
| Contract diffs | Deterministic local contract change comparison | See how declared support differs between two local contract files. |
| Codebase comparison | Local usage checked against contract declarations | Highlight customer usage that may fall outside a selected compatibility contract. |
| JSON and Markdown reports | Local compatibility report format rendering | Share machine-readable or human-readable compatibility findings. |
| Known-gap metadata | Explicit unsupported SDK capability declarations | Make limitations visible instead of implying broader support. |
| Certification disclaimer | Contracts do not certify production compatibility | Use contracts as review evidence, not as a production guarantee. |

## Phase 18F — Deprecation and Migration Guide Generator

| Feature | Technical description | Simple description |
|---|---|---|
| Deprecation guide reports | Local contract-based deprecation guide documentation | Turn compatibility contract changes into a readable guide for maintainers. |
| Usage-aware guidance | Optional local scan finding integration | Tailor migration notes to PyProcore usage detected in a selected local codebase. |
| Risk classification | Deterministic migration concern grouping rules | Group possible upgrade concerns so reviewers can prioritize them. |
| Upgrade checklists | Human-review local migration action checklists | Provide practical steps for a maintainer to evaluate and perform manually. |
| Verification steps | Local post-migration verification review instructions | Describe what humans should verify after making their own changes. |
| Safe test plans | Non-executing local migration validation recommendations | Suggest tests without running customer code or external services. |
| Bounded guide artifacts | Optional local JSON Markdown outputs | Save guides only to a user-selected local output location. |
| Migration lockout | No edits patches git or PRs | Guide generation never edits code, applies patches, creates commits, or opens pull requests. |

## Safety Summary

Every feature above preserves PyProcore's current safety posture. Procore write
actions remain unavailable, MCP remains discovery-only, and agent or Procore
tool execution remains disabled. AI examples do not call external models.
Plugin, OAS, discovery, analytics, integration, compatibility, and maintenance
features operate on explicit local inputs and produce local metadata, reports,
or copied templates. Human review remains required before using generated
maintenance guidance, scaffolds, migration suggestions, or PR draft text.
