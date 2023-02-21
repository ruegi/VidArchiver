# -*- coding: utf-8 -*-

'''
vidarchdb.py
Erstellen / Pflegen der Video-Archiv-DB mittels sqlalchemy / sqlite
rg 05.2022
Anderungen:
    Version Datum       Inhalt
    ------- ----------  ------------------------------------------
    1.1     2022-11-27  alertApp Logik hinzugefügt
    1.2     2022-11-29  try except Logik bei den Queries zugefügt
                        für eine bessere Fehlerkontrolle
              aus: https://stackoverflow.com/questions/2136739/error-handling-in-sqlalchemy
    1.3     2022-12-02  Umstellung auf MySql
    1.4     2023-01-03  Behandlung des Fehlers "(2006, 'MySQL server has gone away')", 
                        wenn vidsuch die Nacht über geöffnet war (dann kamm es zum harten Absturz)
                        Lösung: der Parameter 'pool_pre_ping=True' im create_DB sowie
                        die Kapselung der Session durch den Kontext-Manger 
                        "with Session(bind=DB) as session:" in "getFilmListe"
    1.5     2023-01-27  - Function 'film_merken', Parameter 'relPath' wurde verallgemeinert:
                        der Parm akzeptiert jetzt entweder die PathId als int oder den relativen
                        Pfad als String
                        - in 'dbconnect' wird jetz nur noch die engine(DB) erzeugt; die globale Variable 
                        my_session wurde eliminiert. Eine Session wird nur noch lokal in jeder 
                        Funktion mittels 'with Session(bind=DB) as session:' erzeugt.
                        - die globale Variable conn wurde eliminiert; es wird überall mit ORM 
                        und damit mit 'session' gearbeitet
    1.6     2023-01-30  Säuberung des Codes;
    1.7     2023-02-12  Änderung des Feldes vainhalt.dateiName auf CaseInsensitive;
                        Dadurch kann auch Groß/Kleinschreibung in den Ordnernamen geändert werden
    2.0     2023-02-20  Überarbeitungen: -  Die DB Definitionen und Init der DB ausgelagert nach 
                                            vidarchdbstruct.py;
                                         - 'engine' in 'DB' umbenannt
                                         - die Funktion 'dbconnect' entfernt
                                         - Details in der Funktion db_san verbessert
                                         - die Felder FP, dateiLen und modDateTime der Tabelle vainhalt
                                           versorgt
'''

# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, ForeignKey, UniqueConstraint
# from sqlalchemy.sql.sqltypes import Integer, String, Text
# from sqlalchemy import and_
# from sqlalchemy import delete
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import SQLAlchemyError

# db-struktur & Init der DB importieren
from vidarchdbStruct import *

import os.path
from pathlib import Path
import hashlib
import sys
import datetime
from sameLinePrint import sameLinePrint
# from privat import DBZugang

# DBVERSION = "1.0"
# MODULVERSION = "1.6 vom 2023-01-30"
# DBNAME = "vidarch.db"
# ARCHIV = "v:\\video"

# if sys.platform.lower() == "linux":
#     ARCHIV = "/archiv/video"
# else:
#     ARCHIV = "y:/video"

# mysql DB
# DBNAME = 'mysql://userid:psw@IP-Adr/DBName'       # nur, um den Aufbau zu zeigen
            # für pool_pre_ping=True siehe:
            # https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
# DBNAME = DBZugang.DBNAME
# SQLECHO = False

# engine = None
# base = declarative_base()
# Session = sessionmaker()
# DBError  = ""   # ggf. für eine Fehlermeldung

# eine einfache Alert-Strategie:
# das einbindende Programm kann per 'defineAlert' eine eigene Alert-Routine zur Verfügung
# stellen, um Fehler, Hinweise und Warnungen auszugeben

def simpleAlert(txt: str):
    print(txt)
    return

def stummerAlarm(txt: str):
    # nix zu tun
    return

alertApp = simpleAlert

def defineAlert(alertFunc):
    global alertApp
    if alertFunc:   # alertApp > None oder alertApp > ""
        alertApp = alertFunc
    else:
        alertApp = stummerAlarm
    return
