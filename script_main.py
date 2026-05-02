import os
import re
import config
import script_injector
import db_manager

TARGET_FUNCTIONS = {
    "system.tag.readBlocking": "tag",
    "system.tag.writeBlocking": "tag",
    "system.tag.read": "tag",
    "system.tag.write": "tag",
    "system.db.runNamedQuery": "db",
    "system.db.runQuery": "db",
    "system.db.runPrepQuery": "db",
    "system.db.runScalarQuery": "db",
}


def get_indentation(line):
    match = re.match(r"^(\s*)", line)
    return match.group(1) if match else ""


def process_scripts():
    project_path = os.path.abspath(config.DESTINATION_PROJECT_PATH)
    script_python_path = os.path.join(project_path, "ignition", "script-python")

    if not os.path.exists(script_python_path):
        return

    for root, dirs, files in os.walk(script_python_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, script_python_path)

                with open(file_path, "r") as f:
                    lines = f.readlines()

                print(f"Processing: {file_path}")

                # Clean up previous injections
                cleaned_lines = []
                skip_block = False
                for line in lines:
                    if "# Added by Audit Script" in line.strip():
                        skip_block = True
                        continue
                    if skip_block:
                        if "except: pass" in line.strip():
                            skip_block = False
                        continue
                    cleaned_lines.append(line)
                # Remove extra blank lines
                final_lines = []
                for line in cleaned_lines:
                    if (
                        line.strip() == ""
                        and final_lines
                        and final_lines[-1].strip() == ""
                    ):
                        continue
                    final_lines.append(line)

                # Re-inject using multiline paren tracking
                result_lines = []
                i = 0
                while i < len(final_lines):
                    line = final_lines[i]
                    injected = False

                    for func, type in TARGET_FUNCTIONS.items():
                        if func in line:
                            start_line_index = i
                            full_call_lines = [line]
                            paren_balance = line.count("(") - line.count(")")

                            while paren_balance > 0 and i + 1 < len(final_lines):
                                i += 1
                                next_line = final_lines[i]
                                full_call_lines.append(next_line)
                                paren_balance += next_line.count("(") - next_line.count(
                                    ")"
                                )

                            indent = get_indentation(line)

                            is_return = "return" in line
                            var_name = None
                            function_call = None

                            block_str = "".join(full_call_lines)

                            # Extract variable or function call
                            # Helper to extract the argument passed to the function
                            def get_func_arg(full_block_str, func_name):
                                match = re.search(
                                    re.escape(func_name) + r"\s*\(([^,)]+)",
                                    full_block_str.replace("\n", " "),
                                )
                                return match.group(1).strip() if match else None

                            if type == "tag":
                                var_name = get_func_arg(block_str, func)
                            elif type == "db":
                                if is_return:
                                    match = re.search(
                                        r"return\s+.*?"
                                        + re.escape(func)
                                        + r"\((.*?)\)",
                                        block_str.replace("\n", " "),
                                    )
                                    if match:
                                        function_call = (
                                            func + "(" + match.group(1) + ")"
                                        )
                                else:
                                    # Check for variable assignment
                                    match = re.search(
                                        r"(\w+)\s*=\s*" + re.escape(func),
                                        block_str.replace("\n", " "),
                                    )
                                    if match:
                                        var_name = match.group(1)

                            audit_block = script_injector.get_audit_block(
                                relative_path,
                                start_line_index + 1,
                                func,
                                var_name,
                                is_return,
                                function_call,
                            )

                            lines_to_add = []
                            for l in audit_block.splitlines():
                                if l.strip():
                                    if l.strip().startswith(("#", "try:", "except:")):
                                        lines_to_add.append(indent + l.lstrip())
                                    else:
                                        lines_to_add.append(
                                            indent + "    " + l.lstrip()
                                        )

                            formatted_audit_block = "\n".join(lines_to_add) + "\n"

                            if is_return:
                                result_lines.append(formatted_audit_block)
                                result_lines.extend(full_call_lines)
                            else:
                                result_lines.extend(full_call_lines)
                                result_lines.append(formatted_audit_block)

                            script_injector.log_injection(
                                relative_path, start_line_index + 1, func
                            )
                            print(
                                f"Injected audit into: {relative_path} at line {start_line_index + 1}"
                            )
                            injected = True
                            break

                    if not injected:
                        result_lines.append(line)
                    i += 1

                with open(file_path, "w") as f:
                    f.writelines(result_lines)


if __name__ == "__main__":
    db_manager.initialize_db()
    process_scripts()
