# -*- coding: utf-8 -*-

import logging, StringIO, time, hashlib
import psycopg2, psycopg2.pool
from contextlib import contextmanager
from kcaptcha import TextGenerator, FontLoad, Captcha

INSERT_IGNORE = '''INSERT INTO captcha (ctext, gendate, imghash, cimg)
SELECT %s, %s, %s, %s
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
	
	def __init__(self, dsn=None, conn_pool=None, fontdir='fonts/'):
		
		if dsn == conn_pool == None:
			raise Exception("No database connection specified")
		
		if dsn:
			try:
				self.dbconn = psycopg2.pool.ThreadedConnectionPool(1, 3, dsn)
			except:
				logging.error("UNABLE TO CONNECT TO DATABASE!")
				raise
		if conn_pool:
			self.dbconn = conn_pool
		
		self.fontdir = fontdir
	
	def inittable(self):
		for i in range(0, 4):
			try:
				with getcursor(self.dbconn, "INIT TABLE") as cur:
					cur.execute("CREATE TABLE IF NOT EXISTS captcha (ctext VARCHAR(8) PRIMARY KEY, gendate INTEGER, imghash VARCHAR(65), cimg BYTEA)")
			except psycopg2.InterfaceError:
				if i == 3:
					logging.error("DATABASE CONNECTION ERROR")
					raise
				continue
			break

	
	def updatecache(self, cacheregen=200, cachesize=400):
		get_font = FontLoad(self.fontdir)
		get_text = TextGenerator()
		captcha = Captcha(size=(120, 50))
		new_captchas = []
		
		for i in range(cacheregen):
			text = get_text()
			rndfont = get_font.randomfont()
			print text
			
			buf = StringIO.StringIO()
			img = captcha.create(text, rndfont)
			img.save(buf, format=self.imgformat)
			
			imgdig = hashlib.sha256()
			imgdig.update(buf.getvalue())
			imghash = imgdig.hexdigest()
			
			new_data = (text, int(time.time()), imghash, psycopg2.Binary(buf.getvalue()), text)
			new_captchas.append(new_data)
			buf.close()
		
		for i in range(0, 4):
			try:
				with getcursor(self.dbconn, "INSERT/IGNORE") as cur:
					cur.executemany(INSERT_IGNORE, new_captchas)
			except psycopg2.InterfaceError:
				if i == 3:
					logging.error("DATABASE CONNECTION ERROR")
					raise
				continue
			break
		
		for i in range(0, 4):
			try:
				with getcursor(self.dbconn, "DATABASE CLEANUP") as cur:
					cur.execute("DELETE FROM captcha WHERE ctext IN (SELECT ctext FROM captcha ORDER BY gendate DESC OFFSET (%s))", (cachesize,))
			except psycopg2.InterfaceError:
				if i == 3:
					logging.error("DATABASE CONNECTION ERROR")
					raise
				continue
			break


	def getcaptcha(self):
		data = None
		for i in range(0, 4):
			try:
				with getcursor(self.dbconn, "GET") as cur:
					cur.execute("SELECT imghash, cimg FROM captcha ORDER BY RANDOM() LIMIT 1")
					data = cur.fetchone()
			except psycopg2.InterfaceError:
				if i == 3:
					logging.error("DATABASE CONNECTION ERROR")
					raise
				continue
			break
		
		if not data:
			logging.error("No captchas in database cache!!!")
		return data
		
		
	def validate(self, input_text, img_hash):
		data = None
		for i in range(0, 4):
			try:
				with getcursor(self.dbconn, "VALIDATE") as cur:
					cur.execute("SELECT ctext FROM captcha WHERE ctext = %s AND imghash = %s", (input_text, img_hash))
					data = cur.fetchone()
			except psycopg2.InterfaceError:
				if i == 3:
					logging.error("DATABASE CONNECTION ERROR")
					raise
				continue
			break
		
		if not data:
			return False
		return True
