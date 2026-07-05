"""
One-shot migration script.
Run once to bring an old conversations.db up to the current schema.
Safe to re-run — it skips columns that already exist.
"""
import sqlite3
import os

DB_PATH = os.path.join("data", "conversations.db")


def get_existing_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def add_column_if_missing(cursor, table, column, definition, existing_cols):
    if column not in existing_cols:
        print(f"  [+] Adding '{column}' to '{table}' ...")
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        return True
    else:
        print(f"  [=] '{column}' already exists in '{table}' — skipping.")
        return False


def main():
    if not os.path.exists(DB_PATH):
        print(f"[!] Database not found at {DB_PATH}. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── Show current tables ────────────────────────────────────────────────────
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"[*] Found tables: {tables}\n")

    # ── documents table ────────────────────────────────────────────────────────
    if "documents" in tables:
        print("[*] Checking 'documents' table ...")
        existing = get_existing_columns(cursor, "documents")
        print(f"    Existing columns: {existing}\n")

        migrations = [
            ("user_id",            "TEXT"),
            ("original_filename",  "TEXT"),
            ("file_type",          "TEXT"),
            ("file_size",          "INTEGER DEFAULT 0"),
            ("chunk_count",        "INTEGER DEFAULT 0"),
            ("page_count",         "INTEGER DEFAULT 0"),
            ("status",             "TEXT DEFAULT 'indexed'"),
            ("summary",            "TEXT"),
            ("metadata",           "TEXT"),   # file_metadata maps to 'metadata' column
        ]
        changed = False
        for col, defn in migrations:
            changed |= add_column_if_missing(cursor, "documents", col, defn, existing)

        if changed:
            conn.commit()
            print("\n[✓] 'documents' table migrated successfully.")
        else:
            print("\n[=] 'documents' table already up to date.")
    else:
        print("[!] 'documents' table not found — skipping (init_db will create it).")

    # ── conversations table ────────────────────────────────────────────────────
    if "conversations" in tables:
        print("\n[*] Checking 'conversations' table ...")
        existing = get_existing_columns(cursor, "conversations")
        print(f"    Existing columns: {existing}\n")

        migrations = [
            ("user_id",    "TEXT"),
            ("title",      "TEXT DEFAULT 'New Conversation'"),
            ("updated_at", "TEXT"),
        ]
        changed = False
        for col, defn in migrations:
            changed |= add_column_if_missing(cursor, "conversations", col, defn, existing)

        if changed:
            conn.commit()
            print("\n[✓] 'conversations' table migrated successfully.")
        else:
            print("\n[=] 'conversations' table already up to date.")

    # ── Final verification ─────────────────────────────────────────────────────
    print("\n[*] Final schema verification:")
    for table in ["documents", "conversations", "messages", "users"]:
        if table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cursor.fetchall()]
            print(f"    {table}: {cols}")

    conn.close()
    print("\n[✓] Migration complete. Restart uvicorn and the error should be gone.")


if __name__ == "__main__":
    main()
