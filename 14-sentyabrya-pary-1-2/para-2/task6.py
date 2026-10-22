class Message:
    def __init__(self, text):
        self.text = text
        self.fl_like = False
        self.id = id(self)


class Viber:
    msgs = {}  

    @classmethod
    def add_message(cls, msg):
        cls.msgs[msg.id] = msg

    @classmethod
    def remove_message(cls, msg):
        if msg.id in cls.msgs:
            del cls.msgs[msg.id]

    @classmethod
    def set_like(cls, msg):
        if msg.id in cls.msgs:
            msg.fl_like = not msg.fl_like

    @classmethod
    def total_messages(cls):
        return len(cls.msgs)

msg = Message("Всем привет!")
Viber.add_message(msg)
Viber.add_message(Message("Это курс по Python ООП."))
Viber.add_message(Message("Что вы о нем думаете?"))

print(Viber.total_messages())          
Viber.set_like(msg)
print(msg.fl_like)                
Viber.remove_message(msg)
print(Viber.total_messages())          
 