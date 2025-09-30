import sqlite3
from config import db_name

def init_db():
    con = sqlite3.connect(db_name)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS movies (
        name TEXT,
        code INTEGER
        )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS channels (
        link TEXT,
        id INTEGER
        )""")
    con.commit() 
    con.close()

def new_movie(m_name, m_code):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("INSERT INTO movies (name, code) VALUES (?, ?)", (m_name, m_code))
        con.commit()
        con.close()
        return True
    except:
        return False

def new_channel(c_link, c_id):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("INSERT INTO channels (link, id) VALUES (?, ?)", (c_link, c_id))
        con.commit()
        con.close()
        return True
    except: 
        return False

def get_movie(code):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT name FROM movies WHERE code = ?", (code,))  # Исправлено: добавлена запятая
        result = cur.fetchone()
        con.close()
        return result[0] if result else None  # Исправлено: индексация
    except:
        return None

def get_channels():
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("SELECT link, id FROM channels")
        channels = cur.fetchall()
        con.close()
        return [{'link': row[0], 'id': row[1]} for row in channels]
    except:
        return []

def delete_anime(code):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("DELETE FROM movies WHERE code = ?", (code,))
        con.commit()
        deleted = cur.rowcount > 0
        con.close()
        return deleted
    except:
        return False

def delete_channel(channel_id):
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        cur.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
        con.commit()
        deleted = cur.rowcount > 0
        con.close()
        return deleted
    except:
        return False