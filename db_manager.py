import sqlite3
import config


def get_connection():
    return sqlite3.connect(config.DATABASE_NAME)


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Need to drop table to add column since I cannot easily alter it
    cursor.execute("DROP TABLE IF EXISTS audit_mods")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_mods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource TEXT NOT NULL,
            binding TEXT,
            line INTEGER,
            function TEXT,
            size TEXT,
            mod_type TEXT NOT NULL,
            original_data TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_mod(resource, binding, line, function, size, mod_type, original_data=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audit_mods (resource, binding, line, function, size, mod_type, original_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (resource, binding, line, function, size, mod_type, original_data),
    )
    conn.commit()
    conn.close()


def mod_exists(resource, binding, function, mod_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1 FROM audit_mods 
        WHERE resource = ? AND binding = ? AND function = ? AND mod_type = ?
    """,
        (resource, binding, function, mod_type),
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def remove_mod(resource, binding, function, mod_type):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM audit_mods 
        WHERE resource = ? AND binding = ? AND function = ? AND mod_type = ?
    """,
        (resource, binding, function, mod_type),
    )
    conn.commit()
    conn.close()
