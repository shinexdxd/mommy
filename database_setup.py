import sqlite3

def setup_database():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()

    # Create Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0,
            petname TEXT
        )
    ''')

    # Create Tasks Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            points INTEGER,
            task TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Create Points Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS points_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            points INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    # Create Rewards Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            point_value INTEGER,
            consumable BOOLEAN DEFAULT 1,
            target_user_id INTEGER DEFAULT NULL,
            FOREIGN KEY (target_user_id) REFERENCES users (user_id)
        )
    ''')

    # Create Uptime Context Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uptime_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            context_name TEXT UNIQUE NOT NULL,
            message_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Reaction Roles Table (optional for future features)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reaction_roles (
            message_id INTEGER,
            emoji TEXT,
            role_id INTEGER,
            channel_id INTEGER,
            PRIMARY KEY (message_id, emoji)
        )
    ''')




    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