# -----------------------------------------------------------------------------

'''
# DB Definitionen
class vainhalt(base):
    __tablename__ = 'vainhalt'

    id = Column(Integer, primary_key=True, autoincrement=True)    
    # relPath = Column(String(240), nullable=False)
    relPath = Column(Integer, ForeignKey("vapfad.id"), nullable=False)
    # dateiName = Column(Text, dialects.mysql.VARCHAR(1024, collation='utf8_bin'), nullable=False)
    dateiName = Column(Text, nullable=False)
    dateiExt = Column(Text, nullable=True)
    md5 = Column(String(32), nullable=True)    # 5d65db39edca7fceb49fb9f978576fdb
    UniqueConstraint(relPath, dateiName, name='uc_0')

    def __init__(self, relPath_id, dateiName, dateiExt, md5):
        self.relPath = relPath_id
        self.dateiName = dateiName
        self.dateiExt = dateiExt
        self.md5 = md5

    def __str__(self) -> str:
        return f"{self.relPath =}\n{self.dateiName}\n{self.md5}"

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


def defineDBName(db: str):
    # setzt den Namen der zu nutzenden DB
    # jetzt: veraltet
    # global DBNAME
    # DBNAME=db
    return


def dbconnect(mustExist=True, SQLECHO=SQLECHO):    
    # Verbindet die DB und gibt True bei Erfolg zurück, sonst False
    # opt. KeyWord-Parameter:
    #     db:         Pfad zur DB (default DBNAME)
    #     mustExist:  legt fest, ob die Bank schon vorhanden sein soll (default: True)
    
    global DBNAME, DB
    dtJetzt = datetime.datetime.now()
    if DB is None:
        if DBZugang.DBTyp == "mysql":
            try:            
                DB = create_engine(DBNAME, echo=SQLECHO, pool_pre_ping=True)
                return True
            except SQLAlchemyError as e:
                error = str(e.orig)
                alertApp(f"Exception bei DB connect:\n{error}")
                return False
        elif DBZugang.DBTyp == "sqlite":
            DBNAME = os.path.join(ARCHIV, "vidarch.db")   # für sqlite nötig
            if mustExist:
                if not os.path.exists(DBNAME):                    
                    alertApp(f"DB [{DBNAME}] pyhsisch nicht gefunden!")
                    return False
            try:            
                DB = create_engine('sqlite+pysqlite:///' + DBNAME, echo=SQLECHO, future=True,
                                            connect_args={'check_same_thread': False})                
                return True
            except SQLAlchemyError as e:
                error = str(e.orig)
                alertApp(f"Exception bei DB connect:\n{error}")
                return False
        else:
            alertApp(f"Ungültiger DBTyp {DBZugang.DBTyp} - Abbruch!")
            return False
    else:
        return True

def dbClose():
    # erfolgt implizt
    pass

def erstelle_db(db=DBNAME, archiv=ARCHIV):
    global DB, Session, base
    if not dbconnect(mustExist=False):
        return

    base.metadata.create_all(DB)

    with Session(bind=DB) as DB:
        try:
            q = session.query(vaconfig).count()
            if q == 0:
                _ = set_config("VideoArchiv", archiv)
                _ = set_config("DBVERSION", DBVERSION)
        except SQLAlchemyError as e:
            error = str(e.orig)
            alertApp(f"Query meldet Fehler: {error}")
            
    return

'''

