__author__ = 'Peter Hofmann'

import sys
import zlib
import datetime

from ...loggingwrapper import DefaultLogging
from ...binarystream import BinaryStream
from ..smdblock.blockpool import block_pool, StyleBasic


class SmdSegment(DefaultLogging):
    """
    Each segment represents an area the size of 32 x 32 x 32 (smd3) and contains 32768 blocks
    A Segment position is the lowest coordinate of a segment area.
    The Position coordinates are always a multiple of 32, like (32, 0, 128)
    Example: The core, or center of a blueprint is (16,16,16) and the position of its segment is (0,0,0)

    @type block_index_to_block: dict[int, StyleBasic]
    @type _position: tuple[int]
    """

    def __init__(self, version, blocks_in_a_line=16, logfile=None, verbose=False, debug=False):
        super(SmdSegment, self).__init__(
            label="SmdSegment",
            logfile=logfile,
            verbose=verbose,
            debug=debug)
        self._blocks_in_a_line = blocks_in_a_line
        self._blocks_in_an_area = self._blocks_in_a_line * self._blocks_in_a_line
        self._blocks_in_a_cube = self._blocks_in_an_area * self._blocks_in_a_line
        self._region_version = version
        self._version = 0
        self._timestamp = 0
        self._position = None
        self.has_valid_data = False
        self._compressed_size = 0
        self.block_index_to_block = {}
        self._header_size = 26
        if self._region_version == 0:
            self._header_size = 25
        self._data_size = 5120-self._header_size

    # #######################################
    # ###  Read
    # #######################################

    def _read_header(self, input_stream):
        """
        Read segment header data from a byte stream.
        Size: 25/26 byte

        @param input_stream: input byte stream
        @type input_stream: BinaryStream
        """
        if self._region_version != 0:
            self._version = abs(input_stream.read_byte())  # 1 byte
        self._timestamp = input_stream.read_int64_unassigned()  # 8 byte
        self._position = input_stream.read_vector_3_int32()  # 12 byte
        self.has_valid_data = input_stream.read_bool()  # 1 byte
        self._compressed_size = input_stream.read_int32_unassigned()  # 4 byte

    def _read_block_data(self, block_list, input_stream):
        """
        Read segment block data from a byte stream.
        Size: 5120-header_size byte

        @type block_list: BlockList
        @param input_stream: input byte stream
        @type input_stream: BinaryStream
        """
        decompressed_data = zlib.decompress(input_stream.read(self._compressed_size))
        self.block_index_to_block = {}
        for block_index in range(0, int(len(decompressed_data) / 3)):
            position = block_index * 3
            int_24bit = BinaryStream.unpack_int24(decompressed_data[position:position+3])
            block = block_pool(int_24bit, version=self._version)
            if block is None:
                continue
            block_list[self.get_block_position_by_block_index(block_index)] = block
        input_stream.seek(self._data_size-self._compressed_size, 1)  # skip unused bytes

    def read(self, block_list, input_stream):
        """
        Read segment data from a byte stream.
        Always total size 5120 byte

        @type block_list: BlockList
        @param input_stream: input byte stream
        @type input_stream: BinaryStream
        """
        assert isinstance(input_stream, BinaryStream)
        self._read_header(input_stream)
        if not self.has_valid_data:
            input_stream.seek(self._data_size, 1)  # skip presumably empty bytes
        else:
            self._read_block_data(block_list, input_stream)
        if self.has_valid_data and len(self.block_index_to_block) == 0:
            self.has_valid_data = False

    # #######################################
    # ###  Write
    # #######################################

    def _write_block_data(self, output_stream):
        """
        Write segment block data to a byte stream.
        Size: 49126 byte + 4 byte because of compressed_size

        @param output_stream: input byte stream
        @type output_stream: BinaryStream
        """
        if not self.has_valid_data:
            self._compressed_size = 0
            output_stream.write_int32_unassigned(self._compressed_size)   # 4 byte
        else:
            byte_string = b""
            set_of_valid_block_index = set(self.block_index_to_block.keys())
            for block_index in range(0, self._blocks_in_a_cube):
                if block_index in set_of_valid_block_index:
                    block_int_24 = self.block_index_to_block[block_index].get_int_24()
                    byte_string += BinaryStream.pack_int24(block_int_24)
                    continue
                byte_string += b"\0" * 3
            compressed_data = zlib.compress(byte_string)
            self._compressed_size = len(compressed_data)
            output_stream.write_int32_unassigned(self._compressed_size)   # 4 byte
            output_stream.write(compressed_data)

        output_stream.seek((self._data_size-1)-self._compressed_size, 1)
        output_stream.write(b"\0")  # this should fill the skipped positions with \0

    def _write_header(self, output_stream):
        """
        Write segment header data to a byte stream.
        Size: 26 byte - 4 byte

        @attention: compressed_size, 4 bytes, will be written later when the size is known

        @param output_stream: input byte stream
        @type output_stream: BinaryStream
        """
        output_stream.write_byte(self._version)  # 1 byte
        output_stream.write_int64_unassigned(self._timestamp)  # 8 byte
        output_stream.write_vector_3_int32(self._position)  # 12 byte
        output_stream.write_bool(self.has_valid_data)  # 1 byte

    def write(self, output_stream):
        """
        Write segment as binary data to any kind of stream.
        Always total size 49152 byte

        @param output_stream: Output byte stream
        @type output_stream: BinaryStream
        """
        assert isinstance(output_stream, BinaryStream)
        self._write_header(output_stream)
        self._write_block_data(output_stream)

    # #######################################
    # ###  Index and positions
    # #######################################

    def get_block_position_by_block_index(self, block_index):
        """
        Get global position based on local index

        @param block_index:
        @ptype block_index: int

        @return: (x,y,z), a global position
        @rtype: tuple[int]
        """
        # block size z 1024
        # block size y 32
        z = int(block_index / self._blocks_in_an_area)
        rest = block_index % self._blocks_in_an_area
        y = int(rest / self._blocks_in_a_line)
        x = rest % self._blocks_in_a_line
        return x+self._position[0], y+self._position[1], z+self._position[2]

    def get_block_index_by_block_position(self, position):
        """
        Get block index of position in this segment

        @param position: x,y,z position of block
        @type position: tuple[int]

        @return: index of block of this segment 0:32767
        @rtype: int
        """
        assert isinstance(position, (list, tuple))
        return \
            (position[0] % self._blocks_in_a_line) + \
            (position[1] % self._blocks_in_a_line) * self._blocks_in_a_line + \
            (position[2] % self._blocks_in_a_line) * self._blocks_in_an_area

    # #######################################
    # ###  Set
    # #######################################

    def set_position(self, segment_position):
        """
        Set position of segment

        @param segment_position: x,y,z position of segment
        @type segment_position: tuple[int]
        """
        self._position = segment_position

    def add(self, block_position, block, replace=True):
        """
        Add a block to the segment based on its global position

        @param block_position: x,y,z position of block
        @type block_position: int,int,int
        @param block:
        @type block: StyleBasic
        """
        block_index = self.get_block_index_by_block_position(block_position)
        if not replace and block_index in self.block_index_to_block:
            self._logger.debug("Prevented block replacement")
            return
        self.block_index_to_block[block_index] = block
        self.has_valid_data = True

    def to_stream(self, output_stream=sys.stdout):
        """
        Stream segment values

        @param output_stream: Output stream
        @type output_stream: fileIO
        """
        output_stream.write("Segment: {} '{}' ({})\n".format(
            self._position,
            datetime.datetime.fromtimestamp(self._timestamp / 1000.0).strftime('%Y-%m-%d %H:%M:%S'),
            self._version,
            ))
        output_stream.flush()
        if self._debug:
            for block_index in sorted(self.block_index_to_block.keys()):
                output_stream.write("{}\t".format(self.get_block_position_by_block_index(block_index)))
                # output_stream.write("{}\t".format(block_index))
                self.block_index_to_block[block_index].to_stream(output_stream)
        output_stream.flush()