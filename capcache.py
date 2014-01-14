# -*- coding: utf-8 -*-

import sys, logging, StringIO, time
import psycopg2
from contextlib import contextmanager
from kcaptcha import TextGenerator, FontLoad, Captcha

INSERT_IGNORE = '''INSERT INTO captcha (ctext, gendate, cimg)
SELECT %s, %s, %s
WHERE NOT EXISTS (SELECT 1 FROM captcha WHERE ctext = %s)'''

@contextmanager
def getcursor(conn_pool, query_text):
	con = conn_pool.getconn()
	try:
		yield con.cursor()
	except:
		logging.error("DATABASE ERROR EXECUTING %s!", query_text)
		con.rollback()
	finally:
		con.commit()
		conn_pool.putconn(con)


class PsqlCaptcha(object):
	imgformat = 'jpeg'
	
	def __init__(self, dsn, fontdir='fonts/'):
		try:
			self.dbconn = psycopg2.pool.ThreadedConnectionPool(1, 4, dsn)
		except:
			logging.error("UNABLE TO CONNECT TO DATABASE, TERMINATING!")
			sys.exit(1)
		
		with getcursor(conn, "DATABASE CLEANUP") as cur:
			cur.execute("CREATE TABLE IF NOT EXISTS captcha (ctext VARCHAR(8) PRIMARY KEY, gendate INTEGER, cimg BYTEA)")
			
		self.fontdir = fontdir
	
	def fillcache(self, cacheregen=200, cachesize=400)
		get_font = FontLoad(self.fontdir)
		get_text = TextGenerator()
		captcha = Captcha(size=(120, 50))
		new_captchas = []
		
		for i in range(regen):
			text = get_text()
			rndfont = get_font.randomfont()
			print text
			
			buf = StringIO.StringIO()
			img = captcha.create(text, rndfont)
			img.save(buf, format=self.imgformat)
			new_data = (text, int(time.time()), psycopg2.Binary(buf.getvalue(), text)
		
		with getcursor(conn, "INSERT/IGNORE") as cur:
			cur.executemany(INSERT_IGNORE, data)
		
		with getcursor(conn, "DATABASE CLEANUP") as cur:
			cur.execute("DELETE FROM captcha WHERE ctext IN (SELECT ctext FROM captcha ORDER BY gendate DESC OFFSET (%s))", (cachesize,))
