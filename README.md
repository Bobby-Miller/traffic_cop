# Ignition Perspective Project Modifier & Auditor

## Overview

This application automates the process of injecting traceability and audit logging into an existing Ignition project. It scans the source project for specific functions (such as tag reads/writes and database queries), injects auditing wrappers around those calls, and outputs the modified files to a new destination folder. 

All modifications made during this process are logged to a SQLite database, ensuring full traceability of what was changed and preserving the original code.

**Note:** This application is configured to work exclusively with **Perspective** components and project-level Python scripts. It does *not* process or modify Vision windows or other unsupported module resources.

---

## Project Flow

The core workflow consists of reading an unzipped Ignition project, duplicating its relevant components to a destination directory, and performing targeted modifications on bindings and scripts.

### 1. Configuration
Before running the tool, you must configure the source and destination paths in `config.py`.
- `SOURCE_PROJECT_PATH`: The path pointing to your source, **unzipped** Ignition project folder. To function correctly, this unzipped folder must contain scripts (`ignition/script-python`) and Perspective components (`com.inductiveautomation.perspective/views`).
- `DESTINATION_PROJECT_PATH`: The output directory where the modified project files will be saved. The application will create this folder if it doesn't exist.
- `DATABASE_NAME`: The name of the SQLite database file (e.g., `audit_mods.sqlite3`) used to track all modifications.

### 2. Execution & Extraction
When you run `main.py`, the tool begins by creating the destination directory. It selectively copies only the essential project structure from the source:
- `project.json`
- `com.inductiveautomation.perspective/views`
- `ignition/script-python`

### 3. Scanning and Injection
Once the files are staged in the destination folder, the application performs two primary passes:
- **Perspective Views:** Recursively parses `view.json` files for Perspective views. It scans for script nodes, tag bindings, and query bindings, injecting modified structures where necessary.
- **Project Scripts:** Scans all `.py` files within the `ignition/script-python` library. It searches for specific target functions (e.g., `system.tag.readBlocking`, `system.db.runNamedQuery`) and modifies the code to wrap these calls with auditing logic.

### 4. SQLite Traceability Feature
For every injection or modification performed, the application logs a detailed record into the SQLite database specified in `config.py`. 
The `audit_mods` table tracks:
- The specific `resource` (script path or view path) that was modified.
- The `binding` or `function` targeted.
- The `line` number or `size` of the modification.
- The `mod_type` (indicating what kind of injection occurred).
- The `original_data` (the exact script content or binding configuration before it was changed).

This database serves as an exhaustive audit trail, giving you full visibility into the modifications and allowing you to reference the original logic if needed.

---

## How to Replicate in Your Environment

1. **Prepare Your Ignition Project:**
   - Export your project from the Ignition Gateway (`.zip` format).
   - Unzip the project archive into a folder on your local machine.
   - **Update**: Make sure to add a session custom property `pageSelected` to your project to capture the page which the logging is pointed to.

2. **Configure the Tool:**
   - Open `config.py`.
   - Set `SOURCE_PROJECT_PATH` to the path of your unzipped project folder.
   - Set `DESTINATION_PROJECT_PATH` to the desired output directory for the modified files.
   - Set `DATABASE_NAME` to your preferred SQLite file name.

3. **Run the Modifier:**
   - Execute the main script using Python 3:
     ```bash
     python main.py
     ```
   - The script will output its progress to the console, detailing which views and scripts are being processed.

4. **Review and Import:**
   - Open the generated SQLite database using any standard SQLite viewer to review the modifications.
   - The modified components in your `DESTINATION_PROJECT_PATH` can now be zipped back into a `.zip` archive (ensure `project.json` is at the root of the zip) or dropped directly into your development Gateway's `data/projects/` directory.
