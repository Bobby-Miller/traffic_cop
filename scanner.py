import os
import json
import db_manager
import config


def find_script_nodes(data, path=""):
    nodes = []
    if isinstance(data, dict):
        # 1. Scripts (Events, Message Handlers, Custom Methods)
        if (
            "type" in data
            and data["type"] == "script"
            and "config" in data
            and isinstance(data["config"], dict)
            and "script" in data["config"]
        ):
            nodes.append(
                {
                    "type": "script",
                    "path": path,
                    "content": data["config"]["script"],
                    "node": data["config"],
                }
            )

        if "messageHandlers" in data and isinstance(data["messageHandlers"], list):
            for handler in data["messageHandlers"]:
                if "script" in handler:
                    nodes.append(
                        {
                            "type": "script",
                            "path": f"{path}/messageHandler/{handler.get('messageType', 'unknown')}",
                            "content": handler["script"],
                            "node": handler,
                        }
                    )

        if "customMethods" in data and isinstance(data["customMethods"], list):
            for method in data["customMethods"]:
                if "script" in method:
                    nodes.append(
                        {
                            "type": "script",
                            "path": f"{path}/customMethod/{method.get('name', 'unknown')}",
                            "content": method["script"],
                            "node": method,
                        }
                    )

        # 2. Bindings (Tag, Query)
        if "propConfig" in data and isinstance(data["propConfig"], dict):
            for prop_path, config_val in data["propConfig"].items():
                if isinstance(config_val, dict) and "binding" in config_val:
                    binding = config_val["binding"]
                    binding_type = binding.get("type")
                    if binding_type == "tag":
                        nodes.append(
                            {
                                "type": "tag_binding",
                                "path": f"{path}/propConfig/{prop_path}",
                                "node": binding,
                            }
                        )
                    elif binding_type == "query":
                        nodes.append(
                            {
                                "type": "query_binding",
                                "path": f"{path}/propConfig/{prop_path}",
                                "node": binding,
                            }
                        )

        # Recurse
        for key, value in data.items():
            new_path = f"{path}/{key}" if path else key
            nodes.extend(find_script_nodes(value, new_path))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            nodes.extend(find_script_nodes(item, f"{path}[{i}]"))
    return nodes


def scan_project():
    project_path = os.path.join(os.getcwd(), config.SOURCE_PROJECT_PATH)
    perspective_path = os.path.join(
        project_path, "com.inductiveautomation.perspective", "views"
    )

    findings = []

    if os.path.exists(perspective_path):
        for root, dirs, files in os.walk(perspective_path):
            if "view.json" in files:
                view_json_path = os.path.join(root, "view.json")
                view_relative_path = os.path.relpath(root, perspective_path)

                try:
                    with open(view_json_path, "r") as f:
                        view_data = json.load(f)

                    nodes = find_script_nodes(view_data, view_relative_path)
                    for node in nodes:
                        findings.append(node)
                except Exception as e:
                    print(f"Error processing {view_json_path}: {e}")
    return findings


if __name__ == "__main__":
    db_manager.initialize_db()
    results = scan_project()
    for res in results:
        print(f"Found {res['type']} at {res['path']}")
