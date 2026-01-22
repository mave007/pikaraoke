import json
import logging
import os
import sqlite3


class PlayDatabase:
    def __init__(self, db_path="pikaraoke_plays.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with the current schema"""
        with sqlite3.connect(self.db_path) as conn:
            self._create_tables_if_needed(conn)
            conn.commit()

    def _create_tables_if_needed(self, conn):
        """Create database tables and indexes if they don't exist - CREATE tables/indexes"""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                canonical_name TEXT PRIMARY KEY
            )
        """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_aliases (
                alias TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                FOREIGN KEY (canonical_name) REFERENCES users (canonical_name)
            )
        """
        )

        # Create plays table if it doesn't exist
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                song TEXT NOT NULL,
                duration REAL,
                completed BOOLEAN DEFAULT 1,
                FOREIGN KEY (canonical_name) REFERENCES users (canonical_name)
            )
        """
        )

        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plays_canonical_name ON plays(canonical_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_plays_timestamp ON plays(timestamp)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_aliases_canonical_name ON user_aliases(canonical_name)"
        )

    def _resolve_canonical_user(self, user):
        """Resolve a user name to its canonical name, creating user if needed - READ/INSERT users table"""
        with sqlite3.connect(self.db_path) as conn:
            # Check if it's an alias
            cursor = conn.execute(
                "SELECT canonical_name FROM user_aliases WHERE alias = ?", (user,)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                # Not an alias, ensure user exists in users table
                conn.execute("INSERT OR IGNORE INTO users (canonical_name) VALUES (?)", (user,))
                return user

    def add_play(self, song, user, duration=None, completed=True):
        """Add a new play record to the database - INSERT into plays table"""
        # First, resolve the user to canonical name
        canonical_name = self._resolve_canonical_user(user)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO plays (timestamp, canonical_name, song, duration, completed) VALUES (datetime('now'), ?, ?, ?, ?)",
                (canonical_name, song, duration, completed),
            )
            conn.commit()

    def _build_filter_clause(self, user_filter=None, date_filter=None, table_prefix="p"):
        """Build WHERE clause and parameters for user/date filtering - UTILITY for query building"""
        conditions = []
        params = []

        if user_filter:
            canonical_user = self._resolve_canonical_user(user_filter)
            conditions.append(f"{table_prefix}.canonical_name = ?")
            params.append(canonical_user)

        if date_filter:
            conditions.append(f"date({table_prefix}.timestamp) = ?")
            params.append(date_filter)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params

    def populate_from_log(self, log_file_path):
        """Populate database from a JSON log file - BULK INSERT into plays table"""
        if not os.path.exists(log_file_path):
            logging.warning(f"Log file {log_file_path} does not exist")
            return

        with sqlite3.connect(self.db_path) as conn:
            # First, collect all unique users and resolve them
            users_to_resolve = set()
            entries_to_insert = []

            with open(log_file_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        user = entry.get("user", "").strip()
                        if not user:
                            continue
                        users_to_resolve.add(user)
                        entries_to_insert.append(entry)
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON in log: {line.strip()} - {e}")
                    except KeyError as e:
                        logging.error(f"Missing required field in log entry: {e}")

            # Resolve all users first
            user_map = {}
            for user in users_to_resolve:
                canonical_name = self._resolve_canonical_user(user)
                user_map[user] = canonical_name

            # Now insert all entries
            for entry in entries_to_insert:
                user = entry.get("user", "").strip()
                canonical_name = user_map[user]

                # Check if already exists to avoid duplicates
                cursor = conn.execute(
                    "SELECT id FROM plays WHERE timestamp = ? AND canonical_name = ? AND song = ?",
                    (entry["timestamp"], canonical_name, entry["song"]),
                )
                if not cursor.fetchone():
                    conn.execute(
                        "INSERT INTO plays (timestamp, canonical_name, song, duration, completed) VALUES (?, ?, ?, ?, 1)",
                        (
                            entry["timestamp"],
                            canonical_name,
                            entry["song"],
                            entry.get("duration", 0),
                        ),
                    )
            conn.commit()

    def get_top_songs(self, limit=10):
        """Get top songs by play count - READ from plays table with aggregation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT song, COUNT(*) as count
                FROM plays
                WHERE completed = 1
                GROUP BY song
                ORDER BY count DESC
                LIMIT ?
            """,
                (limit,),
            )
            return cursor.fetchall()

    def get_top_users(self, limit=10, offset=0, sort_by="count", sort_order="DESC"):
        """Get top users by play count with pagination and sorting - READ from plays/users tables with aggregation"""
        # Validate sort parameters
        if sort_by not in ["user", "count"]:
            sort_by = "count"
        if sort_order not in ["ASC", "DESC"]:
            sort_order = "DESC"

        # For user sorting, we need to sort by the canonical name
        if sort_by == "user":
            order_clause = f"ORDER BY u.canonical_name {sort_order}"
        else:
            order_clause = f"ORDER BY count {sort_order}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT u.canonical_name, COUNT(*) as count
                FROM plays p
                JOIN users u ON p.canonical_name = u.canonical_name
                WHERE p.completed = 1
                GROUP BY u.canonical_name
                {order_clause}
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )
            return cursor.fetchall()

    def get_top_users_count(self):
        """Get total count of users with plays - READ from plays table with aggregation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT canonical_name) FROM plays WHERE completed = 1"
            )
            return cursor.fetchone()[0]

    def get_last_plays(self, limit=10, offset=0, date_filter=None, user_filter=None):
        """Get recent plays with optional filtering - READ from plays table with filtering"""
        where_clause, params = self._build_filter_clause(user_filter, date_filter)

        query = f"""
                SELECT p.timestamp, p.canonical_name, p.song, p.completed
                FROM plays p
                {where_clause}
                ORDER BY p.timestamp DESC LIMIT ? OFFSET ?
            """
        params.extend([limit, offset])

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def get_plays_count(self, date_filter=None, user_filter=None):
        """Get total count of plays with optional filtering - READ from plays table with aggregation"""
        where_clause, params = self._build_filter_clause(user_filter, date_filter)

        query = f"SELECT COUNT(*) FROM plays p{where_clause}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]

    def update_play(self, play_id, user=None, song=None):
        """Update a play record - UPDATE plays table"""
        with sqlite3.connect(self.db_path) as conn:
            if user:
                # Resolve user to canonical name
                canonical_name = self._resolve_canonical_user(user)
                conn.execute(
                    "UPDATE plays SET canonical_name = ? WHERE id = ?", (canonical_name, play_id)
                )
            if song:
                conn.execute("UPDATE plays SET song = ? WHERE id = ?", (song, play_id))
            conn.commit()

    def set_user_alias(self, alias, canonical_user):
        """Create or update a user alias - INSERT/UPDATE user_aliases table"""
        with sqlite3.connect(self.db_path) as conn:
            # Ensure canonical user exists in users table
            conn.execute(
                "INSERT OR IGNORE INTO users (canonical_name) VALUES (?)", (canonical_user,)
            )

            conn.execute(
                "INSERT OR REPLACE INTO user_aliases (alias, canonical_name) VALUES (?, ?)",
                (alias, canonical_user),
            )
            conn.commit()

    def get_user_aliases(self):
        """Get all user aliases as (alias, canonical_name) tuples - READ from user_aliases table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT alias, canonical_name FROM user_aliases")
            return cursor.fetchall()

    def remove_user_alias(self, alias):
        """Remove a user alias - DELETE from user_aliases table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM user_aliases WHERE alias = ?", (alias,))
            conn.commit()

    def get_top_songs_by_period(self, period="day", limit=10):
        """Get top songs for a specific time period - READ from plays table with time filtering"""
        # period: 'day', 'month', 'year'
        if period == "day":
            date_func = "strftime('%Y-%m-%d', timestamp)"
            now = "strftime('%Y-%m-%d', 'now')"
        elif period == "month":
            date_func = "strftime('%Y-%m', timestamp)"
            now = "strftime('%Y-%m', 'now')"
        elif period == "year":
            date_func = "strftime('%Y', timestamp)"
            now = "strftime('%Y', 'now')"
        else:
            raise ValueError("Invalid period")
        query = f"""
            SELECT song, COUNT(*) as count
            FROM plays
            WHERE {date_func} = {now} AND completed = 1
            GROUP BY song
            ORDER BY count DESC
            LIMIT ?
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, (limit,))
            return cursor.fetchall()

    def _get_distinct_values(self, table, column, order_by=None):
        """Get distinct values from a table column (utility method) - READ from specified table"""
        order_clause = f" ORDER BY {order_by or column}"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"SELECT DISTINCT {column} FROM {table}{order_clause}")
            return [row[0] for row in cursor.fetchall()]

    def get_plays_by_user(self, user, date_filter=None):
        """Get all plays for a specific user, optionally filtered by date - READ from plays table with filtering"""
        # Resolve user to canonical name
        canonical_user = self._resolve_canonical_user(user) if user else None

        where_clause, params = self._build_filter_clause(canonical_user, date_filter)

        query = f"SELECT id, timestamp, canonical_name, song, completed FROM plays p{where_clause} ORDER BY p.timestamp DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def get_distinct_users(self):
        """Get all distinct users (canonical names and aliases) - READ from users/user_aliases tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Get all canonical users and aliases (special case - union of two tables)
            cursor = conn.execute(
                """
                SELECT canonical_name FROM users
                UNION
                SELECT alias FROM user_aliases
                ORDER BY 1
            """
            )
            return [row[0] for row in cursor.fetchall()]

    def get_distinct_dates(self):
        """Get all distinct dates when plays occurred - READ from plays table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT DISTINCT date(timestamp) as date FROM plays ORDER BY date DESC"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_distinct_songs(self):
        """Get all distinct songs that have been played - READ from plays table"""
        return self._get_distinct_values("plays", "song")
