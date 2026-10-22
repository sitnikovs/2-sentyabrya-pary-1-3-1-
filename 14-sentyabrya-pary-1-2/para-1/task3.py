TYPE_OS = 1

class DialogWindows:
    name_class = "DialogWindows"

class DialogLinux:
    name_class = "DialogLinux"

class Dialog:
    def __new__(cls, *args, **kwargs):
        if TYPE_OS == 1:
            obj = super().__new__(DialogWindows)
        else:
            obj = super().__new__(DialogLinux)
        obj.name = args[0]
        return obj

dlg1 = Dialog("Win")
print(type(dlg1).__name__, dlg1.name, dlg1.name_class)  

TYPE_OS = 2
dlg2 = Dialog("Linux")
print(type(dlg2).__name__, dlg2.name, dlg2.name_class)
    