# -----------------------------------------------------------------------------------------------------------------------
# Utilities für die Verwaltung der DB
# -----------------------------------------------------------------------------------------------------------------------
def film_merken(relPath, datei, ext, md5, FP=None, Bytes=0, ModZeit=None, verbose=True):
    '''
    speichert einen Film in der DB
    Parameter:
    relPath:    entweder ein String, des relativen Pfades zum Film im Archiv
                oder die schon passende relPathId als Int
    datei:      Name der FilmDatei ohen Pfad
    ext:        Extension des Films
    md5:        None oder der MD5-Wert des Films
    Optional:
    FP=         den Fingerprint des Films; default None
    Bytes=      die DateiLänge in Bytes; default 0
    ModZeit=    der ZeitStempel st_mtime der Datei; default None
    verbose:    wenn True, werden mit print bzw. alertApp Ergebnisse des Jobs angezeigt; 
                default: True
    Returns:
                ein String, der mit "OK", "NEU", "UPD" oder "Err" beginnt
                nur "Err" stellt einen Fehler dar

    '''
    global DB, Session

    if type(relPath) is int:
        # absRelPath suchen
        relPathId = relPath
        with Session(bind=DB) as session:
            try:
                q0 = session.query(vapfad).get(relPathId)
                relAbsPath = q0.relPath            
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"Query nach [vapath] meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"
    else:   # type is str
        relAbsPath = relPath
        with Session(bind=DB) as session:
            try:
                qa = session.query(vapfad).filter(vapfad.relPath == relPath).first()
                relPathId = qa.id
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"Query nach [vapath] meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"
    # end if type ...
            
    absPath = os.path.join(ARCHIV, relAbsPath, datei)
    p_datei = Path(absPath)
    if not p_datei.exists():
        alertApp(f"Datei [{absPath}] nicht gefunden!")
        return f"Datei [{absPath}] nicht gefunden!"
    else:        
        p_datei_st = p_datei.stat()
        dateiLen = p_datei_st.st_size
        mDat = p_datei_st.st_mtime

    if not FP:
        FP = make_FP(absPath)

    # md5 = None  # noch nicht belegt

    result = None
    vaid = None # id eines gefundene vainhalt Satzes

    with Session(bind=DB) as session:
        retval = "OK >>> "
        # if type(relPath) is int:
        #     path_id = relPath
        # else:   # type ist String
        #     # erst den relPath anlegen, falls er nicht schon da ist
        #     relPathId = anlage_relpath(session, relPath=relPath)
        # relPath + Datei sind zusammen unique; vorher prüfen!
        # zunächst nach Pfad und DateiName suchen
        try:
            q = session.query(vainhalt).filter(and_(vainhalt.relPath == relPathId, vainhalt.dateiName == datei))
            f = q.first()
            if f:
                vaid = f.id
        except SQLAlchemyError as e:
            error = str(e.orig)
            if verbose:
                alertApp(f"Query meldet Fehler: {error}")
            return f"Err: DB Fehler: {error}"

        if vaid is None:
            # noch mittels FP suchen...
            try:
                q2 = session.query(vainhalt).filter(vainhalt.FP == FP)
                f = q2.first()
                if f:
                    vaid = f.id
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"Query meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"
        if vaid is None:
            # mittels md5 suchen ...
            if not md5:
                md5 = make_md5(absPath)
            try:
                q3 = session.query(vainhalt).filter(vainhalt.md5 == md5)
                f = q3.first()
                if f:
                    vaid = f.id
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"Query meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"

        if vaid: # Update
            if f.md5 is None and md5 is None:
                md5 = make_md5(absPath)
                f.md5 = md5

            try:
                satz = session.query(vainhalt).get(vaid)
                if satz.md5 is None and md5 is None:
                    md5 = make_md5(absPath)
                    satz.md5 = md5
                satz.relPath = relPathId
                satz.dateiName = datei
                satz.ext = ext
                satz.FP = FP
                session.commit()
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"Update meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"
        else:
            # wirklich nichts da...
            # alertApp("Film nicht in der DB gefunden! " + f"relPathId={relPathId}; " +  f"name={datei}" )
            # neuAnlage vorbereiten
            vainhalt_satz = vainhalt(relPathId, datei, ext, md5=md5, FP=FP, dateiLen=dateiLen, modDateTime=mDat )
            try:
                session.add(vainhalt_satz)
                session.commit()
                retval = "NEU >>> "
                if verbose:
                    alertApp(f"  >>> OK! Film {relPath};{datei} in der DB neu angelegt!")
                return retval
            except SQLAlchemyError as e:
                error = str(e.orig)
                if verbose:
                    alertApp(f"NeuAnlage meldet Fehler: {error}")
                return f"Err: DB Fehler: {error}"
        # end if vaid
    # end 

    return retval


