'''
Update der vidarchiv db beim Wechsel von Version 1.0 nach 1.1
rg, 2023-02-19
'''

from vidarchdbStruct import *
from pathlib import Path
import hashlib
from time import sleep

fehlerListe = []

def get_FP(datei):
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


def get_pfad(pfadId):
    # liest den Pfad mit Hilfe der PfadId aus der DB
    global DB, Session
    with Session() as session:
        try:
            q = session.query(vapfad).get(pfadId)
            return q.relPath
        except SQLAlchemyError as e:
            DBerror = str(e.orig)
            return None


def update_inhalt(vainhalt_satz):
    '''
    aktualisiert einen vainhalt Satz um die Felder modDateTime, dateiLen und FP
    gint den Satz aktualisiert zurück
    '''
    global DB, Session

    if relP := get_pfad(vainhalt_satz.relPath):
        absPfad = ARCHIV + "/" + relP + "/" + vainhalt_satz.dateiName
    else:
        vainhalt_satz.FP = None        
        return vainhalt_satz

    if not os.path.exists(absPfad):
        vainhalt_satz.FP = None
        return vainhalt_satz

    absP = Path(absPfad)
    stat_res = absP.stat()
    vainhalt_satz.modDateTime = stat_res.st_mtime
    vainhalt_satz.dateiLen = stat_res.st_size
    vainhalt_satz.FP = get_FP(absPfad)
    return vainhalt_satz

# Main ---------------------------------------------------------------------------------------
with Session() as session:
    try:
        q = session.query(vainhalt).filter(vainhalt.relPath == 70).order_by(vainhalt.relPath).all()
        # q = session.query(vainhalt).order_by(vainhalt.relPath).all()
        for rec in q:
            print(f"> {rec.relPath}; {rec.dateiName}", end=" ")
            if rec.FP:
                print("OK")
                continue
            else:
                rec = update_inhalt(rec)
                if not rec.FP:
                    print("FEHLER!")
                    x = f"Fehler! Datei [relPath={rec.relPath}; ID={rec.id}; dateiName={rec.dateiName}] nicht gefunden!"
                    print(x)
                    fehlerListe.append(x)
                    continue
                print(" UPDATE!")
            sleep(1)
            session.commit()

    except SQLAlchemyError as e:
        DBerror = str(e.orig)
        print(f"Fehler in der DB: {DBerror}")

if fehlerListe:
    with open("dbUpdate11 FehlerListe.txt", "w") as fehl:
        for zle in fehlerListe:
            print(zle, file=fehl)

exit(0)


