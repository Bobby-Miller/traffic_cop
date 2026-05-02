import sqlite3

def generate_markdown_table(db_path):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Define columns to include (excluding 'original_data')
    columns = ['id', 'binding', 'function', 'line', 'mod_type', 'resource', 'size']
    query = f"SELECT {', '.join(columns)} FROM audit_mods"

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        # Create the Markdown header
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        
        markdown_lines = [header, separator]

        # Add data rows
        for row in rows:
            # Ensure all values are strings and handle None values
            formatted_row = "| " + " | ".join(str(item) if item is not None else "" for item in row) + " |"
            markdown_lines.append(formatted_row)

        # Join everything into a single string
        return "\n".join(markdown_lines)

    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        conn.close()

# Usage
if __name__ == "__main__":
    md_table = generate_markdown_table('pw_audit_mods.sqlite3')
    print(md_table)
    print('-'*150)
    md_table = generate_markdown_table('global_audit_mods.sqlite3')
    print(md_table)
