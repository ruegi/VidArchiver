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
'''

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Text
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os.path
import hashlib
import sys
from sameLinePrint import sameLinePrint
from privat import DBZugang

DBVERSION = "1.0"
MODULVERSION = "1.2 vom 2022-12-02"
# DBNAME = "vidarch.db"
# ARCHIV = "v:\\video"

if sys.platform.lower() == "linux":
    ARCHIV = "/archiv/video"
else:
    ARCHIV = "y:/video"

# mysql DB
DBNAME = 'mysql://userid:psw@IP-Adr/DBName' # nur, um den Aufbau zu zeigen
DBNAME = DBZugang.DBNAME
SQLECHO = False

engine = None
base = declarative_base()
conn = None
session = sessionmaker()
my_session = None

# eine einfache Alert Strategie:
# das einbindende Programm kann per 'defineAlert' eine eigene Alert-Routine zur Verfügung
# stellen, um Fehler, Hinweise und Warnungen auszugeben
def simpleAlert(txt: str):
    print(txt)

alertApp = simpleAlert

def defineAlert(alertFunc):
    global alertApp
    alertApp = alertFunc


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


def defineDBName(db: str):
    # setzt den Namen der zu nutzenden DB
    # jetzt: veraltet
    # global DBNAME
    # DBNAME=db
    return


def dbconnect(mustExist=True, SQLECHO=SQLECHO):
    '''
    Verbindet die DB und gibt True bei Erfolg zurück, sonst False
    opt. KeyWord-Parameter:
        db:         Pfad zur DB (default DBNAME)
        mustExist:  legt fest, ob die Bank schon vorhanden sein soll (default: True)
    '''
    global DBNAME, engine, conn, my_session
    
    if engine is None:
        if DBZugang.DBTyp == "mysql":
            try:            
                engine = create_engine(DBNAME, echo=SQLECHO)
                # , future=True,
                #                                 connect_args={'check_same_thread': False})
                conn = engine.connect()
                my_session = session(bind=engine)   
                return True
            except SQLAlchemyError as e:
                error = str(e.orig)
                alertApp(f"Exception bei engine connect:\n{error}")
                return False
        elif DBZugang.DBTyp == "sqlite":
            DBNAME = ARCHIV + "/vidarch.db"   # für sqlite nötig
            if mustExist:
                if not os.path.exists(DBNAME):
                    print(f"DB [{DBNAME}] pyhsisch nicht gefunden!")
                    return False
            try:            
                engine = create_engine('sqlite+pysqlite:///' + DBNAME, echo=SQLECHO, future=True,
                                            connect_args={'check_same_thread': False})                
                conn = engine.connect()
                my_session = session(bind=engine)   
                return True
            except SQLAlchemyError as e:
                error = str(e.orig)
                alertApp(f"Exception bei engine connect:\n{error}")
                return False
        else:
            alertApp(f"Ungültiger DBTyp {DBZugang.DBTyp} - Abbruch!")
            return False
    else:
        # print("DB OK")
        return True

def erstelle_db(db=DBNAME, archiv=ARCHIV):
    global DBNAME, engine, conn, my_session
    dbconnect(mustExist=False)

    base.metadata.create_all(conn)
    try:
        q = my_session.query(vaconfig).count()
        if q == 0:
            _ = set_config("VideoArchiv", archiv)
            _ = set_config("DBVERSION", DBVERSION)
    except SQLAlchemyError as e:
        error = str(e.orig)
        alertApp(f"Query meldet Fehler: {error}")
    
    return

  



def film_merken(relPath, datei, ext, md5, verbose=True):
    global engine, conn, my_session
    if not dbconnect():
        return False
    retval = "OK >>> "
    # erst den relPath anlegen, falls er nicht schon da ist
    path_id = anlage_relpath(my_session, relPath=relPath)
    # relPath + Datei sind zusammen unique; vorher prüfen!
    try:
        q = my_session.query(vainhalt).filter(and_(vainhalt.relPath == path_id, vainhalt.dateiName == datei))
        f = q.first()
    except SQLAlchemyError as e:
        error = str(e.orig)
        alertApp(f"Query meldet Fehler: {error}")
        return False

    if f is None:        
        alertApp("Film nicht in der DB gefunden! " + f"path_id={path_id}; " +  f"name={datei}" )
        if not md5:
            md5 = make_md5(os.path.join(ARCHIV, relPath, datei))
        if md5:
            # ggf. gibt es den md5 schon, dann war der Film nur per OS direkt renamed worden
            q = my_session.query(vainhalt).filter(and_(vainhalt.relPath == path_id, vainhalt.md5 == md5))
            f = q.first()
            if f is None: # Neuanlage mit vorhandener md5
                film = vainhalt(path_id, datei, ext, md5)
                my_session.add(film)
                my_session.commit()
                retval = "NEU >>> "
                if verbose:
                    print(f"  >>> OK! Film {relPath}\{datei} in der DB neu angelegt!")
            else: # nur Update des FilmNamens
                f.dateiName = datei
                my_session.commit()
                retval = "UPD >>> "
                if verbose:
                    print(f"  >>> OK! FilmName {relPath}\{datei} in der DB aktualisiert!")
    else:  # Film schon vorhanden, alles ok
        retval = "OK  >>> "
        if verbose:
            print(f"  >>> OK! Film {relPath}\{datei} in der DB gefunden!")

    return retval

def set_config(key, value):
    # legt eine neue Config an oder aktualisiert nur den Wert
    # und gibt die id zurück
    global engine, conn, my_session
    dbconnect()
    if get_config(key) is None:
        cnf = vaconfig(key, value)
        try:
            my_session.add(cnf)
            my_session.commit()
            id = cnf.id
        except:
            my_session.rollback()
    try:
        q = my_session.query(vaconfig).filter(vaconfig.key == key)
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
            my_session.commit()
    return id


def get_config(key: str):
    # gibt den in der Config gespeicherten Wert für den Parameter 'key' oder None zurück
    global engine, conn, my_session
    dbconnect()
    q = my_session.query(vaconfig).filter(vaconfig.key == key)
    cnf = q.first()
    if cnf is None:
        return None
    else:
        return cnf.value

def anlage_relpath(session, relPath):
    # legt einen neuen relPath an
    # und gibt die id zurück
    # relPath muss wirklich relativ zum ArchivPfad sein!
    global engine, conn, my_session
    if session is None:
        dbconnect()
    else:
        my_session = session
    if "\\" in relPath:
        relp = relPath.replace("\\", "/")
    else:
        relp = relPath
    q = my_session.query(vapfad).filter(vapfad.relPath == relp)
    pa = q.first()
    if pa is None:  # gibt es noch nicht
        pa = vapfad(relPath=relPath)
        try:
            my_session.add(pa)
            my_session.commit()
            id = pa.id
        except:     # hier sollte es nur bei einer race-condition hinkommen...
            my_session.rollback()
            # q = my_session.query(vapfad).filter(vapfad.relPath == relPath)
            # pa = q.first()
            id = None
    else:
        id = pa.id
    return id


def export_CSV(name="vidarch.csv"):    
    global engine, conn, my_session
    if dbconnect(mustExist=True):
        try:
            q = my_session.query(vapfad.relPath, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5).join(vapfad).all()
        except SQLAlchemyError as e:
            error = str(e.orig)
            alertApp(f"Sorry! kein Export möglich! Query meldet Fehler: {error}")
            return
        with open(name, "w", encoding="UTF-8") as f:        
            print("relPath;Datei;Ext;MD5", file=f)
            for erg in q:
                print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}", file=f)
                print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}")


def db_scan(Pfad=None):
    '''
    db_scan
    Prüft, ob alle Medien, die in der DB sind, sich auch im Archiv befinden.
    Wenn nicht, wird der DB-Eintrg gelöscht
    Parameter:
        Pfad:   relativer Pfad unterhalb des Archiv oder None, wenn das fesamte Archiv 
                durchlaufen werden soll
    Returns:
        string mit FehlerText oder leerer String be Erfolg
    '''
    global engine, conn, my_session
    if not dbconnect(mustExist=True):
        return "Kann die DB nicht verbinden!"
    try:
        if Pfad is None:
            q = my_session.query(vapfad.relPath, vainhalt.id, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5)\
                            .join(vapfad)\
                            .group_by(vapfad.relPath, vainhalt.dateiName)\
                            .all()
        else:
            q = my_session.query(vapfad.relPath, vainhalt.id, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5)\
                            .join(vapfad)\
                            .filter(vapfad.relPath==Pfad)\
                            .order_by(vainhalt.dateiName)\
                            .all()
    except SQLAlchemyError as e:
        error = str(e.orig)
        x = f"DB-Scan kann nicht laufen! Query meldet Fehler: {error}"
        alertApp(x)
        return x

    for res in q:
        film = os.path.join(ARCHIV, res.relPath, res.dateiName)
        if os.path.exists(film):
            sameLinePrint(f"OK! Film [{film}] gefunden!")
        else:
            # Film löschen aus DB
            id = res.id
            x = my_session.query(vainhalt).get(id)
            my_session.delete(x)
            my_session.commit()
            sameLinePrint(f" >>> Film [{film}] wurde aus der DB gelöscht!")
    sameLinePrint(f"Ende DBScan!")
    print("")
    return ""


def istSchonDa(film: str)-> list:
    if not dbconnect(mustExist=True):
        alertApp(f"!!! Fehler, die Bank konnte nicht verbunden werden!")
        return None
    try:
        result = my_session.query( vapfad.relPath, 
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
    return liste 


# def findeFilm(suchbegriff1, suchbegriff2, db=DBNAME, archiv=ARCHIV):
#     '''
#       DEPRECATED!     ist jetzt in vidsuch.py enthalten und verbessert!
#     sucht einen Film in der Film-db nach 1-2 Stichworten
#     Parms:
#     SuchBegriffe 1 und 2,
#     benannte Parameter:
#         db: Pfad zur sqlite-DB
#         archiv: Basis-Pfad zum pyhsischen Archiv
#     Returns:
#         gibt "None" zurück, wenn keine DB verbunden werden kann
#         gibt [] zurück, wenn nichts gefunden wurde
#     '''
#     global engine, conn, my_session
#     if not dbconnect(mustExist=True):
#         alertApp(f"!!! Fehler, die Bank konnte nicht verbunden werden!")
#         return None
#     # if '*' in suchbegriff1 or '_' in suchbegriff1 or ' ' in suchbegriff1:
#         # looking_for = suchbegriff1.replace('_', '?')\
#         #                     .replace('*', '%')\
#         #                     .replace('?', '_')\
#         #                     .replace(' ', '_')
#     if ' ' in suchbegriff1:
#         looking_for = "%" + suchbegriff1.replace(' ', '_') + "%"
#         # print(f"Suchbegriff: [{looking_for}]")
#     else:
#         looking_for = '%{0}%'.format(suchbegriff1)

