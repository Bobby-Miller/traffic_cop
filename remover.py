import sqlite3
import config
import os
import json


def get_connection():
    return sqlite3.connect(config.DATABASE_NAME)


def get_node_by_path(data, path_parts):
    # path_parts is a list like ['root', 'children[0]', 'propConfig', 'props.instances']
    current = data
    for part in path_parts:
        if "[" in part and "]" in part:
            # Handle list index: children[0]
            name, index = part.split("[")
            index = int(index.replace("]", ""))
            current = current[name][index]
        else:
            current = current[part]
    return current


def remove_all_mods():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM audit_mods WHERE mod_type IN ("tag_transform", "query_transform")'
    )
    mods = cursor.fetchall()

    for mod in mods:
        # mod: (id, resource, binding, line, function, size, mod_type, original_data)
        mod_id, resource, binding, line, function, size, mod_type, original_data = mod

        print(f"Removing {mod_type} from {resource} at {binding}...")

        view_path = os.path.join(
            config.DESTINATION_PROJECT_PATH,
            "com.inductiveautomation.perspective",
            "views",
            resource,
            "view.json",
        )

        if os.path.exists(view_path):
            with open(view_path, "r") as f:
                data = json.load(f)

            # The binding path in DB is relative to view root
            # Convert binding path like 'root/children[0]/propConfig/props.instances'
            path_parts = binding.split("/")

            try:
                node = get_node_by_path(data, path_parts)
                # Restore original transforms
                node["transforms"] = json.loads(original_data)

                with open(view_path, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error restoring {resource}: {e}")

    conn.close()
    print("Removal complete.")


if __name__ == "__main__":
    remove_all_mods()
