'''
tst_quickComp.py
Test programm
Schneller Compare 2er Videos über den Fingeprint der ersten 8 MB
rg 01.2023
Anderungen:
    Version Datum       Inhalt
    ------- ----------  ------------------------------------------
'''
import os.path
import hashlib
import sys
import datetime
import vidarchdb

QUELLE = r"e:\filme\schnitt.alt"

if sys.platform.lower() == "linux":
    ARCHIV = "/archiv/video"
else:
    ARCHIV = "y:/video"

NOK_List = []
NotFoundList = []


# eine einfache Alert Strategie:
# das einbindende Programm kann per 'defineAlert' eine eigene Alert-Routine zur Verfügung
# stellen, um Fehler, Hinweise und Warnungen auszugeben
def simpleAlert(txt: str):
    print(txt)

alertApp = simpleAlert

def defineAlert(alertFunc):
    global alertApp
    alertApp = alertFunc
# -----------------------------------------------------------------------------

def mk_fingerprint(datei: str) -> str:
    '''
    erzeugt einen Fingerprint der Datei und gibt ihn zurück
    gibt None zurück, wenn die Datei gelesen werden kann
    '''
    chunkSize = 1*1024*1024 # MB Göße des Anfangs
    anz = 0
    try:
        with open(datei, "rb") as f:
            file_hash = hashlib.md5()
            chunk = f.read(chunkSize)
            file_hash.update(chunk)        
            md5 = file_hash.hexdigest()
    except:
        md5 = None
    if md5:
        return str(md5)
    else:
        return None


if __name__ == "__main__":
    import os, os.path

    maxAnz = 100000
    anz = 0
    anzOK = 0
    anzFehl = 0
    anzNotFound = 0
    for root, dirs, files in os.walk(QUELLE):
        # nur scan des QuellOrdners
        for f in files:
            if anz >= maxAnz:
                break
            anz += 1
            print(f"Suche Film {f}...", end="")
            qvid = os.path.join(root, f)      
            qlen = os.stat(qvid).st_size
            qdat = os.stat(qvid).st_mtime
            qmd5 = mk_fingerprint(qvid)

            zvidListe = vidarchdb.istSchonDa(f)            
            if zvidListe:
                anzFound = len(zvidListe)
                if anzFound > 1:
                    print(f" ({len(zvidListe)}")
                    for zvid in zvidListe:
                        # Prüfungen, ob ggf. eine andere Datei gleichen Namens vorliegt
                        zlen = os.stat(zvid).st_size
                        if not qlen == zlen:
                            continue
                        zdat = os.stat(zvid).st_mtime
                        if not qdat == zdat:
                            continue
                        # gleicher Name, gleiche Länge und gleiches Datum, da sollte doch auch der Inhaltt gleich sein
                        zmd5 = mk_fingerprint(os.path.join(ARCHIV, zvid))                        
                        if zmd5 == qmd5:
                            print(f"   >>> gefunden: {zvid}   OK!")
                            anzOK += 1
                            break
                    # end for zvid ...
                elif anzFound == 1:
                    print("")
                    zmd5 = mk_fingerprint(os.path.join(ARCHIV, zvid))                        
                    if zmd5 == qmd5:
                        print(f"   >>> gefunden: {zvid}   OK!")
                        anzOK += 1
                    else:
                        print("   >>> Nicht gefunden (Name gefunden aber Fingerprint falsch!")
                        anzNotFound += 1
                        NotFoundList.append(f)
                else:   # anzFound == 0
                    pass
                    # hier sollte es nie hinkommen

            else:  # zvidListe ist leer
                print("   >>> Nicht gefunden!")
                anzNotFound += 1
                NotFoundList.append(f)

        break # nur einen Ordner durchsuchen
    # end 'for os-walk ..'

    print("-----------------------------------------")
    print(f"Anzahl verarbeitet    : {anz}")
    print(f"Anzahl OK             : {anzOK}")
    print(f"Anzahl Nicht OK       : {anzFehl}")
    print(f"Anzahl nicht gefunden : {anzNotFound}")
    print("-----------------------------------------")
    print("Nicht-OK-Liste:")
    for f in NOK_List:
        print(f"  - {f}")
    print("-----------------------------------------")
    print("Nicht-Gefunden-Liste:")
    for f in NotFoundList:
        print(f"  - {f}")
    print("-----------------------------------------")

    exit(0)
