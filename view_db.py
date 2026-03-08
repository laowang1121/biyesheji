# -*- coding: utf-8 -*-
"""查看数据库内容"""
import sqlite3
import sys

db_path = 'data/pc_config.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('表:', tables)
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    print(f'  {t}: {cur.fetchone()[0]} 条')
print()

# 用户
cur.execute('SELECT id, username, is_admin FROM users')
print('用户:', cur.fetchall())

# 示例：CPU
cur.execute('SELECT brand, model, price FROM cpus LIMIT 5')
print('CPU(前5条):', cur.fetchall())

conn.close()
