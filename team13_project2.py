from Disassembler import Disassembler
from pprint import pprint

# CHECK TO MAKE SURE BRANCH INSTRUCTIONS DON'T BRANCH OUTSIDE OF INSTRUCTION MEMORY
# Display memory starting right after instruction memory
# should dynamically display memory based off of where stuff is added
# display empty memory (all memory from after instructions to end of non-zero)


class Simulator:

    def __init__(self, inst, data, output_file, num_registers=32):
        self.__output_file = output_file
        self.__instructions = inst
        self.__data_begin = max(self.__instructions.keys()) + 4
        self.__memory = data
        self.__registers = [0] * num_registers
        self.__pc = 96

    def run(self):
        type = ''
        out = open(self.__output_file + '_sim.txt', 'w')
        while type != 'BREAK':
            inst = self.__instructions[self.__pc]
            type = inst['type']
            f = getattr(self, '_Simulator__simulate_' + type.lower())
            f(inst)
            out.write(self.get_sim_str(inst))

    def __simulate_r(self, inst):
        name = inst['name']
        rm = inst['rm']
        shamt = inst['shamt']
        rn = inst['rn']
        rd = inst['rd']

        rm_val = self.read_register(rm)
        rn_val = self.read_register(rn)

        op_dict = {
            'AND': rm_val & rn_val,
            'ADD': rm_val + rn_val,
            'ORR': rm_val | rn_val,
            'EOR': rm_val ^ rn_val,
            'SUB': rm_val - rn_val,
            'ASR': rm_val >> shamt,
            'LSR': (rm_val % (1 << 32)) >> shamt,
            'LSL': rm_val << shamt
        }
        rd_val = op_dict[name]
        self.write_register(rd, rd_val)

        self.__pc += 4

    def __simulate_d(self, inst):
        name = inst['name']
        offset = inst['offset']
        rn = inst['rn']
        rt = inst['rt']

        rn_val = self.read_register(rn)
        address = rn_val + 4 * offset

        if name == 'STUR':
            rt_val = self.read_register(rt)
            self.write_memory(address, rt_val)
        elif name == 'LDUR':
            rt_val = self.read_memory(address)
            self.write_register(rt, rt_val)

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
        name = inst['name']
        shift = inst['shift']
        immediate = inst['immediate']
        rd = inst['rd']

        val = immediate << (shift * 16)
        if name == 'MOVZ':
            self.write_register(rd, val)
        elif name == 'MOVK':
            rd_val = self.read_register(rd)
            mask = 0xFFFF << (shift * 16)
            rd_val = (rd_val & mask) | val
            self.write_register(rd, rd_val)

        self.__pc += 4

    def __simulate_nop(self, inst):
        self.__pc += 4

    def __simulate_break(self, inst):
        self.__pc += 4
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
                out += '\t{}'.format(self.__registers[i*8+j])
            out += '\n'
        return out

    def print_memory(self):
        out = 'data:'

        # Fix stupid formatting, thanks Greg
        if len(self.__memory) > 0:
            # Add 0s from beginning to first
            first_data = min(self.__memory.keys())
            for a in range(self.__data_begin, first_data, 4):
                self.__memory[a] = 0

            # Add 0s from last to end of line
            last_data = max(self.__memory.keys())
            a = last_data + 4
            while (a - first_data) % 8 != 0:
                self.__memory[a] = 0
                a += 4

        # Print useful information
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
    infile = 'test11_bin.txt'
    outfile = 'team13_out'

    d = Disassembler(infile, outfile)
    d.run()
    processed_inst = d.get_processed_inst()
    processed_data = d.get_processed_data()

    s = Simulator(processed_inst, processed_data, outfile)
    s.run()
