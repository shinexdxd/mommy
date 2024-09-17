import sqlite3

def setup_database():
    conn = sqlite3.connect('data/bot_database.db')
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

    # Create Rewards Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards_log (
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

    # Create Reminders and Uptime Contexts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uptime_contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,  -- 'reminder' or 'uptime'
            context_name TEXT,  -- for uptimes
            message_id INTEGER,  -- for uptimes
            channel_id INTEGER,  -- for uptimes
            reminder_message TEXT,  -- for reminders
            user_id INTEGER NOT NULL, 
            target INTEGER, 
            created_at INTEGER, 
            reminder_time INTEGER, 
            frequency VARCHAR(20),  
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()