def set_config(key, value):
    # legt eine neue Config an oder aktualisiert nur den Wert
    # und gibt die id zurück
    global DB, Session
    
    id = None

    if get_config(key) is None:

        with Session(bind=DB) as session:
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
            alertApp(f"Query meldet Fehler: {error}")
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
    global DB, Session

    with Session(bind=DB) as session:
        q = session.query(vaconfig).filter(vaconfig.key == key)
        cnf = q.first()
        if cnf is None:
            return None
        else:
            return cnf.value

def finde_relPath(relPath):
    # sucht den relPath in vapath und gibt die id oder None zurück
    if "\\" in relPath:
        relp = relPath.replace("\\", "/")
    else:
        relp = relPath

    with Session(bind=DB) as session:
        try:
            q = session.query(vapfad).filter(vapfad.relPath == relp)
            pa = q.first()
            if pa is None:  # gibt es noch nicht
                return None
            else:
                return pa.id
        except SQLAlchemyError as e:     # hier sollte es nie hinkommen...
            DBError = str(e.orig)
            return None            
    # end 'with session...'            



def anlage_relpath(session, relPath):
    # legt einen neuen relPath an
    # und gibt die id zurück
    # --> session ist veraltet
    # sonst wird session verwendet
    # relPath muss wirklich relativ zum ArchivPfad sein!
    global DB, Session

    if "\\" in relPath:
        relp = relPath.replace("\\", "/")
    else:
        relp = relPath

    with Session(bind=DB) as session:
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


def rename_relpath(oldRelPath, newRelPath):
    # umbenennen der alten relPath-Sätze
    # und gibt True beu Erfolg zurück
    # relPath muss wirklich relativ zum ArchivPfad sein!
    global DB

    #  in der DB wird nur "/" als Verzeichnistrenner gespeichert
    if "\\" in newRelPath:
        newRelp = newRelPath.replace("\\", "/")
    else:
        newRelp = newRelPath

    if "\\" in oldRelPath:
        oldRelp = oldRelPath.replace("\\", "/")
    else:
        oldRelp = oldRelPath

    ok = False
    oLen = len(oldRelp)
    with Session(bind=DB) as session:
        try:
            # alle Pfadeinträge nehmen, die mit 'oldRelp' beginnen
            q = session.query(vapfad).filter(vapfad.relPath.ilike(oldRelp+"%"))
            if q is None:  # gibt es nicht
                DBError = f"Kein Eintrag mit {oldRelp} gefunden!"
                return None
            # alle betroffenen Sätze updaten    
            for pa in q:                
                id = pa.id
                # print(id, pa.relPath, "==>", end="")
                pa.relPath = newRelp + pa.relPath[oLen:]
                # print(pa.relPath)
                
            session.commit()
            ok = True

        except SQLAlchemyError as e:     # hier sollte es nie hinkommen...
            DBError = str(e.orig)
            session.rollback()
            id = None
    # end 'with session...'
    return ok


def delete_relpath(relPath, Test=True):
    # löscht einen relPath, wenn er leer ist und Test=False
    # gibt beit Erfolg True zurück, sonst False
    # und füllt dann den DBError
    global DB, Session

    #  in der DB wird nur "/" als Verzeichnistrenner gespeichert
    if "\\" in relPath:
        relPath = relPath.replace("\\", "/")
    pathId = finde_relPath(relPath)
    if not pathId:
        DBError = f"der Ordner {relPath} konnte nicht in der DB gefunden werden!"
        return False

    ok = False
    with Session(bind=DB) as session:
        try:
            qx = session.query(vainhalt).filter(vainhalt.relPath == id)
            if qx is None:
                if Test:
                    return True
                else:
                    # jetzt kann gelöscht werden
                    qo = session.get(vapfad, pathId)
                    session.delete(qo)
                    session.commit()
                    return True
        except SQLAlchemyError as e:
            DBError = str(e.orig)
            session.rollback()
            return False
    # end 'with session...'


def export_CSV(name="vidarch.csv"):    
    global DB, Session

    with Session(bind=DB) as session:
        try:
            q = session.query(vapfad.relPath, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5).join(vapfad).all()
        except SQLAlchemyError as e:
            error = str(e.orig)
            alertApp(f"Sorry! kein Export möglich! Query meldet Fehler: {error}")
            return
        with open(name, "w", encoding="UTF-8") as f:        
            print("relPath;Datei;Ext;MD5", file=f)
            for erg in q:
                print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}", file=f)
                print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}")
        # session.rollback()
    # end 'with Session...'


