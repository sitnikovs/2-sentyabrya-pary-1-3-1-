class CPU:
    def __init__(self, name, fr):
        self.name = name
        self.fr = fr

class Memory:
    def __init__(self, name, volume):
        self.name = name
        self.volume = volume

class Motherboard:
    def __init__(self, name, cpu, mem_slots):
        self.name = name
        self.cpu = cpu
        self.mem_slots = mem_slots
        self.mem_slots = mem_slots + [None] * (4 - len(mem_slots))

    def get_config(self):
        mem_str = ""
        for m in self.mem_slots:
            if m:
                mem_str = mem_str + f"{m.name} - {m.volume}; "
            else:
                mem_str = mem_str + "None; "
        
        mem_str = mem_str[:-2]
        
        return [
            f"Материнская плата: {self.name}",
            f"Центральный процессор: {self.cpu.name}, {self.cpu.fr}",
            f"Слотов памяти: {len(self.mem_slots)}",
            f"Память: {mem_str}"
        ]

cpu = CPU("AMD ryzen 5 5600OEM", "3.6 GHz")
mem1 = Memory("ADATA XPG", "16 GB")
mem2 = Memory("ADATA XPG", "16 GB")

mb = Motherboard("GIGABYTE AOURUS ELITE", cpu, [mem1, mem2])

for line in mb.get_config():
    print(line)