#     try:
#         result = my_session.query( vapfad.relPath, 
#                                 vainhalt.dateiName, 
#                                 vainhalt.dateiExt, 
#                                 vainhalt.md5
#                                 )\
#                                 .join(vapfad)\
#                                 .filter(vainhalt.dateiName.ilike(looking_for))\
#                                 .order_by(vapfad.relPath)
#     except SQLAlchemyError as e:
#         error = str(e.orig)
#         x = f"Suche  nach {looking_for} fehlgeschlagen!\n Query meldet Fehler: {error}"
#         alertApp(x)
#         return None

#     anz = 0
#     lst = []
#     for res in result:
#         if suchbegriff2.lower() in res.dateiName.lower() or suchbegriff2 == "":
#             anz += 1
#             pfad = res.relPath.replace("/", "\\")
#             vid = os.path.join(archiv, pfad, res.dateiName)
#             # created= os.stat(vid).st_ctime
#             lst.append(vid)
#     return lst


def film_umbenennen(alterName, neuerName):
    '''
        benennt den Film in der DB um und/oder verschiebt ihn in einen anderen Ordner
        gibt bei Erfolg True, sonst False zurück
        Parms:
            alterName:  
            neuerName:
    '''
    # Volle Dateinamen mit pfaden!
    global engine, conn, my_session
    if not dbconnect():
        print("FEHLER! Film umbenennen: kann die DB nicht verbinden!")
        return False
    
    # zuerst die quell- und Zielpfade bestimmen
    qhead, qtail = os.path.split(alterName)
    zhead, ztail = os.path.split(neuerName)
    quellOrdner = qhead[len(ARCHIV)+1:].replace("\\","/")     # den ARCHIV Teilstring abtrennen
    zielOrdner  = zhead[len(ARCHIV)+1:].replace("\\","/")

    # dann die id der Pfade bestimmen
    qid = _get_pfad_id(my_session, quellOrdner)
    zid = _get_pfad_id(my_session, zielOrdner)

    # prüfen, ob es das Ziel bereits in der DB gibt
    try:
        q = my_session.query(vainhalt).filter(and_(vainhalt.relPath==zid, vainhalt.dateiName==ztail))
        res = q.first()
    except SQLAlchemyError as e:
        error = str(e.orig)
        x = f"Query, ob Ziel existiert, meldet Fehler: {error}"
        alertApp(x)
        return False

    if res is None: # gibt es noch nicht, also los
        try:
            q1 = my_session.query(vainhalt).filter(and_(vainhalt.relPath==qid, vainhalt.dateiName==qtail))
            res = q1.first()
        except SQLAlchemyError as e:
            error = str(e.orig)
            x = f"Query, ob Quelle existiert, meldet Fehler: {error}"
            alertApp(x)
            return False
        
        if res:
            # Update des Satzes
            try:
                res.relPath = zid
                res.dateiName = ztail
                my_session.commit()
            except SQLAlchemyError as e:
                error = str(e.orig)
                x = f"Update des DB-Satzes, meldet Fehler: {error}"
                alertApp(x)
                return False            
            return True
        else:
            alert = "FEHLER!\n"
            alert += "-"*70 + "\n"
            alert += "Die Quelle existiert als Datei,\n"
            alert += "kann die Quelle in der DB aber nicht finden,\n"
            alert += " daher keine DB Operation!\n"
            alert += "-"*70 + "\n"
            alert += f"alterName: {alterName}\n"
            alert += f"neuerName: {neuerName}\n"
            alert += f"Quelle relPath: {qid}\n"
            alert += f"Quelle DateiName: {qtail}\n"
            alert += f"Ziel relPath: {zid}\n"
            alert += f"Ziel DateiName: {ztail}\n"
            alert += "-"*70 + "\n"
            alertApp(alert)     
            return False
    else:
        # falls die quelle nicht (mehr) existiert, ist alles in Ordnung
        try:
            q = my_session.query(vainhalt).filter(and_(vainhalt.relPath==qid, vainhalt.dateiName==qtail))
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

