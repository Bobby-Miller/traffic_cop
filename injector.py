import json
import os
import db_manager
import config

# The audit log injection templates from the design doc
TAG_TRANSFORM_TEMPLATE = """
	try:  
		traffic_audit = system.util.getLogger("tag_resource_audit")  
		traffic_audit.trace("R|{Resource}, B|{Binding}, F|{Function}, S|%d, P|%s" % (1, session.custom.pageSelected))
	except: pass  
	return value  
"""

QUERY_TRANSFORM_TEMPLATE = """
	try:  
		traffic_audit = system.util.getLogger("query_resource_audit")  
		traffic_audit.trace("R|{Resource}, B|{Binding}, F|{Function}, S|%d, P|%s" % (value.getRowCount(), session.custom.pageSelected))
	except: pass  
	return value  
"""


def inject_tag_binding(node, resource_path):
    # node contains the full binding definition
    binding = node["node"]

    # 1. Check if already injected (avoid duplicates)
    # The design doc says "Add a new transform", so we need to inspect 'transforms' list
    transforms = binding.get("transforms", [])
    for t in transforms:
        if "code" in t and "tag_resource_audit" in t["code"]:
            return False  # Already injected

    # 2. Prepare the new transform
    new_transform = {
        "code": TAG_TRANSFORM_TEMPLATE.format(
            Resource=resource_path, Binding=node["path"], Function="read"
        ),
        "type": "script",
    }

    # 3. Add to transforms
    # Track the state BEFORE modification
    original_transforms = json.dumps(transforms)

    binding.setdefault("transforms", []).append(new_transform)

    # 4. Log to DB
    db_manager.add_mod(
        resource_path,
        node["path"],
        0,
        "read",
        "1",
        "tag_transform",
        original_data=original_transforms,
    )
    return True


def inject_query_binding(node, resource_path):
    binding = node["node"]

    transforms = binding.get("transforms", [])
    for t in transforms:
        if "code" in t and "query_resource_audit" in t["code"]:
            return False

    new_transform = {
        "code": QUERY_TRANSFORM_TEMPLATE.format(
            Resource=resource_path, Binding=node["path"], Function="read"
        ),
        "type": "script",
    }

    original_transforms = json.dumps(transforms)

    binding.setdefault("transforms", []).append(new_transform)

    db_manager.add_mod(
        resource_path,
        node["path"],
        0,
        "read",
        "N/A",
        "query_transform",
        original_data=original_transforms,
    )
    return True


def inject_query_binding(node, resource_path):
    binding = node["node"]

    transforms = binding.get("transforms", [])
    for t in transforms:
        if "code" in t and "query_resource_audit" in t["code"]:
            return False

    new_transform = {
        "code": QUERY_TRANSFORM_TEMPLATE.format(
            Resource=resource_path, Binding=node["path"], Function="read"
        ),
        "type": "script",
    }

    binding.setdefault("transforms", []).append(new_transform)

    db_manager.add_mod(resource_path, node["path"], 0, "read", "N/A", "query_transform")
    return True
