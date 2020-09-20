import os

class FixUvloop():
    
    def __init__(self):
        try :
            import uvloop
            with open(uvloop.__file__, 'w') as fp:
                fp.write("raise ImportError\n")
                pass
        except ImportError:
            pass

