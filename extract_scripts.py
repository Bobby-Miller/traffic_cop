import os
import json
import re

TARGET_FUNCTIONS = [
    "system.tag.readBlocking",
    "system.tag.writeBlocking",
    "system.tag.read",
    "system.tag.write",
]


def find_scripts(data, path=""):
    scripts = []
    if isinstance(data, dict):
        # Check for events
        if (
            "type" in data
            and data["type"] == "script"
            and "config" in data
            and isinstance(data["config"], dict)
            and "script" in data["config"]
        ):
            scripts.append((path, data["config"]["script"]))

        # Check for message handlers
        if "messageHandlers" in data and isinstance(data["messageHandlers"], list):
            for handler in data["messageHandlers"]:
                if "script" in handler:
                    scripts.append(
                        (
                            f"{path}/messageHandler/{handler.get('messageType', 'unknown')}",
                            handler["script"],
                        )
                    )

        # Check for custom methods
        if "customMethods" in data and isinstance(data["customMethods"], list):
            for method in data["customMethods"]:
                if "script" in method:
                    scripts.append(
                        (
                            f"{path}/customMethod/{method.get('name', 'unknown')}",
                            method["script"],
                        )
                    )

        # Recurse
        for key, value in data.items():
            new_path = f"{path}/{key}" if path else key
            scripts.extend(find_scripts(value, new_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            scripts.extend(find_scripts(item, f"{path}[{i}]"))
    return scripts


def process_projects(project_folders):
    extracted_base = "extracted_scripts"
    if not os.path.exists(extracted_base):
        os.makedirs(extracted_base)

    findings = []

    for project in project_folders:
        project_path = os.path.join(os.getcwd(), project)

        # 1. Perspective Resources
        perspective_path = os.path.join(
            project_path, "com.inductiveautomation.perspective", "views"
        )
        if os.path.exists(perspective_path):
            for root, dirs, files in os.walk(perspective_path):
                if "view.json" in files:
                    view_json_path = os.path.join(root, "view.json")
                    view_relative_path = os.path.relpath(root, perspective_path)

                    try:
                        with open(view_json_path, "r") as f:
                            view_data = json.load(f)

                        scripts = find_scripts(view_data)

                        for i, (script_path, script_content) in enumerate(scripts):
                            # Create a safe filename
                            safe_script_path = (
                                script_path.replace("/", "_")
                                .replace("[", "(")
                                .replace("]", ")")
                            )
                            filename = f"{safe_script_path}_{i}.py"

                            dest_dir = os.path.join(
                                extracted_base,
                                project,
                                "Perspective",
                                view_relative_path,
                            )
                            if not os.path.exists(dest_dir):
                                os.makedirs(dest_dir)

                            dest_file = os.path.join(dest_dir, filename)
                            with open(dest_file, "w") as f:
                                f.write(script_content)

                            # Check for target functions
                            found_funcs = [
                                func
                                for func in TARGET_FUNCTIONS
                                if func in script_content
                            ]
                            if found_funcs:
                                findings.append(
                                    {
                                        "project": project,
                                        "type": "Perspective",
                                        "view": view_relative_path,
                                        "script_path": script_path,
                                        "functions": found_funcs,
                                        "file": dest_file,
                                    }
                                )
                    except Exception as e:
                        print(f"Error processing {view_json_path}: {e}")

        # 2. Project Library Scripts
        script_python_path = os.path.join(project_path, "ignition", "script-python")
        if os.path.exists(script_python_path):
            for root, dirs, files in os.walk(script_python_path):
                for file in files:
                    if file.endswith(".py"):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, script_python_path)

                        try:
                            with open(file_path, "r") as f:
                                content = f.read()

                            found_funcs = [
                                func for func in TARGET_FUNCTIONS if func in content
                            ]
                            if found_funcs:
                                findings.append(
                                    {
                                        "project": project,
                                        "type": "ProjectLibrary",
                                        "view": os.path.dirname(relative_path),
                                        "script_path": file,
                                        "functions": found_funcs,
                                        "file": file_path,
                                    }
                                )
                        except Exception as e:
                            print(f"Error processing {file_path}: {e}")
    return findings


def main():
    projects = ["Global_full_2026-04-05_1403", "PureWest_full_export_2026-04-04_0720"]
    results = process_projects(projects)

    print("\nScripts using target system.tag functions:")
    print("==========================================")
    for res in results:
        print(f"Project: {res['project']}")
        print(f"Type:    {res['type']}")
        if res["type"] == "Perspective":
            print(f"View:    {res['view']}")
        else:
            print(f"Library: {res['view']}")
        print(f"Path:    {res['script_path']}")
        print(f"Funcs:   {', '.join(res['functions'])}")
        print(f"Source:  {res['file']}")
        print("-" * 40)


if __name__ == "__main__":
    main()
