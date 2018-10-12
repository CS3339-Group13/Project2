import Disassembler as dis


class Simulator:
    def __init__(self, inst, data, output_file, num_registers=32):
        self.__output_file = output_file
        self.__instructions = inst
        self.__memory = data
        self.__registers = dict.fromkeys([r for r in range(num_registers)], 0)
        self.__pc = 96

    def run(self):
        type = ''
        outfile = open(self.__output_file + '_sim.txt', 'w')
        while type != 'BREAK':
            inst = self.__instructions[self.__pc]
            type = inst['type']
            f = getattr(self, '_Simulator__simulate_' + type.lower())
            f(inst)
            outfile.write(self.get_sim_str(inst))

    def __simulate_r(self, inst):
        self.__pc += 4

    def __simulate_d(self, inst):
        self.__pc += 4

    def __simulate_i(self, inst):
        name = inst['name']
        immediate = inst['immediate']
        rn = inst['rn']
        rd = inst['rd']
        rn_val = self.read_register(rn)
        if name == 'ADDI':
            rd_val = rn_val + immediate
        elif name == 'SUBI':
            rd_val = rn_val - immediate

        self.write_register(rd, rd_val)
        self.__pc += 4

    def __simulate_b(self, inst):
        # opcode = inst['opcode']
        offset = inst['offset']
        self.__pc += offset * 4

    def __simulate_cb(self, inst):
        name = inst['name']
        # opcode = inst['opcode']
        offset = inst['offset']
        rt = inst['rt']
        if (name == 'CBZ' and rt == 0) or (name == 'CBNZ' and rt != 0):
            self.__pc += offset * 4
        else:
            self.__pc += 4

    def __simulate_im(self, inst):
        self.__pc += 4

    def __simulate_nop(self, inst):
        self.__pc += 4

    def __simulate_break(self, inst):
        pass

    def read_register(self, r):
        return self.__registers[r]

    def write_register(self, r, val):
        self.__registers[r] = val

    def read_memory(self, a):
        return self.__memory[a]

    def write_memory(self, a, val):
        self.__memory[a] = val

    def get_sim_str(self, inst):
        out = '=' * 21 + '\n' \
               + 'cycle:{}\t{}\t{}\n'.format(int((self.__pc - 96) / 4), inst['address'], inst['assembly']) + '\n' \
               + self.print_registers() \
               + '\n' \
               + self.print_memory()
        return out

    def print_registers(self):
        out = 'registers:\n'
        for i in range(4):
            out += 'r{:02d}:'.format(i*8)
            for j in range(8):
                out += '\t{}'.format(self.__registers[i*4+j])
            out += '\n'
        return out

    def print_memory(self):
        out = 'data:'
        addresses = list(self.__memory.keys())
        addresses.sort()
        for i, addr in enumerate(addresses):
            if i % 8 == 0:
                out += '\n{}:\t{}'.format(addr, self.__memory[addr])
            else:
                out += '\t{}'.format(self.__memory[addr])
        out += '\n' * 2
        return out


if __name__ == '__main__':
    infile = 'test10_bin.txt'
    outfile = 'team13_out'

    d = dis.Disassembler(infile, outfile)
    d.run()
    processed_inst = d.get_processed_inst()
    processed_data = d.get_processed_data()

    s = Simulator(processed_inst, processed_data, outfile)
    s.run()