def _get_pfad_id(session, pfad):
    # bestimmt die Pfad-Id eines Pfades und legt diese ggf. an
    try:
        qres = session.query(vapfad).filter(vapfad.relPath == pfad).first()
    except SQLAlchemyError as e:
        error = str(e.orig)
        x = f"Query des vapfad-Satzes meldet Fehler: {error}"
        alertApp(x)
        return None
    
    if qres is None:
        return anlage_relpath(session, pfad)
    else:
        return qres.id


def getFilmMD5(relPfad: str, FilmName: str)->str:
    # ermittelt den gespeicherten MD5-Wert einen Filmes;
    # gibt den MD5-Wert bei Erfolg zurück
    # oder "", wenn nichts gefunden wurde,
    # oder none bei Connect-Fehler
    if not dbconnect():
        print("FEHLER! Film-MD5 finden: kann die DB nicht verbinden!")
        return None
    try:
        q = my_session.query(vainhalt.md5)\
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
    # import re
    global engine, conn, my_session
    if not dbconnect(mustExist=True):
        alertApp(f"!!! Fehler, die Bank konnte nicht verbunden werden!")
        return None
    try:
        result = my_session.query( vapfad.relPath, 
                                vainhalt.dateiName, 
                                vainhalt.dateiExt, 
                                vainhalt.md5
                            )\
                            .join(vapfad)\
                            .filter(vainhalt.dateiName.ilike(suchbegriff))\
                            .order_by(vapfad.relPath)\
                            .all()
    except SQLAlchemyError as e:
        error = str(e.orig)
        x = f"Query der Medien-DB meldet Fehler: {error}"
        alertApp(x)
        return None

    anz = 0
    lst = []
    for res in result:
        anz += 1
        if sys.platform == "win32":
            pfad = res.relPath.replace("/", "\\")            
        if mitArchiv:
            vid = os.path.join(archiv, pfad, res.dateiName)        
        else:
            vid = os.path.join(pfad, res.dateiName)
        lst.append(vid)
    return lst




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


if __name__ == "__main__":
    import os, os.path
    if os.path.exists(DBNAME):
        try:
            if os.path.exists(DBNAME + ".alt"):
                os.remove(DBNAME + ".alt")
                print("UrAlte DB gelöscht!")    
            os.rename(DBNAME, DBNAME + ".alt")
            print("Alte DB umbenannt!")
        except OSError as e:
            print(f"Konnte die alte DB nicht umbenennen - wird sie noch benutzt!?\n{e}")
            exit(1)
    
    erstelle_db()
    print("Neue DB erstellt!")

    film_merken(my_session, "test\\unter", "TestFilm.mkv", ".mkv", "")    

    exit(0)
