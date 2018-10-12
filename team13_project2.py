import Disassembler as dis


class Simulator:
    def __init__(self, inst, data, num_registers=32):
        self.__instructions = inst
        self.__memory = data
        self.__registers = dict.fromkeys([r for r in range(num_registers)], 0)
        self.__address = 96
        print('{}\n{}\n'.format(self.__instructions, self.__memory))

    def run(self):
        name = ''
        while name != 'BREAK':
            inst = self.__instructions[self.__address]
            name = inst['name']
            print(inst)
            self.__address += 4

    def read_register(self, r):
        return self.__registers[r]

    def write_register(self, r, val):
        self.__registers[r] = val

    def read_memory(self, a):
        return self.__memory[a]

    def write_memory(self, a, val):
        self.__memory[a] = val

    def alu(self, x1, x2, op):
        d = {
            '0010': x1 + x2,    # ADD
            '0110': x1 - x2,    # SUB
            '0000': x1 & x2,    # AND
            '0001': x1 | x2     # ORR
        }
        return {
            'out': d[op],
            'carry-out': None,
            'zero': d[op] == 0,
            'negative': d[op] < 0,
            'overflow': None,
            'parity': None
        }


if __name__ == '__main__':
    infile = 'test10_bin.txt'
    outfile = 'team13_out'

    d = dis.Disassembler(infile, outfile)
    d.run()
    processed_inst = d.get_processed_inst()
    processed_data = d.get_processed_data()

    s = Simulator(processed_inst, processed_data)
    s.run()
