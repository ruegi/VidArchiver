'''
vidarchdb.py
Erstellen / Pflegen der Video-Archiv-DB mittels sqlalchemy / sqlite
rg 05.2022
'''

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, Text
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy import exc
import os.path
import hashlib
from sameLinePrint import sameLinePrint

DBVERSION = "1.0"
DBNAME = "vidarch.db"
ARCHIV = "v:\\video"
SQLECHO = False

engine = None
base = declarative_base()
conn = None
session = sessionmaker()
my_session = None

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
    global DBNAME
    DBNAME=db
    return


def dbconnect(mustExist=True, SQLECHO=SQLECHO):
    '''
    Verbindet die DB und gibt True bei Erfolg zurück, sonst False
    opt. KeyWord-Parameter:
        db:         Pfad zur DB (default DBNAME)
        mustExist:  legt fest, ob die Bank schon vorhanden sein soll (default: True)
    '''
    global DBNAME, engine, conn, my_session
    
    if mustExist:
        if not os.path.exists(DBNAME):
            print(f"DB [{db}] pyhsisch nicht gefunden!")
            return False
    if engine is None:
        try:
            engine = create_engine('sqlite+pysqlite:///' + DBNAME, echo=SQLECHO, future=True,
                                            connect_args={'check_same_thread': False})
            conn = engine.connect()
            my_session = session(bind=engine)   
            return True
        except:
            print("Exception bei engine/conn/session-Try")
            return False
    else:
        # print("DB OK")
        return True

def erstelle_db(db=DBNAME, archiv=ARCHIV):
    global DBNAME, engine, conn, my_session
    dbconnect(mustExist=False)

    base.metadata.create_all(conn)
    q = my_session.query(vaconfig).count()
    if q == 0:
        _ = set_config("VideoArchiv", archiv)
        _ = set_config("DBVERSION", DBVERSION)


def film_merken(relPath, datei, ext, md5, verbose=True):
    global engine, conn, my_session
    if not dbconnect():
        return False
    retval = "OK >>> "
    # erst den relPath anlegen, falls er nicht schon da ist
    path_id = anlage_relpath(my_session, relPath=relPath)
    # relPath + Datei sind zusammen unique; vorher prüfen!
    q = my_session.query(vainhalt).filter(and_(vainhalt.relPath == path_id, vainhalt.dateiName == datei))
    f = q.first()
    if f is None:
        
        print("Film nicht gefunden!",f"path_id={path_id}", f"name={datei}" )
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

    q = my_session.query(vaconfig).filter(vaconfig.key == key)
    cnf = q.first()
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
    global engine, conn, my_session
    if session is None:
        dbconnect()
    if "\\" in relPath:
        relp = relPath.replace("\\", "/")
    else:
        relp = relPath
    q = session.query(vapfad).filter(vapfad.relPath == relp)
    pa = q.first()
    if pa is None:
        pa = vapfad(relPath=relPath)
        try:
            session.add(pa)
            session.commit()
            id = pa.id
        except:     # hier sollte es nur bei einer race-condition hinkommen...
            session.rollback()
            q = session.query(vapfad).filter(vapfad.relPath == relPath)
            pa = q.first()
            id = pa.id
    else:
        id = pa.id
    return id


def export_CSV(name="vidarch.csv"):    
    global engine, conn, my_session
    dbconnect(mustExist=True)
    q = my_session.query(vapfad.relPath, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5).join(vapfad).all()
    with open(name, "w", encoding="UTF-8") as f:        
        print("relPath;Datei;Ext;MD5", file=f)
        for erg in q:
            print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}", file=f)
            print(f"{erg[0]};{erg[1]};{erg[2]};{erg[3]}")


def db_scan():
    global engine, conn, my_session
    if not dbconnect(mustExist=True):
        return "Kann die DB nicht verbinden!"
    q = my_session.query(vapfad.relPath, vainhalt.id, vainhalt.dateiName, vainhalt.dateiExt, vainhalt.md5)\
                        .join(vapfad)\
                        .group_by(vapfad.relPath, vainhalt.dateiName)\
                        .all()
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
        

