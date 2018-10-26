import sys


class Disassembler:
    # bit groupings for printing a spaced out instruction
    inst_spacing = [0, 8, 11, 16, 21, 26, 32]
    break_inst = 0xFEDEFFE7

    def __init__(self, input_file, output_file):
        self.__input_file = input_file
        self.__output_file = output_file

        # Holds information about instructions
        # mem_address : {dict with name, opcode, fields...}
        self.__processed_inst = {}

        # Holds information about data
        # mem_address : decimal value
        self.__processed_data = {}

        self.__lines_dec = []     # Holds raw lines in decimal
        self.__address = 96       # Memory starting address

        self.opcode_dict = {
            (0, 0): ['NOP', 'NOP'],
            (160, 191): ['B', 'B'],
            (1104, 1104): ['R', 'AND'],
            (1112, 1112): ['R', 'ADD'],
            (1160, 1161): ['I', 'ADDI'],
            (1360, 1360): ['R', 'ORR'],
            (1440, 1447): ['CB', 'CBZ'],
            (1448, 1455): ['CB', 'CBNZ'],
            # (1616, 1616): ['R', 'EOR'], # EOR opcode from book, wrong?
            (1872, 1872): ['R', 'EOR'],
            (1624, 1624): ['R', 'SUB'],
            (1672, 1673): ['I', 'SUBI'],
            (1684, 1687): ['IM', 'MOVZ'],
            (1692, 1692): ['R', 'ASR'],
            (1940, 1943): ['IM', 'MOVK'],
            (1690, 1690): ['R', 'LSR'],
            (1691, 1691): ['R', 'LSL'],
            (1984, 1984): ['D', 'STUR'],
            (1986, 1986): ['D', 'LDUR'],
            (2038, 2038): ['BREAK', 'BREAK']
        }

    def get_processed_inst(self):
        return self.__processed_inst

    def get_processed_data(self):
        return self.__processed_data

    def run(self):
        """
        Calls all necessary functions to perform the disassembly
        """
        try:
            self.__read_file()
            self.__process_lines()
        except ValueError as ve:
            print >> sys.stderr, ve

    def __read_file(self):
        """
        Reads the designated input file and stores each line as a decimal integer
        """
        line_num = 0
        with open(self.__input_file, 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                line_num += 1
                if len(line) != 32:
                    raise ValueError('Invalid instruction on line {}: \'{}\''.format(line_num, line))
                self.__lines_dec.append(int(line, 2))

    def __process_lines(self):
        """
        Loops through each decimal line value and calls the function to process it as an instruction or as data
        """
        out_file = open(self.__output_file + '_dis.txt', 'w')
        data = False

        for line_num, line in enumerate(self.__lines_dec):
            valid = False
            if not data:
                out_file.write(Disassembler.get_bin_spaced(line) + '\t' + str(self.__address) + '\t')

                opcode_dec = self.get_bits_as_decimal(31, 21, line)

                # Loop through all known opcodes
                for (low, high), inst_info in self.opcode_dict.items():
                    # Once correct range found, call appropriate function
                    if low <= opcode_dec <= high:
                        valid = True
                        f = getattr(self, '_Disassembler__process_' + inst_info[0].lower())
                        out_file.write(f(line, inst_info[1]) + '\n')

                if not valid:
                    raise ValueError('Invalid instruction on line {}: \'{}\''.format(line_num, line))

                # Set data flag to True when BREAK is reached
                if line == self.break_inst:
                    data = True

            else:
                out_file.write(self.__process_data(line) + '\n')

            self.__address += 4

    @staticmethod
    def tc_to_dec(bin_str):
        """
        Converts a two's complement binary string into a decimal integer
        :param bin_str: A two's complement binary string
        :return: The corresponding decimal integer
        """
        dec = int(bin_str, 2)
        # If positive, just convert to decimal
        if bin_str[0] == '0':
            return dec
        # If negative, flip bits and add 1, then multiply decimal by -1
        else:
            mask_str = '1' * len(bin_str)
            return -1 * ((dec ^ int(mask_str, 2)) + 1)

    @staticmethod
    def get_bits_as_decimal(high, low, b, signed=False):
        """
        Extracts a range of bits from a binary string as a decimal integer
        :param high: The leftmost desired bit
        :param low: The rightmost desired bit
        :param b: The binary string
        :return: The decimal value corresponding to the bots extracted from the binary string
        """
        mask_str = '0' * (31 - high) + '1' * (high - low + 1) + '0' * low
        mask_int = int(mask_str, 2)
        t1 = b & mask_int
        out = t1 >> low
        out_str = bin(out)[2:].zfill(high - low + 1)
        # if negative number and signed
        if out_str[0] == '1' and signed:
            return Disassembler.tc_to_dec(out_str)
        else:
            return out

    @staticmethod
    def get_bin_spaced(inst_dec):
        """
        Spaces a 32-bit string into groups of 8, 3, 5, 5, 5, 6
        :param inst_dec: The 32-bit binary string
        :return: The same string but spaced into the desired groups
        """
        inst_bin = '{0:032b}'.format(inst_dec)
        inst_spaced = ''
        for start, stop in zip(Disassembler.inst_spacing, Disassembler.inst_spacing[1:]):
            inst_spaced += inst_bin[start:stop] + ' '
        return inst_spaced

    def __process_r(self, inst_dec, inst_name):
        """
        Disassembles an R-format ARM instruction
            opcode    rm  shamt   rn  rd
            11        5   6       5   5
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 21, inst_dec)
        rm = Disassembler.get_bits_as_decimal(20, 16, inst_dec)
        shamt = Disassembler.get_bits_as_decimal(15, 10, inst_dec)
        rn = Disassembler.get_bits_as_decimal(9, 5, inst_dec)
        rd = Disassembler.get_bits_as_decimal(4, 0, inst_dec)

        # Return proper assembly instruction
        if inst_name == 'LSL' or inst_name == 'LSR' or inst_name == 'ASR':
            assembly = '{}\tR{}, R{}, #{}'.format(inst_name, rd, rn, shamt)
        else:
            assembly = '{}\tR{}, R{}, R{}'.format(inst_name, rd, rn, rm)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'opcode': opcode,
            'rm': rm,
            'shamt': shamt,
            'rn': rn,
            'rd': rd,
            'assembly': assembly
        }

        return assembly

    def __process_d(self, inst_dec, inst_name):
        """
        Disassembles a D-format ARM instruction
            opcode    offset  op2 rn  rt
            11        9       2   5   5
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 21, inst_dec)
        offset = Disassembler.get_bits_as_decimal(20, 12, inst_dec)
        op2 = Disassembler.get_bits_as_decimal(11, 10, inst_dec)
        rn = Disassembler.get_bits_as_decimal(9, 5, inst_dec)
        rt = Disassembler.get_bits_as_decimal(4, 0, inst_dec)

        assembly = '{}\tR{}, [R{}, #{}]'.format(inst_name, rt, rn, offset)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'D',
            'opcode': opcode,
            'offset': offset,
            'op2': op2,
            'rn': rn,
            'rt': rt,
            'assembly': assembly
        }

        # Return proper assembly instruction
        return assembly

    def __process_i(self, inst_dec, inst_name):
        """
        Disassembles an I-format ARM instruction
            opcode    immediate   rn  rd
            10        12          5   5
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 22, inst_dec)
        immediate = Disassembler.tc_to_dec('{0:012b}'.format(Disassembler.get_bits_as_decimal(21, 10, inst_dec)))
        rn = Disassembler.get_bits_as_decimal(9, 5, inst_dec)
        rd = Disassembler.get_bits_as_decimal(4, 0, inst_dec)

        assembly = '{}\tR{}, R{}, #{}'.format(inst_name, rd, rn, immediate)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'I',
            'opcode': opcode,
            'immediate': immediate,
            'rn': rn,
            'rd': rd,
            'assembly': assembly
        }

        # Return proper assembly instruction
        return assembly

    def __process_b(self, inst_dec, inst_name):
        """
        Disassembles a B-format ARM instruction
            opcode    address
            6         26
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 24, inst_dec)
        address = Disassembler.get_bits_as_decimal(23, 0, inst_dec, signed=True)

        assembly = '{}\t#{}'.format(inst_name, address)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'B',
            'opcode': opcode,
            'offset': address,
            'assembly': assembly
        }

        # Return proper assembly instruction
        return assembly

    def __process_cb(self, inst_dec, inst_name):
        """
        Disassembles a CB-format ARM instruction
            opcode    offset      rt
            8         19          5
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 24, inst_dec)
        offset = Disassembler.get_bits_as_decimal(23, 5, inst_dec, signed=True)
        rt = Disassembler.get_bits_as_decimal(4, 0, inst_dec)

        assembly = '{}\tR{}, #{}'.format(inst_name, rt, offset)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'CB',
            'opcode': opcode,
            'offset': offset,
            'rt': rt,
            'assembly': assembly
        }

        # Return proper assembly instruction
        return assembly

    def __process_im(self, inst_dec, inst_name):
        """
        Disassembles a CB-format ARM instruction
            opcode  shift  immediate   rd
            9       2      16          5
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Extract fields from machine instruction
        opcode = Disassembler.get_bits_as_decimal(31, 23, inst_dec)
        shift = Disassembler.get_bits_as_decimal(22, 21, inst_dec)
        immediate = Disassembler.get_bits_as_decimal(20, 5, inst_dec)
        rd = Disassembler.get_bits_as_decimal(4, 0, inst_dec)

        assembly = '{}\tR{}, {}, LSL {}'.format(inst_name, rd, immediate, shift * 16)

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'IM',
            'opcode': opcode,
            'shift': shift,
            'immediate': immediate,
            'rd': rd,
            'assembly': assembly
        }

        # Return proper assembly instruction
        return assembly

    def __process_nop(self, inst_dec, inst_name):
        """
        Disassembles a NOP instruction
            instruction
            00000000000000000000000000000000
            0x00000000
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # If the instruction isn't all 0s, raise error because opcode is zero -> invalid instruction
        if inst_dec != 0:
            bin_str = '{0:032b}'.format(inst_dec)
            raise ValueError('Invalid instruction on line {}: \'{}\''.format((self.__address - 96) / 4, bin_str))

        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'NOP',
            'assembly': 'NOP'
        }

        # Return proper assembly instruction
        return inst_name

    def __process_break(self, inst_dec, inst_name):
        """
        Disassembles a BREAK instruction
            instruction
            0x11111110110111101111111111100111
            0xFEDEFFE7
        :param inst_dec: The decimal value of the 32-bit instruction
        :param inst_name: The assembly name of the instruction
        :return: A string containing the ARM assembly instruction
        """
        # Add instruction fields to data structure
        self.__processed_inst[self.__address] = {
            'address': self.__address,
            'name': inst_name,
            'type': 'BREAK',
            'assembly': 'BREAK'
        }

        # Return proper assembly instruction
        return inst_name

    def __process_data(self, dec):
        """
        Process a 32-bit two's complement data value
        :param dec: The unsigned decimal of the 32-bit data
        :return: A string containing the 32-bit two's complement binary string, the address, and the signed decimal
        value
        """
        bin_str = '{0:032b}'.format(dec)
        tc_dec = Disassembler.tc_to_dec(bin_str)

        # Add data to data structure
        self.__processed_data[self.__address] = tc_dec

        # Return string for output
        return '{}\t{}\t{}'.format(bin_str, self.__address, tc_dec)


if __name__ == "__main__":
    infile = ''
    outfile = ''

    # Get in/out file from command line arguments
    for i in range(len(sys.argv)):
        if sys.argv[i] == '-i':
            infile = sys.argv[i + 1]
        elif sys.argv[i] == '-o':
            outfile = sys.argv[i + 1]

    # Create disassembler and run
    d = Disassembler(infile, outfile)
    d.run()