def db_scan(Pfad=None, exportDel=""):
    '''
    db_scan
    Prüft, ob alle Medien, die in der DB sind, sich auch im Archiv befinden.
    Wenn nicht, wird der DB-Eintrg gelöscht
    Parameter:
        Pfad:   relativer Pfad unterhalb des Archiv oder None, wenn das gesamte Archiv 
                durchlaufen werden soll
        exportDel="" wird hier ein Dateiname angegeben, werden die aus der DB gelöschten Sätze
                        in diese Datei exportiert
    Returns:
        string mit FehlerText oder leerer String bei Erfolg
    '''
    global DB, Session
    exportiert = False

    with Session(bind=DB) as session:
        try:
            if Pfad is None:
                q = session.query(vapfad.id, vapfad.relPath, vainhalt.id, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5)\
                    .join(vainhalt, vapfad.id == vainhalt.relPath )\
                    .group_by(vapfad.id, vainhalt.dateiName)\
                    .all()
            else:
                Pfad = Pfad.replace("\\", "/")
                q = session.query(vapfad.id, vapfad.relPath, vainhalt.id, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5)\
                                .join(vapfad)\
                                .filter(vapfad.relPath.startswith(Pfad))\
                                .order_by(vainhalt.dateiName)\
                                .all()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"DB-Scan kann nicht laufen! Query meldet Fehler: {error}"
            alertApp(x)
            return x    

        anzD = 0
        anz = 0
        aktOId = 0
        for res in q:
            film = os.path.join(ARCHIV, res[vapfad.relPath], res[vainhalt.dateiName])   
            # print(f"{film =}")         
            # Gruppenwechsel erkennen
            currOId = res[vapfad.id]
            if not currOId == aktOId:
                if aktOId:   # meint aktOId > 0
                    sameLinePrint(f"    --- {anzD} Medien im Ordner [{res[vapfad.relPath]}]")
                    print("")
                    anzD = 0
                    aktOId = currOId
        
            if os.path.exists(film):
                sameLinePrint(f"OK! Film [{film}]")
            else:
                # Film löschen aus DB
                try:
                    id = res[vainhalt.id]
                    if exportDel:
                        if not os.path.exists(exportDel):
                            with open(exportDel, "w") as f:
                                print(f"id;relPath;dateiName,dateiExt;md5", file=f)                                
                        with open(exportDel, "a") as f:
                            print(f"{id};{res[vapfad.relPath]};{res.dateiName};{res.dateiExt};{res.md5}")
                    x = session.query(vainhalt).get(id)
                    session.delete(x)
                    session.commit()
                except SQLAlchemyError as e:
                    error = str(e.orig)
                    x = f"DB_scan: Löschung des DB-Satzes misslungen!\n{error}"
                    alertApp(x)
                    return x

                sameLinePrint(f" >>> Film [{film}] wurde aus der DB gelöscht!")

                anz +=1
                anzD +=1
            # end if - else
        # end for res ...
    # with 'Session = ...'
    #                 
    sameLinePrint(f"Ende DBScan!")
    print("")
    return ""

def filmIstInDerDB(ordner, film):
    '''
    prüft, ob ein Film in der DB ist
    Parameter:
        ordner:     entweder der (relative) Name (str) eines Ordners in dem Archiv
                    oder die PfadeId (int) des Ordners
        film:       Name des Films
    Returns:    True oder False
    '''
    global DB
    
    if type(ordner) is int:
        oid = ordner
    else:   # ordner ist str
        oid = _get_pfad_id(ordner, verbose=False, neuAnlage=False)
        if not oid:
            return False
    
    with Session(bind=DB) as session:
        try:
            exists = session.query(vainhalt.id).filter(and_(vainhalt.relPath == oid, vainhalt.dateiName == film)).first() is not None
        except SQLAlchemyError as e:
            error = str(e.orig)
            exists = False
    return exists



