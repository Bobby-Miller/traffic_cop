import db_manager

# Audit log templates for script injection
SCRIPT_TAG_AUDIT_TEMPLATE = """
# Added by Audit Script
try:
    traffic_audit = system.util.getLogger("tag_resource_audit")
    # Ensure we only log the first argument as per design
    traffic_audit.trace("R|{Resource}, L|{Line}, F|{Function}, S|%d, P|%s" % (len({Variable}), session.custom.pageSelected))
except: pass
"""

SCRIPT_QUERY_AUDIT_TEMPLATE = """
# Added by Audit Script
try:
    traffic_audit = system.util.getLogger("query_resource_audit")
    traffic_audit.trace("R|{Resource}, L|{Line}, F|{Function}, S|%d, P|%s" % ({Variable}.getRowCount(), session.custom.pageSelected))
except: pass
"""

SCRIPT_QUERY_RETURN_AUDIT_TEMPLATE = """
# Added by Audit Script
try:
    traffic_audit = system.util.getLogger("query_resource_audit")
    # Recall the function to get size if returned directly
    traffic_audit.trace("R|{Resource}, L|{Line}, F|{Function}, S|%d, P|%s" % ({FunctionCall}.getRowCount(), session.custom.pageSelected))
except: pass
"""


def get_audit_block(
    resource_path,
    line_number,
    function_name,
    var_name=None,
    is_return=False,
    function_call=None,
):
    if "tag" in function_name:
        return SCRIPT_TAG_AUDIT_TEMPLATE.format(
            Resource=resource_path,
            Line=line_number,
            Function=function_name,
            Variable=var_name,
        )
    elif "db" in function_name:
        if is_return and function_call:
            return SCRIPT_QUERY_RETURN_AUDIT_TEMPLATE.format(
                Resource=resource_path,
                Line=line_number,
                Function=function_name,
                FunctionCall=function_call,
            )
        elif var_name and var_name != "None":
            return SCRIPT_QUERY_AUDIT_TEMPLATE.format(
                Resource=resource_path,
                Line=line_number,
                Function=function_name,
                Variable=var_name,
            )
    return ""


def log_injection(resource_path, line_number, function_name):
    db_manager.add_mod(
        resource_path,
        "N/A",
        line_number,
        function_name,
        "N/A",
        "script_transform",
    )
