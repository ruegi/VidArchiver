# -*- coding: utf-8 -*-

'''
vidarchdbStruct.py
Anbindung an vidarchdb ; zunächst nur struct
rg 01.2023
Anderungen:
    Version Datum       Inhalt
    ------- ----------  ------------------------------------------
    1.0     2023-01-29  erste Version; NUR MySql!
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Text
from sqlalchemy import and_
# from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

import os, os.path
# import hashlib
import sys
# import datetime
# from sameLinePrint import sameLinePrint

DBVERSION = "1.0"
MODULVERSION = "1.0 vom 2023-01-29"

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

def dbconnect(mustExist=True, SQLECHO=SQLECHO):
    '''
    Verbindet die DB und gibt True bei Erfolg zurück, sonst False
    opt. KeyWord-Parameter:
        db:         Pfad zur DB (default DBNAME)
        mustExist:  legt fest, ob die Bank schon vorhanden sein soll (default: True)
    '''
    global DBNAME, DB, DBerror
    if DB is None:
        if DBZugang.DBTyp == "mysql":
            try:            
                DB = create_engine(DBNAME, echo=SQLECHO, pool_pre_ping=True)
                return True
            except SQLAlchemyError as e:
                DBerror = str(e.orig)
                return False
        elif DBZugang.DBTyp == "sqlite":
            DBNAME = ARCHIV + "/vidarch.db"   # für sqlite nötig
            if mustExist:
                if not os.path.exists(DBNAME):
                    print(f"DB [{DBNAME}] pyhsisch nicht gefunden!")
                    return False
            try:            
                DB = create_engine('sqlite+pysqlite:///' + DBNAME, echo=SQLECHO, future=True,
                                            connect_args={'check_same_thread': False})                
                return True
            except SQLAlchemyError as e:
                DBerror = str(e.orig)                
                return False
        else:
            DBerror = f"Ungültiger DBTyp {DBZugang.DBTyp} - Abbruch!"
            return False
    else:
        return True

# DB Definitionen
class vainhalt(base):
    __tablename__ = 'vainhalt'

    id = Column(Integer, primary_key=True, autoincrement=True)    
    # relPath = Column(String(240), nullable=False)
    relPath = Column(Integer, ForeignKey("vapfad.id"), nullable=False)
    dateiName = Column(Text, nullable=False)
    dateiExt = Column(Text, nullable=True)
    md5 = Column(String(32), nullable=True)    # 5d65db39edca7fceb49fb9f978576fdb
    UniqueConstraint(relPath, dateiName, name='uc_0')

    def __init__(self, relPath_id, dateiName, dateiExt, md5):
        self.relPath = relPath_id
        self.dateiName = dateiName
        self.dateiExt = dateiExt
        self.md5 = md5

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




def erstelle_db(db=DBNAME, archiv=ARCHIV):
    global DB, base
    if not dbconnect(mustExist=False):
        return

    base.metadata.create_all(engine)

    with Session() as session:
        try:
            q = session.query(vaconfig).count()
            if q == 0:
                _ = set_config("VideoArchiv", archiv)
                _ = set_config("DBVERSION", DBVERSION)
        except SQLAlchemyError as e:
            DBerror = str(e.orig)            
            
    return

  
def film_merken(relPath, datei, ext, md5, verbose=False):
    '''
    speichert einen Film in der DB
    Parameter:
    relPath:    entweder ein String, des realtiven Pfades zum Film im Archiv
                oder die schon passende relPathId als Int
    datei:      Name der FilmDatei ohen Pfad
    ext:        Extension des Films
    md5:        None oder der MD5-Wert des Films
    verbose:    wenn True, werden mit print bzw.alertApp Ergebnisse des Jobs angezeigt; 
                default: True
    Returns:
                ein String, der mit "OK", "NEU", "UPD" oder "Err" beginnt
                nur "Err" stellt einen Fehler dar

    '''
    global DB
    if not dbconnect():
        return "Err: DB nicht verbunden"  

    result = None
    with Session() as session:

        retval = "OK >>> "
        if type(relPath) is int:
            path_id = relPath
        else:   # type ist String
            # erst den relPath anlegen, falls er nicht schon da ist
            path_id = anlage_relpath(session, relPath=relPath)

        # relPath + Datei sind zusammen unique; vorher prüfen!
        try:
            q = session.query(vainhalt).filter(and_(vainhalt.relPath == path_id, vainhalt.dateiName == datei))
            f = q.first()
        except SQLAlchemyError as e:
            error = str(e.orig)
            return f"Err: DB Fehler: {error}"

        if f is None:        
            if not md5:
                md5 = make_md5(os.path.join(ARCHIV, relPath, datei))
        if md5:
            # ggf. gibt es den md5 schon, dann war der Film nur per OS direkt renamed worden
            q = session.query(vainhalt).filter(and_(vainhalt.relPath == path_id, vainhalt.md5 == md5))
            f = q.first()
            if f is None: # Neuanlage mit vorhandener md5
                film = vainhalt(path_id, datei, ext, md5)
                session.add(film)
                session.commit()
                retval = "NEU >>> "
                if verbose:
                    print(f"  >>> OK! Film {relPath}\{datei} in der DB neu angelegt!")
            else: # nur Update des FilmNamens
                f.dateiName = datei
                session.commit()
                retval = "UPD >>> "
                if verbose:
                    print(f"  >>> OK! FilmName {relPath}\{datei} in der DB aktualisiert!")
        else:  # Film schon vorhanden, alles ok
            retval = "OK  >>> "
            if verbose:
                print(f"  >>> OK! Film {relPath}\{datei} in der DB gefunden!")

    # end 'with Session...'

    return retval

def set_config(key, value):
    # legt eine neue Config an oder aktualisiert nur den Wert
    # und gibt die id zurück
    global DB
    if not dbconnect():
        return None
    
    if get_config(key) is None:

        with Session() as session:
            cnf = vaconfig(key, value)
            try:
                session.add(cnf)
                session.commit()
                id = cnf.id
            except:
                session.rollback()
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
    if not dbconnect():
        return None    

    with Session() as session:
        q = session.query(vaconfig).filter(vaconfig.key == key)
        cnf = q.first()
        if cnf is None:
            return None
        else:
            return cnf.value


def anlage_relpath(relPath):
    # legt einen neuen relPath an
    # und gibt die id zurück    
    # relPath muss wirklich relativ zum ArchivPfad sein!
    global DB

    if not dbconnect():
        return None

    if "\\" in relPath:
        relp = relPath.replace("\\", "/")
    else:
        relp = relPath

    with Session() as session:
        q = session.query(vapfad).filter(vapfad.relPath == relp)
        pa = q.first()
        if pa is None:  # gibt es noch nicht
            pa = vapfad(relPath=relPath)
            try:
                session.add(pa)
                session.commit()
                id = pa.id
            except:     # hier sollte es nur bei einer race-condition hinkommen...
                session.rollback()
                id = None
        else:
            id = pa.id
    # end 'with session...'            
    return id


def filmIstInDerDB(ordner, film):
    '''
    prüft, ob ein Film in der DB ist
    Parameter:
        ordner:     entweder der (relative) Name (str) eines Ordners in dem Archiv
                    oder die PfadeId (int) des Ordners
        film:       Name des Films
    Returns:    True oder False
    '''

    
def findeFilmeInDB(film: str)-> list:
    '''
    findet alle Filme mit dem String 'film' in der DB
    Gibt eine Liste der gefundenen Filme oder 
    eine leere Liste (wenn nichts gewfunden wurde) oder 
    None bei Fehler zurück
    '''
    global DB, Session
    if not dbconnect(mustExist=True):        
        return None

    with Session() as session:
        try:
            result = session.query( vapfad.relPath, 
                                    vainhalt.dateiName, 
                                )\
                                .join(vapfad)\
                                .filter(vainhalt.dateiName.ilike("%"+film+"%"))\
                                .order_by(vapfad.relPath, vainhalt.dateiName)\
                                .all()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query meldet Fehler: {error}"
            return None
    
        liste = []
        for res in result:
            # vid = os.path.join(res.relPath, res.dateiName)
            vid = res.relPath +"/" + res.dateiName
            liste.append(vid)
    # end 'with Session...'

    return liste 


def _get_pfad_id(pfad, neuAnlage=False):
    # bestimmt die Pfad-Id eines Pfades und legt diese an,
    # wenn neuAnlage = True
    
    global DB, Session

    if not dbconnect():
        return None

    with Session() as session:
        try:
            qres = session.query(vapfad).filter(vapfad.relPath == pfad).first()
        except SQLAlchemyError as e:
            error = str(e.orig)            
            return None
        
        if neuAnlage and qres is None:
            return anlage_relpath(pfad)
        else:
            return qres.id


def getFilmMD5(relPfad: str, FilmName: str)->str:
    # ermittelt den gespeicherten MD5-Wert einen Filmes;
    # gibt den MD5-Wert bei Erfolg zurück
    # oder "", wenn nichts gefunden wurde,
    # oder none bei Connect-Fehler
    global DB, Session
    if not dbconnect():        
        return None

    with Session() as session:
        try:
            q = session.query(vainhalt.md5)\
                            .join(vapfad)\
                            .filter(and_(vapfad.relPath==relPfad, vainhalt.dateiName==FilmName) )\
                            .first()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query des Medien-Satzes meldet Fehler: {error}"
            return None

        if q is None:
            return ""
        else:
            return q.md5



if __name__ == "__main__":
    print()
    # print(*(f"{film}\n" for film in findeFilmeInDB("wisting")))

    # Korrektur falscher relPath-Inhalte
    with Session() as session:
        q = session.query(vainhalt).\
            filter(vainhalt.relPath == 374)
        for inhalt in q:
            print(f"{inhalt.id}, {inhalt.dateiName}, {inhalt.relPath}, => 351")
            inhalt.relPath = 351
        
        session.commit()  
    
    exit(0)