def istSchonDa(film: str)-> list:
    global DB, Session

    with Session(bind=DB) as session:
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
            alertApp(x)
            return None
    
        anz = 0    
        liste = []
        for res in result:
            vid = vid = os.path.join(res.relPath, res.dateiName)
            liste.append(vid)
    # end 'with Session...'

    return liste 


def film_umbenennen(alterName, neuerName):
    '''
        benennt den Film in der DB um und/oder verschiebt ihn in einen anderen Ordner
        gibt bei Erfolg True, sonst False zurück
        Parms:
            alterName:  
            neuerName:
    '''
    # Volle Dateinamen mit pfaden!
    global DB, Session

    # zuerst die quell- und Zielpfade bestimmen
    qhead, qtail = os.path.split(alterName)
    zhead, ztail = os.path.split(neuerName)
    quellOrdner = qhead[len(ARCHIV)+1:].replace("\\","/")     # den ARCHIV Teilstring abtrennen
    zielOrdner  = zhead[len(ARCHIV)+1:].replace("\\","/")

    # dann die id der Pfade bestimmen
    qid = _get_pfad_id(quellOrdner)
    if quellOrdner == zielOrdner:
        zid = qid
    else:
        zid = _get_pfad_id(zielOrdner)
    
    # print(zid, qid)

    with Session(bind=DB) as session:
        # prüfen, ob es das Ziel bereits in der DB gibt
        gibts_Nicht = True
        try:
            # print(f"{qtail =}\n{ztail =}")
            q = session.query(vainhalt).filter(and_(vainhalt.relPath==zid, vainhalt.dateiName==ztail))
            if q.count() == 0:
                # print("Query ist leer!")
                pass
            else:                
                for satz in q:
                    # print(str(satz))       
                    if satz.dateiName == ztail:  # dieser Vergleich ist nötig, weil die query case-insensitive ist
                        gibts_Nicht = False
                        break            
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query, ob Ziel existiert, meldet Fehler: {error}"
            alertApp(x)
            return False
    # ende with session (suche)

    if gibts_Nicht: # gibt es noch nicht, also los
        gefunden = False        
        with Session(bind=DB) as session:
            try:    # zunächst den alten Satz suchen                
                q1 = session.query(vainhalt).filter(and_(vainhalt.relPath==qid, vainhalt.dateiName==qtail))
                for res in q1:
                    if res.dateiName == qtail:
                        # dieser Satz muss geändert werden
                        try:
                            res.relPath = zid
                            res.dateiName = ztail
                            session.commit()
                            gefunden = True
                            break
                        except SQLAlchemyError as e:
                            error = str(e.orig)
                            x = f"Update des DB-Satzes, meldet Fehler: {error}"
                            alertApp(x)
                            return False            
                # end for res ...
                return gefunden

            except SQLAlchemyError as e:
                error = str(e.orig)
                x = f"Query, ob Quelle existiert, meldet Fehler: {error}"
                alertApp(x)
                return False
        # end with ...

    else: # gibts_nicht = False
        # das Ziel gibt es schon!
        # falls die quelle nicht (mehr) existiert, ist alles in Ordnung
        with Session(bind=DB) as session:
            try:
                q = session.query(vainhalt).filter(and_(vainhalt.relPath==qid, vainhalt.dateiName==qtail))
                res = q.first()
            except SQLAlchemyError as e:
                error = str(e.orig)
                x = f"Query des Quell-Satzes meldet Fehler: {error}"
                alertApp(x)
                return False
            if res is None:
                return True # Alles OK
            else:
                alertApp("DB-Fehler! Das Ziel gibt es schon in der DB!")        
                return False
        # end 'with Session...'
    # else
    

