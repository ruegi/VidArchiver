'''
sameLinePrint.py

'''
import shutil 
anzahlSpalten = shutil.get_terminal_size().columns  


def sameLinePrint(txt: str):    
    '''
    druckt den Text 'txt' in die selbe Zeile, in der aktuell der Cursor steht
    und löscht den Rest der Zeile
    '''
    l = len(txt)
    if l > anzahlSpalten:
        txt = txt[-1*anzahlSpalten]
    else:
        txt = txt + " "*(anzahlSpalten-l)
    print(f"\r{txt}\r" , end="")

# only 4 testing
if __name__ == "__main__":
    sameLinePrint("Das ist ganz Lang"*20)
    sameLinePrint("Das ist kurz\n")

