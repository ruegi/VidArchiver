# -*- coding: utf-8 -*-

'''
vidarchdbStruct.py
Anbindung an vidarchdb ; zunächst nur struct
rg 01.2023
Anderungen:
    Version Datum       Inhalt
    ------- ----------  ------------------------------------------
    1.0     2023-01-29  erste Version; NUR MySql!
    1.1     2023-02-19  Erweiterung der Tabelle vainhalt: Felder modDateiTime, dateiLen, FP
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Text, Float, BIGINT
from sqlalchemy import and_
# from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

import os, os.path
import sys

DBVERSION = "1.1"
MODULVERSION = "1.1 vom 2023-02-19"

if sys.platform.lower() == "linux":
    ARCHIV = "/archiv/video"
else:
    ARCHIV = "y:\\video"

# mysql DB
from privat import DBZugang
# DBNAME = 'mysql://userid:psw@IP-Adr/DBName' # nur, um den Aufbau zu zeigen
DBNAME = DBZugang.DBNAME
SQLECHO = False

DB = create_engine(DBNAME, echo=SQLECHO, pool_pre_ping=True)
DBerror = ""
base = declarative_base()
Session = sessionmaker(bind=DB)

# DB Definitionen
class vainhalt(base):
    __tablename__ = 'vainhalt'

    id = Column(Integer, primary_key=True, autoincrement=True)    
    relPath = Column(Integer, ForeignKey("vapfad.id"), nullable=False)
    dateiName = Column(Text, nullable=False)
    dateiExt = Column(Text, nullable=True)
    md5 = Column(String(32), nullable=True)    # 5d65db39edca7fceb49fb9f978576fdb MD5 Summe des Films
    FP  = Column(String(32), nullable=True)    # 5d65db39edca7fceb49fb9f978576fdb FingerPrint der ersten 64 KB
    dateiLen = Column(BIGINT, nullable=True)
    modDateTime = Column(Float, nullable=True)
    UniqueConstraint(relPath, dateiName, name='uc_0')


    def __init__(self, relPath_id, dateiName, dateiExt, md5=None, FP=None, dateiLen=None, modDateTime=None):
        self.relPath = relPath_id
        self.dateiName = dateiName
        self.dateiExt = dateiExt
        self.md5 = md5
        self.FP = FP
        self.dateiLen = dateiLen
        self.modDateTime = modDateTime

class vapfad(base):
    __tablename__ = 'vapfad'

    id = Column(Integer, primary_key=True, autoincrement=True)    
    relPath = Column(String(240), nullable=False)
    UniqueConstraint('relPath', name='uc_1')

    def __init__(self, relPath):
        self.relPath = relPath

class vaconfig(base):
    __tablename__ = 'vaconfig'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(Text, nullable=False)
    value = Column(Text, nullable=True)
    UniqueConstraint('key', name='uc_0')
    def __init__(self, key, value):
        self.key = key
        self.value = value

 
def set_config(key, value):
    # legt eine neue Config an oder aktualisiert nur den Wert
    # und gibt die id zurück
    global DB
    
    if id := get_config(key) is None:
        
        with Session() as session:
            cnf = vaconfig(key, value)
            try:
                session.add(cnf)
                session.commit()
                id = cnf.id
            except:
                session.rollback()
    else:
        with Session() as session:
            try:
                q = session.query(vaconfig).filter(vaconfig.key == key)
                cnf = q.first()
            except SQLAlchemyError as e:
                error = str(e.orig)
                return None
            
            if cnf is None:
                return None
            else:
                id = cnf.id
                if not cnf.value == value:
                    # update des wertes
                    cnf.value = value
                    session.commit()
    # end 'with Session...'

    return id


def get_config(key: str):
    # gibt den in der Config gespeicherten Wert für den Parameter 'key' oder None zurück
    global DB

    with Session() as session:
        q = session.query(vaconfig).filter(vaconfig.key == key)
        cnf = q.first()
        if cnf is None:
            return None
        else:
            return cnf.value

    
'''
--------------------------------------------------------------------------------------------------------------
'''

if __name__ == "__main__":
    # print(set_config("DBVERSION", DBVERSION))
    # print(*(f"{film}\n" for film in findeFilmeInDB("wisting")))

    # Korrektur falscher relPath-Inhalte
    with Session() as session:
        q = session.query(vainhalt).\
            filter(vainhalt.relPath == 317)
        for inhalt in q:
            print(f"{inhalt.id}, {inhalt.dateiName}, relPath = {inhalt.relPath}")
            # inhalt.relPath = 351
        
        session.commit()  
    
    exit(0)
