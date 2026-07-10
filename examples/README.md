# PyProcore Examples

These examples are small, runnable scripts that show common PyProcore tasks.
They are meant for learning, testing your setup, and copying into your own
automation projects.

## Prerequisites

Before running the examples:

1. Install PyProcore.

   ```bash
   pip install pyprocore
   ```

2. Configure your `.env` file with Procore OAuth and API settings.

3. Complete OAuth once so PyProcore has a usable token store.

The examples require valid Procore credentials and access to the company,
project, RFI, or submittal you are trying to read.

## Environment Variables

IDs and lookup values can be supplied through environment variables:

```bash
export PROCORE_COMPANY_ID=your_company_id
export PROCORE_PROJECT_ID=your_project_id
export PROCORE_PROJECT_NAME="Project name"
export PROCORE_PROJECT_NUMBER="Project number"
export PROCORE_RFI_ID=your_rfi_id
export PROCORE_RFI_NUMBER=your_rfi_number
export PROCORE_RFI_STATUS=open
export PROCORE_SUBMITTAL_ID=your_submittal_id
export PROCORE_SUBMITTAL_NUMBER=your_submittal_number
export PROCORE_SUBMITTAL_STATUS=pending
export PROCORE_DOCUMENT_ID=your_document_id
export PROCORE_DOCUMENT_FOLDER_ID=your_document_folder_id
export PROCORE_DRAWING_ID=your_drawing_id
export PROCORE_DRAWING_AREA_ID=your_drawing_area_id
export PROCORE_DRAWING_DISCIPLINE_ID=your_drawing_discipline_id
export PROCORE_SPECIFICATION_SET_ID=your_specification_set_id
export PROCORE_SPECIFICATION_SECTION_ID=your_specification_section_id
export PROCORE_SPECIFICATION_REVISION_ID=your_specification_revision_id
export PROCORE_OUTPUT_DIR=downloads/examples
export PROCORE_DRY_RUN=1
export PROCORE_STATUS=open
```

Use placeholder values while learning. Do not commit real IDs, tokens, secrets,
or `.env` files.

## Running Examples

From the repository root:

```bash
python3 examples/01_list_companies.py
python3 examples/02_list_projects.py
python3 examples/05_get_rfi.py
python3 examples/13_client_interface.py
python3 examples/14_export_rfis_to_csv.py
python3 examples/18_incremental_sync.py
python3 examples/20_list_documents.py
python3 examples/23_list_drawings.py
python3 examples/26_list_specification_sections.py
```

Documents use Procore's Project Folders and Files endpoints internally. Before a
release or sandbox rollout, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-documents
```

Drawings support is first-class for list/get/find/download helpers. Procore
organizes drawings by drawing areas, so `PROCORE_DRAWING_AREA_ID` is useful when
you want to fetch or download one drawing directly. Before relying on downloads
in a new sandbox, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-drawings
```

Specifications use Procore's company/project-scoped V2 endpoints. Before
building automation around a new project, inspect the live payload shape with:

```bash
PROCORE_PROJECT_ID=352338 make smoke-specifications
```

Each script prints helpful messages when required environment variables are
missing.

## Keeping Examples Valid

Developers can check example syntax without running live Procore calls:

```bash
make examples-check
```

## Example Index

| File | Demonstrates |
| ---- | ------------ |
| `01_list_companies.py` | List companies available to the authenticated user |
| `02_list_projects.py` | List projects for `PROCORE_COMPANY_ID` |
| `03_find_project.py` | Find a project by name or number |
| `04_list_rfis.py` | List RFIs for `PROCORE_PROJECT_ID`, optionally filtered by `PROCORE_RFI_STATUS` |
| `05_get_rfi.py` | Fetch one RFI by ID |
| `06_download_rfi_attachments.py` | Download attachments from one RFI |
| `07_list_submittals.py` | List submittals for a project, optionally filtered by `PROCORE_SUBMITTAL_STATUS` |
| `08_get_submittal.py` | Fetch one submittal by ID |
| `09_download_submittal_attachments.py` | Download attachments from one submittal |
| `10_build_rfi_package.py` | Build an automation package for one RFI |
| `11_build_submittal_package.py` | Build an automation package for one submittal |
| `12_export_typed_model_json.py` | Export a typed model as JSON |
| `13_client_interface.py` | Use the object-oriented `Procore` client interface |
| `14_export_rfis_to_csv.py` | Export project RFIs to a CSV file |
| `15_export_submittals_to_csv.py` | Export project submittals to a CSV file |
| `16_sync_rfis_to_folder.py` | Sync project RFIs into local folders |
| `17_sync_submittals_to_folder.py` | Sync project submittals into local folders |
| `18_incremental_sync.py` | Run an incremental RFI sync with local state |
| `19_sync_project_to_folder.py` | Sync RFIs and submittals into one project folder |
| `20_list_documents.py` | List documents for a project or document folder |
| `21_download_document.py` | Download one document by ID |
| `22_sync_documents_to_folder.py` | Sync project documents into local folders |
| `23_list_drawings.py` | List drawings for a project, optionally filtered by drawing area or discipline |
| `24_download_drawing.py` | Download one drawing by ID and optional drawing area when Procore provides a direct URL |
| `25_list_specification_sets.py` | List specification sets for a project |
| `26_list_specification_sections.py` | List specification sections for a project, optionally filtered by set, area, or division |
| `27_get_specification_section.py` | Fetch one specification section by ID using the verified list endpoint |
| `28_list_specification_revisions.py` | List specification section revisions for a project or section |
| `29_download_specification_revision.py` | Download one specification section revision PDF |

## Safety Notes

- These scripts make live Procore API calls when you run them.
- Unit tests do not run these scripts against Procore.
- Keep secrets out of code, screenshots, logs, and issue reports.
