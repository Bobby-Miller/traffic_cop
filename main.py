import os
import json
import shutil
import config
import scanner
import injector
import script_main
import db_manager


def run_injection():
    # 1. Setup minimal project structure
    if os.path.exists(config.DESTINATION_PROJECT_PATH):
        shutil.rmtree(config.DESTINATION_PROJECT_PATH)

    os.makedirs(config.DESTINATION_PROJECT_PATH)

    # Copy essential project.json
    project_json_src = os.path.join(config.SOURCE_PROJECT_PATH, "project.json")
    if os.path.exists(project_json_src):
        shutil.copy2(
            project_json_src,
            os.path.join(config.DESTINATION_PROJECT_PATH, "project.json"),
        )

    # Copy required subdirectories
    required_subdirs = [
        os.path.join("com.inductiveautomation.perspective", "views"),
        os.path.join("ignition", "script-python"),
    ]

    for subdir in required_subdirs:
        src_dir = os.path.join(config.SOURCE_PROJECT_PATH, subdir)
        dest_dir = os.path.join(config.DESTINATION_PROJECT_PATH, subdir)
        if os.path.exists(src_dir):
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(src_dir, dest_dir)
            print(f"Copied: {subdir}")

    db_manager.initialize_db()

    # 2. Process Perspective (Bindings)
    project_path = os.path.abspath(config.DESTINATION_PROJECT_PATH)
    perspective_path = os.path.join(
        project_path, "com.inductiveautomation.perspective", "views"
    )

    if os.path.exists(perspective_path):
        for root, dirs, files in os.walk(perspective_path):
            if "view.json" in files:
                view_json_path = os.path.join(root, "view.json")
                view_relative_path = os.path.relpath(root, perspective_path)

                with open(view_json_path, "r") as f:
                    view_data = json.load(f)

                nodes = scanner.find_script_nodes(view_data, view_relative_path)

                changed = False
                for node in nodes:
                    if node["type"] == "tag_binding":
                        if injector.inject_tag_binding(node, view_relative_path):
                            changed = True
                    elif node["type"] == "query_binding":
                        if injector.inject_query_binding(node, view_relative_path):
                            changed = True

                if changed:
                    with open(view_json_path, "w") as f:
                        json.dump(view_data, f, indent=2)
                    print(f"Modified View: {view_relative_path}")

    # 3. Process Scripts (Ignition script-python)
    print("Processing Ignition scripts...")
    script_main.process_scripts()
    print("Injection complete.")


if __name__ == "__main__":
    run_injection()
