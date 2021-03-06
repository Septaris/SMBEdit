__author__ = 'Peter Hofmann'

import os
import sys

from ...utils.smbinarystream import SMBinaryStream
from ...common.loggingwrapper import DefaultLogging
from ...utils.blockconfig import block_config
from ...utils.vector import Vector
from ..smd3.smd import Smd
from .datatype2 import DataType2
from .datatype3 import DataType3, DockedEntity
from .datatype4 import DataType4
from .datatype5 import DataType5
from .datatype6 import DataType6
from .datatype7 import DataType7
from .tag.raildockentitylinks import RailDockedEntityLinks, RailDockedEntity, RailDockedEntityLink


# #######################################
# ###  META
# #######################################

class Meta(DefaultLogging):

    _file_name = "meta.smbpm"

    _valid_versions = {0, 1, 2, 3, 4, 5}

    _data_type = {
        1: "Finish",
        2: "Stored items / AI config",
        3: "Docking outdated",
        4: "Name/Size/Rail docker",
        5: "AI config",
        6: "unknown",
        7: "unknown",
    }

    def __init__(self, logfile=None, verbose=False, debug=False):
        super(Meta, self).__init__(label="Meta", logfile=logfile, verbose=verbose, debug=debug)
        self._version = 5
        self._data_type_2 = DataType2(logfile=logfile, verbose=verbose, debug=debug)
        self._data_type_3 = DataType3(logfile=logfile, verbose=verbose, debug=debug)
        self._data_type_4 = DataType4(
            max(self._valid_versions), max(self._valid_versions), logfile=logfile, verbose=verbose, debug=debug)
        self._data_type_5 = DataType5(logfile=logfile, verbose=verbose, debug=debug)
        self._data_type_6 = DataType6(logfile=logfile, verbose=verbose, debug=debug)
        self._data_type_7 = DataType7(logfile=logfile, verbose=verbose, debug=debug)
        return

    # #######################################
    # ###  Read
    # #######################################

    def _read_file(self, input_stream):  # avt.class
        """
        Read data from byte stream

        @param input_stream: input stream
        @type input_stream: SMBinaryStream
        """
        assert isinstance(input_stream, SMBinaryStream)
        self._version = input_stream.read_int32_unassigned()
        # self._version = input_stream.read_vector_4_byte()
        assert self._version in self._valid_versions, "Unsupported version '{}' of '{}'.".format(
            self._version, self._file_name)

        self._data_type_2 = DataType2(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
        self._data_type_3 = DataType3(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
        self._data_type_4 = DataType4(
            self._version, max(self._valid_versions), logfile=self._logfile, verbose=self._verbose, debug=self._debug)
        self._data_type_5 = DataType5(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
        self._data_type_6 = DataType6(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
        self._data_type_7 = DataType7(logfile=self._logfile, verbose=self._verbose, debug=self._debug)

        while True:
            data_type = input_stream.read_byte()
            self._logger.debug("Found data_type: {}".format(data_type))
            if data_type == 1:  # Finish
                break
            elif data_type == 2:  # TagManager
                self._data_type_2.read(input_stream)
                break
            elif data_type == 3:  # Docking
                self._data_type_3.read(input_stream)
            elif data_type == 4:  # Rail Docked entities and wireless connections
                self._data_type_4.read(input_stream, self._version)
            elif data_type == 5:  # AI config
                self._data_type_5.read(input_stream)
            elif data_type == 6:  # RailDocker info
                self._data_type_6.read(input_stream)
            elif data_type == 7:  # Remote wireless connections
                self._data_type_7.read(input_stream)
            else:
                msg = "read_file unknown data type: {}".format(data_type)
                self._logger.debug(msg)
                raise Exception(msg)
        self.tail_data = input_stream.read()  # any data left?
        assert len(self.tail_data) == 0, "Unknown byte left: #{}".format(len(self.tail_data))
        if self._version < 4:
            self._logger.debug("Converting smd2 to smd3 positions. v{}".format(self._version))
            self._smd2_to_smd3()

    def read(self, directory_blueprint):
        """
        Read data from meta file in blueprint directory

        @param directory_blueprint: input directory
        @type directory_blueprint: str
        """
        file_path = os.path.join(directory_blueprint, self._file_name)
        with open(file_path, 'rb') as input_stream:
            self._read_file(SMBinaryStream(input_stream))

    # #######################################
    # ###  Write
    # #######################################

    @staticmethod
    def _write_dummy(output_stream):
        """
        Write dummy data to a byte stream
        Until I know how a meta file has to look like, this will have to do

        @param output_stream: output stream
        @type output_stream: SMBinaryStream
        """
        output_stream.write_int32_unassigned(0)  # version
        output_stream.write_byte(1)  # data byte 'Finish'

    def _write_file(self, output_stream, relative_path):
        """
        write values

        @param output_stream: Output stream
        @type output_stream: SMBinaryStream
        """
        output_stream.write_int32_unassigned(self._version)

        # data_type 3
        if self._data_type_3.has_data():
            self._logger.warning("Old style docked entities are not yet supported and are removed")
        self._data_type_3.write_dummy(output_stream)

        # self._data_type_3.write(output_stream, relative_path)

        if self._version > 4:
            # data_type 6
            self._data_type_6.write(output_stream)
            # data_type 7
            self._data_type_7.write(output_stream)
        # data_type 4
        self._data_type_4.write(output_stream, self._version, relative_path)
        # data_type 5
        self._data_type_5.write(output_stream)
        # data_type 2   # todo: needs distinction between station and ship
        # if self._data_type_2.has_data():
        #     self._data_type_2.write(output_stream)
        # else:
        output_stream.write_byte(1)

    def write(self, directory_blueprint, relative_path=None):
        """
        Write data to the meta file of a blueprint

        @param directory_blueprint: output directory
        @type directory_blueprint: str
        """
        self._version = max(self._valid_versions)
        file_path = os.path.join(directory_blueprint, self._file_name)
        with open(file_path, 'wb') as output_stream:
            if relative_path is None:
                self._logger.warning("Writing dummy meta file.")
                self._write_dummy(SMBinaryStream(output_stream))
                return
            self._write_file(SMBinaryStream(output_stream), relative_path)

    # #######################################
    # ###  Else
    # #######################################

    def _smd2_to_smd3(self):
        offset = (8, 8, 8)
        self.move_positions(offset)

    def move_positions(self, vector_direction, main_only=False):
        self._data_type_2.move_position(vector_direction)
        self._data_type_3.move_position(vector_direction)
        self._data_type_4.move_position(vector_direction, main_only)
        self._data_type_5.move_position(vector_direction)
        self._data_type_6.move_position(vector_direction)
        self._data_type_7.move_position(vector_direction)

    def has_old_docked_entities(self):
        """
        True if entities are docked in the old way
        @rtype: bool
        """
        return self._data_type_3.has_data()

    @staticmethod
    def get_docked_entity_location(block_position, block_side_id):
        """
        # 0: "FRONT ",
        # 1: "BACK  ",
        # 2: "TOP   ",
        # 3: "BOTTOM",
        # 4: "RIGHT ",
        # 5: "LEFT  ",

        @type block_position: tuple[int]
        @type block_side_id: int

        @rtype: tuple[int]
        """
        if block_side_id == 0:
            return Vector.addition(block_position, (0, 0, 1))
        elif block_side_id == 1:
            return Vector.subtraction(block_position, (0, 0, 1))
        elif block_side_id == 2:
            return Vector.addition(block_position, (0, 1, 0))
        elif block_side_id == 3:
            return Vector.subtraction(block_position, (0, 1, 0))
        elif block_side_id == 4:
            return Vector.subtraction(block_position, (1, 0, 0))
        elif block_side_id == 5:
            return Vector.addition(block_position, (1, 0, 0))

    def update_docked_entities(self, smd, main_entity_label, rail_docked_label_prefix):
        """
        Replace old style turrets with rail based turrets

        @attention: Needs to be called before docker blocks are replaced.

        @type smd: Smd
        @type main_entity_label: str
        @type rail_docked_label_prefix: str
        """
        while self._data_type_3.has_data():
            docked_entity_index, docker_entity = self._data_type_3.popitem()
            assert isinstance(docker_entity, DockedEntity)
            block = smd.get_block_at_position(docker_entity.position)
            main_entity = RailDockedEntity()
            rail_dock_entity = RailDockedEntity()
            block_side_id = block.get_block_side_id()
            main_entity.set_by_block_side(
                label=main_entity_label,
                location=docker_entity.position,
                block_id=block_config[block.get_id()].get_rail_equivalent(),
                side=block_side_id,
                version=self._version
            )
            rail_dock_entity.set(
                label="{}{}".format(rail_docked_label_prefix, docked_entity_index),
                location=(16, 15, 16),  # below core
                block_id=663,  # Rail docker
                byte_orientation_1=10,  # Bottom pointing forward
                byte_orientation_2=1  # Bottom pointing forward
            )

            link = RailDockedEntityLink()
            link.set(
                docked_entity_location=self.get_docked_entity_location(docker_entity.position, block_side_id),
                entity_main=main_entity,
                entity_docked=rail_dock_entity
                )
            links = RailDockedEntityLinks()
            links.set([link])
            self._data_type_4.add(docked_entity_index, links)

    def move_center_by_vector(self, direction_vector):
        """
        Relocate docked entities in a direction

        @param direction_vector: vector
        @type direction_vector: tuple[int]
        """
        direction_vector = Vector.subtraction((0, 0, 0), direction_vector)
        self.move_positions(direction_vector, main_only=True)

    def to_stream(self, output_stream=sys.stdout):
        """
        Stream logic values

        @param output_stream: Output stream
        @type output_stream: fileIO
        """
        output_stream.write("####\nMETA v{}\n####\n\n".format(self._version))
        if self._debug:
            self._data_type_2.to_stream(output_stream)
            self._data_type_3.to_stream(output_stream)
            self._data_type_4.to_stream(output_stream)
            self._data_type_5.to_stream(output_stream)
            self._data_type_6.to_stream(output_stream, self._version)
            self._data_type_7.to_stream(output_stream)
        if self._debug and len(self.tail_data) > 0:
            output_stream.write("Tail: {} bytes\n".format(len(self.tail_data)))
        output_stream.write("\n")
