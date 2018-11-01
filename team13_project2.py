import sys
from Disassembler import Disassembler
from pprint import pprint


class Simulator:

    def __init__(self, inst, data, output_file, num_registers=32):
        self.__output_file = output_file
        self.__instructions = inst
        self.__data_begin = max(self.__instructions.keys()) + 4
        self.__memory = data
        self.__registers = [0] * num_registers
        self.__pc = 96

    def run(self):
        """
        Calls all necessary functions to simulate the code.
        """
        type = ''
        out = open(self.__output_file + '_sim.txt', 'w')
        while type != 'BREAK':
            try:
                inst = self.__instructions[self.__pc]
            except KeyError:
                print >> sys.stderr, "ERROR: Can't access instruction outside instruction memory ({})".format(self.__pc)
                quit(1)
            type = inst['type']
            f = getattr(self, '_Simulator__simulate_' + type.lower())
            f(inst)
            out.write(self.__get_sim_str(inst))

    def __simulate_r(self, inst):
        """
        Simulates an R-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        name = inst['name']
        rm = inst['rm']
        shamt = inst['shamt']
        rn = inst['rn']
        rd = inst['rd']

        rm_val = self.__read_register(rm)
        rn_val = self.__read_register(rn)

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
        self.__write_register(rd, rd_val)

        self.__pc += 4

    def __simulate_d(self, inst):
        """
        Simulates an D-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        name = inst['name']
        offset = inst['offset']
        rn = inst['rn']
        rt = inst['rt']

        rn_val = self.__read_register(rn)
        address = rn_val + 4 * offset

        if name == 'STUR':
            rt_val = self.__read_register(rt)
            self.__write_memory(address, rt_val)
        elif name == 'LDUR':
            rt_val = self.__read_memory(address)
            self.__write_register(rt, rt_val)

        self.__pc += 4

    def __simulate_i(self, inst):
        """
        Simulates an I-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        name = inst['name']
        immediate = inst['immediate']
        rn = inst['rn']
        rd = inst['rd']
        rn_val = self.__read_register(rn)
        if name == 'ADDI':
            rd_val = rn_val + immediate
        elif name == 'SUBI':
            rd_val = rn_val - immediate

        self.__write_register(rd, rd_val)
        self.__pc += 4

    def __simulate_b(self, inst):
        """
        Simulates an B-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        offset = inst['offset']
        self.__pc += offset * 4

    def __simulate_cb(self, inst):
        """
        Simulates an CB-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        name = inst['name']
        offset = inst['offset']
        rt = inst['rt']
        if (name == 'CBZ' and rt == 0) or (name == 'CBNZ' and rt != 0):
            self.__pc += offset * 4
        else:
            self.__pc += 4

    def __simulate_im(self, inst):
        """
        Simulates an IM-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        name = inst['name']
        shift = inst['shift']
        immediate = inst['immediate']
        rd = inst['rd']

        val = immediate << (shift * 16)
        if name == 'MOVZ':
            self.__write_register(rd, val)
        elif name == 'MOVK':
            rd_val = self.__read_register(rd)
            mask = 0xFFFF << (shift * 16)
            rd_val = (rd_val & mask) | val
            self.__write_register(rd, rd_val)

        self.__pc += 4

    def __simulate_nop(self, inst):
        """
        Simulates an NOP-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        self.__pc += 4

    def __simulate_break(self, inst):
        """
        Simulates an BREAK-format instruction by performing various arithmetic.
        :param inst: A dictionary containing the the instruction's information.
        """
        self.__pc += 4
        pass

    def __read_register(self, r):
        """
        Reads and returns the value in a specified register.
        :param r: The register (0-31).
        :return: The value in register r.
        """
        return self.__registers[r]

    def __write_register(self, r, val):
        """
        Writes a value to a specified register.
        :param r: The register (0-31).
        :param val: The value to write to register r.
        """
        self.__registers[r] = val

    def __read_memory(self, a):
        """
        Reads and returns the value in a specified memory location.
        :param a: The memory address.
        :return: The value in memory address a.
        """
        return self.__memory[a]

    def __write_memory(self, a, val):
        """
        Writes a value to a specified memory location.
        :param a: The memory address.
        :param val: The value to write to memory address a.
        """
        self.__memory[a] = val

    def __get_sim_str(self, inst):
        """
        Returns a string to be printed to the command line for tracking state of the simulator.
        :param inst: A dictionary containing the isntruction's information.
        :return:
        """
        out = '=' * 21 + '\n' \
               + 'cycle:{}\t{}\t{}\n'.format(int((self.__pc - 96) / 4), inst['address'], inst['assembly']) + '\n' \
               + self.registers_to_string() \
               + '\n' \
               + self.memory_to_string()
        return out

    def get_registers(self):
        """
        Returns the current registers.
        :return The simulator's registers.
        """
        return self.__registers

    def get_memory(self):
        """
        Returns the current memory.
        :return: The simulator's memory.
        """
        return self.__memory

    def registers_to_string(self):
        """
        Returns a string of the 32 registers, 4 lines with 8 each and a label for each line.
        :return: A string representation of the registers.
        """
        out = 'registers:\n'
        for i in range(4):
            out += 'r{:02d}:'.format(i*8)
            for j in range(8):
                out += '\t{}'.format(self.__registers[i*8+j])
            out += '\n'
        return out

    def memory_to_string(self):
        """
        Returns a string of the memory, with a label for each line.
        :return: A string representation of the memory.
        """
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
    infile = ''
    outfile = ''

    # Get in/out file from command line arguments
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-i':
            infile = sys.argv[i + 1]
        elif sys.argv[i] == '-o':
            outfile = sys.argv[i + 1]

    d = Disassembler(infile, outfile)
    d.run()
    processed_inst = d.get_processed_inst()
    processed_data = d.get_processed_data()
    pprint(processed_inst)

    s = Simulator(processed_inst, processed_data, outfile)
    s.run()