def film_loeschen(filmName):
    '''
        loescht einen Film aus dem Archiv (falls da) und aus der DB (falls vorhanden)
        Parms:
            filmName:  relativer Name des Films im Archiv
        Returns:
            Erfolg: True oder False
    '''
    # Volle Dateinamen mit pfaden!
    global DB   #, conn
    
    # zuerst den Pfad bestimmen
    head, tail = os.path.split(filmName)
    Ordner = head[len(ARCHIV)+1:].replace("\\","/")     # den ARCHIV Teilstring abtrennen
    
    # dann die id der Pfade bestimmen
    path_id = _get_pfad_id(Ordner)
    with Session(bind=DB) as session:
        # prüfen, ob es die Quelle in der DB gibt
        try:
            q = session.query(vainhalt).filter(and_(vainhalt.relPath==path_id, vainhalt.dateiName==tail))
            res = q.first()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query, ob Ziel existiert, meldet Fehler: {error}"
            alertApp(x)
            return False
        if res:
            # film in der db gefunden
            # wenn nicht, störts auch nicht
            try:
                filmid = res.id
                x = session.query(vainhalt).get(filmid)
                session.delete(x)
                session.commit()
            except SQLAlchemyError as e:
                error = str(e.orig)
                x = f"Löschversuch von {filmName} ist scheitert: {error}"
                alertApp(x)
                return False
        # physisches löschen
        try:
            os.remove(filmName)
            erfolg = True
        except:
            x = f"Physisches Löschen von {filmName} ist gescheitert: {error}"
            alertApp(x)
            erfolg = False

    return erfolg



def _get_pfad_id(pfad, neuAnlage=True, verbose=True):
    # bestimmt die Pfad-Id eines Pfades und legt diese ggf. an 
    # Parameter:
    #   pfad:     string des Pfades relativ zum Archiv
    #   neuAnlage:    wenn der pfad nicht gefunden wurde,
    #               wird bei True der pfad neu angelegt,
    #   verbose     wenn True, wird über die alertApp eine Fehlermeldung
    #               ausgegeben
    # Returns:      die PfadId bei Erfolg, 
    #               sonst None
    #                

    with Session(bind=DB) as session:
        try:
            qres = session.query(vapfad).filter(vapfad.relPath == pfad).first()
        except SQLAlchemyError as e:
            if verbose:
                error = str(e.orig)
                x = f"Query des vapfad-Satzes meldet Fehler: {error}"
                alertApp(x)
            return None
        
        if qres is None:
            if neuAnlage:
                return anlage_relpath(session, pfad)
            else:
                return None
        else:
            return qres.id


def getFilmMD5(relPfad: str, FilmName: str)->str:
    # ermittelt den gespeicherten MD5-Wert einen Filmes;
    # gibt den MD5-Wert bei Erfolg zurück
    # oder "", wenn nichts gefunden wurde,
    # oder none bei Connect-Fehler
    global DB, Session

    with Session(bind=DB) as session:
        try:
            q = session.query(vainhalt.md5)\
                            .join(vapfad)\
                            .filter(and_(vapfad.relPath==relPfad, vainhalt.dateiName==FilmName) )\
                            .first()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query des Medien-Satzes meldet Fehler: {error}"
            alertApp(x)
            return None

        if q is None:
            return ""
        else:
            return q.md5


def getFilmListe(suchbegriff, archiv=ARCHIV, mitArchiv=True):
    '''
    sucht alle Filme in der Film-db nach Stich(-teil)wort
    Parms:
    SuchBegriff,
    benannte Parameter:
        archiv:         Basis-Pfad zum pyhsischen Archiv
        mitArchiv=True: Bestimmt, ob die Rückgabe mit dem ARCHIV als Präfix erfolgen soll
    Returns:
        gibt "None" zurück, wenn keine DB verbunden werden kann
        gibt [] zurück, wenn nichts gefunden wurde
        gibt eine Liste der gefundenen Filme bei Erfolg zurück
    '''    
    global DB, Session
    

    result = None
    with Session(bind=DB) as session:
        try:
            result = session.query( vapfad.relPath,             
                                    vainhalt.dateiName, 
                                    vainhalt.dateiExt, 
                                    vainhalt.md5
                            )\
                            .join(vapfad)\
                            .filter(vainhalt.dateiName.ilike(suchbegriff))\
                            .order_by(vapfad.relPath)\
                            .all()
            # session.rollback()      # nur lesen, nichts ändern
        except SQLAlchemyError as e:
            # error = str(e.__dict__['orig'])
            error = str(e.orig)
            x = f"Query der Medien-DB meldet Fehler: {error}"
            alertApp(x)
            result = None
        finally:
            session.close()

    if result:
        anz = 0
        result = []
        for res in result:
            anz += 1
            if sys.platform == "win32":
                pfad = res.relPath.replace("/", "\\")            
            if mitArchiv:
                vid = os.path.join(archiv, pfad, res.dateiName)        
            else:
                vid = os.path.join(pfad, res.dateiName)
            result.append(vid)

    return result