def findeFilm(suchbegriff1, suchbegriff2, db=DBNAME, archiv=ARCHIV):
    '''
    sucht einen Film in der Film-db nach 1-2 Stichworten
    Parms:
    SuchBegriffe 1 und 2,
    benannte Parameter:
        db: Pfad zur sqlite-DB
        archiv: Basis-Pfad zum pyhsischen Archiv
    Returns:
        gibt "None" zurück, wenn keine DB verbunden werden kann
        gibt [] zurück, wenn nichts gefunden wurde
    '''
    global engine, conn, my_session
    if not dbconnect(mustExist=True):
        print(f"!!! Fehler, die Bank konnte nicht verbunden werden!")
        return None
    # if '*' in suchbegriff1 or '_' in suchbegriff1 or ' ' in suchbegriff1:
        # looking_for = suchbegriff1.replace('_', '?')\
        #                     .replace('*', '%')\
        #                     .replace('?', '_')\
        #                     .replace(' ', '_')
    if ' ' in suchbegriff1:
        looking_for = "%" + suchbegriff1.replace(' ', '_') + "%"
        # print(f"Suchbegriff: [{looking_for}]")
    else:
        looking_for = '%{0}%'.format(suchbegriff1)

    result = my_session.query( vapfad.relPath, 
                               vainhalt.dateiName, 
                               vainhalt.dateiExt, 
                               vainhalt.md5
                            )\
                            .join(vapfad)\
                            .filter(vainhalt.dateiName.ilike(looking_for))\
                            .order_by(vapfad.relPath)
    anz = 0
    lst = []
    for res in result:
        if suchbegriff2.lower() in res.dateiName.lower() or suchbegriff2 == "":
            anz += 1
            pfad = res.relPath.replace("/", "\\")
            vid = os.path.join(archiv, pfad, res.dateiName)
            # created= os.stat(vid).st_ctime
            lst.append(vid)
    return lst

def film_umbenennen(alterName, neuerName):
    # benennt den Film in der DB um und/oder verschiebt ihn in einen anderen Ordner
    # gibt bei Erfolg True, sonst False zurück
    # Parms:
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
    q = my_session.query(vainhalt).filter(and_(vainhalt.relPath==zid, vainhalt.dateiName==ztail))
    res = q.first()
    if res is None: # gibt es noch nicht, also los
        # Update des Satzes
        q = my_session.query(vainhalt).filter(and_(vainhalt.relPath==qid, vainhalt.dateiName==qtail))
        res = q.first()
        res.relPath = zid
        res.dateiName = ztail
        my_session.commit()
        return True
    else:
        print("Fehler! Das Ziel gibt es schon!")
        return False

def _get_pfad_id(session, pfad):
    # bestimmt die Pfad-Id eines Pfades und legt diese ggf. an
    qres = session.query(vapfad).filter(vapfad.relPath == pfad).first()
    if qres is None:
        return anlage_relpath(session, pfad)
    else:
        return qres.id
    

def make_md5(DateiName):
    '''
    berechnet die MD5 einer Datei
    Parameter:
        DateiName: voller Dateiname mit Pfad
    Return:
        MD5-Checksum der Datei
    '''
    chunkSize = 8*1024*1024        
    anz = 0
    sym = "-\|/-"
    with open(DateiName, "rb") as f:
        file_hash = hashlib.md5()
        print("MD5", end="", flush=True)
        while chunk := f.read(chunkSize):
            file_hash.update(chunk)
            print("\rMD5 " + sym[anz], end="", flush=True)
            anz = (anz + 1) % 5
    md5 = file_hash.hexdigest()
    print("")
    # print(md5)  # to get a printable str instead of bytes
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


'''
aus: https://stackoverflow.com/questions/27736122/how-to-insert-into-multiple-tables-to-mysql-with-sqlalchemy
session = self.DBSession()
new_group = Group(name='gname')
session.add(new_group)
session.flush() # NOTE: this will actually insert the record in the database and set
                # new_group.id automatically. The session, however, is not committed yet! 
gu = GroupUser(gid=new_group.id, uid=100)
session.add(gu)

session.commit() # this will finally commit your transaction, i.e. 2 statements above
'''

