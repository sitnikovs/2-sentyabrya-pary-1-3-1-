class DataBase:
    lst_data = []
    FIELDS = ('id', 'name', 'old', 'salary')

    def insert(self, data):
        for item in data:
            values = item.split()
            record = {}
            for i, field in enumerate(self.FIELDS):
                record[field] = values[i]
            self.lst_data.append(record)

    def select(self, a , b):
        return self.lst_data

db = DataBase()
db.insert([input()])
print(db.select(0, 0))