def make_md5(DateiName, filler=None):
    '''
    berechnet die MD5 einer Datei
    Parameter:
        DateiName: voller Dateiname mit Pfad
        (opt.) filler: Fülltext vor den laufenden Strichen
    Return:
        MD5-Checksum der Datei
    '''
    chunkSize = 8*1024*1024
    anz = 0
    sym = "-\|/-"
    if filler is None:
        filler = "MD5 "
    with open(DateiName, "rb") as f:
        file_hash = hashlib.md5()
        print("MD5", end="", flush=True)
        while chunk := f.read(chunkSize):
            file_hash.update(chunk)
            print(f"\r{filler}" + sym[anz], end="", flush=True)
            anz = (anz + 1) % 5
    md5 = file_hash.hexdigest()
    return str(md5)

def make_FP(datei):
    '''
    Bestimmt den Fingerprint eine Datei.
    datei muss ein absoluter Pfad sein
    Returns:
        - den FP als 32 Zeichen langen String oder None
    '''
    if not os.path.exists(datei):
        return None

    chunkSize = 64*1024
    fp = ""
    with open(datei, "rb") as q:        
        fp_hash = hashlib.md5()            
        chunk = q.read(chunkSize)
        fp_hash.update(chunk)
    fp  = str(fp_hash.hexdigest())
    return fp


def md5Copy(quelle: str, ziel: str):
    '''
    kopiert die quelle in das Ziel und ermittelt dabei den md5-Wert der Quelle
    Parameter:
        quelle: voller Dateiname der Quelle
        ziel:   voller DateiName des Ziels
    Returns:
        ein Liste der Form (ErfolgNr,ErfolgText,BytesCopied,md5-Wert)
        (BytesCopied = Länge der Datei)
        (Erfolg = 0: OK, > 0 Fehler)
    Abbruchbedingungen:
        - die Quelle existiert nicht, Status = 10
        - das Ziel existiert bereits, Status = 20
        - ZielLänge <> Quell-Länge, 100, "Abweichende Länge"
        - Fehler beim kopieren,  Status = 200
    Normales Ende z.B.: returns (0,"OK",123456798,"A12BC47FDC")
    '''
    chunkSize = 8*1024*1024
    anz = 0
    sym = "-\|/-"
    qlen = 0
    
    filler = "MD5 "
    # Prüfung, ob quelle existiert
    if os.path.exists(quelle):
        qlen = os.path.getsize(quelle)
    else:
        return(10, "Source File not found", 0, "")

    # Prüfung, ob ziel existiert
    if os.path.exists(ziel):
        return(20, "Target exists", 0, "")
    else:   # vorsorglich anlegen
        f = open(ziel, "wb")
        f.close()
    
    with open(quelle, "rb") as q, open(ziel,"wb") as z:
        file_hash = hashlib.md5()
        print("MD5", end="", flush=True)
        copiedLen = 0
        while chunk := q.read(chunkSize):
            copiedLen += len(chunk)
            file_hash.update(chunk)
            z.write(chunk)
            print(f"\r{filler}" + sym[anz], end="", flush=True)
            anz = (anz + 1) % 5

    md5 = file_hash.hexdigest()

    # vergleich der kopierten mit der gespeicherten Länge
    if copiedLen == qlen:
        # print("OK! Kopierte Länge und QuellDateiLänge sind identisch!")
        return(0, "OK", qlen, str(md5))
    else:
        # print("Nanu?")
        # print(f"Quelle: {qlen} Bytes; Ziel: {copiedLen} Bytes")
        return((100, "Abweichende Länge", qlen, str(md5)))
    

if __name__ == "__main__":
    import os, os.path
    
    # film_merken("test\\unter", "TestFilm.mkv", ".mkv", "")
    
    exit(0)
