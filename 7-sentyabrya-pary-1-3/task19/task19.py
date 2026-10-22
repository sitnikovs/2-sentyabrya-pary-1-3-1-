class CPU:
    def __init__(self, name, fr):
        self.name = name
        self.fr = fr

class Memory:
    def __init__(self, name, volume):
        self.name = name
        self.volume = volume

class MotherBoard:
    total_mem_slots = 4
    
    def __init__(self, name, cpu, *mem_slots):
        self.name = name
        self.cpu = cpu
        self.mem_slots = list(mem_slots[:self.total_mem_slots])
    
    def get_config(self):
        config = []
        config.append(f'Материнская плата: {self.name}')
        config.append(f'Центральный процессор: {self.cpu.name}, {self.cpu.fr}')
        config.append(f'Слотов памяти: {self.total_mem_slots}')
        
        memory_info = []
        for mem in self.mem_slots:
            memory_info.append(f'{mem.name} - {mem.volume}')
        config.append(f'Память: {"; ".join(memory_info)}')
        
        return config

cpu = CPU('AMD Ryzen 9', '4.2 GHz')
mem1 = Memory('Samsung', '16 GB')
mem2 = Memory('G.Skill', '32 GB')

mb = MotherBoard('Gigabyte X570', cpu, mem1, mem2)