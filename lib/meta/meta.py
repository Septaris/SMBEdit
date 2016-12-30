__author__ = 'Peter Hofmann'

import os
import sys
from lib.bits_and_bytes import ByteStream
from lib.loggingwrapper import DefaultLogging
from lib.meta.segmanager import SegManager
from lib.meta.docking import Docking
from lib.meta.raildocker import RailDocker
from lib.meta.datatype5 import DataType5
from lib.meta.datatype6 import DataType6
from lib.meta.datatype7 import DataType7


# #######################################
# ###  META
# #######################################

class Meta(DefaultLogging):

	_file_name = "meta.smbpm"

	_tag_type = {
		1: "Finish",
		2: "SegManager",
		3: "Docking"
	}

	def __init__(self, logfile=None, verbose=False, debug=False):
		self._label = "Meta"
		super(Meta, self).__init__(logfile, verbose, debug)
		self._version = (0, 0, 0, 0)
		self.seg_manager = SegManager(logfile=logfile, verbose=verbose, debug=debug)
		self.docked_outdated = Docking(logfile=logfile, verbose=verbose, debug=debug)
		self.rail_docked = RailDocker(logfile=logfile, verbose=verbose, debug=debug)
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
		@type input_stream: ByteStream
		"""
		assert isinstance(input_stream, ByteStream)
		# self.version = input_stream.read_int32_unassigned()
		self._version = input_stream.read_vector_4_byte()
		# assert self._version < (0, 0, 0, 5)
		while True:
			data_type = input_stream.read_byte()
			self._logger.debug("read_file data_type: {}".format(data_type))
			# input_stream.read(38)
			if data_type == 1:  # Finish
				break
			elif data_type == 2:  # SegManager # aLt.class
				self.seg_manager = SegManager(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				self.seg_manager.read(input_stream, False, False)
				break
			elif data_type == 3:  # Docking
				self.docked_outdated = Docking(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				self.docked_outdated.read(input_stream)
			elif data_type == 4:  # Unknown stuff
				self.rail_docked = RailDocker(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				self.rail_docked.read(input_stream, self._version)
			elif data_type == 5:  # Unknown byte array
				self._data_type_5 = DataType5(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				byte_array_length = self._data_type_5.read(input_stream)  # aLt.class
				if byte_array_length > 0:
					break
			elif data_type == 6:  # Unknown byte array
				self._data_type_6 = DataType6(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				self._data_type_6.read(input_stream)  # aLt.class
			elif data_type == 7:  # Unknown byte array
				self._data_type_7 = DataType7(logfile=self._logfile, verbose=self._verbose, debug=self._debug)
				self._data_type_7.read(input_stream)  # aLt.class
			else:
				msg = "read_file unknown data type: {}".format(data_type)
				self._logger.debug(msg)
				raise Exception(msg)
		self.tail_data = input_stream.read()  # any data left?
		self._logger.debug("read_file tail_data: {}".format(len(self.tail_data)))

	def read(self, directory_blueprint):
		"""
		Read data from meta file in blueprint directory

		@param directory_blueprint: input directory
		@type directory_blueprint: str
		"""
		file_path = os.path.join(directory_blueprint, self._file_name)
		with open(file_path, 'rb') as input_stream:
			self._read_file(ByteStream(input_stream))

	# #######################################
	# ###  Write
	# #######################################

	@staticmethod
	def _write_dummy(output_stream):
		"""
		Write dummy data to a byte stream
		Until I know how a meta file has to look like, this will have to do

		@param output_stream: output stream
		@type output_stream: ByteStream
		"""
		output_stream.write_int32_unassigned(0)  # version
		output_stream.write_byte(1)  # data byte 'Finish'

	def _write_file(self, output_stream, relative_apth):
		"""
		write values

		@param output_stream: Output stream
		@type output_stream: ByteStream
		"""
		output_stream.write_vector_4_byte(self._version)

		# data_type 2
		self.seg_manager.write(output_stream)
		# data_type 3
		self.docked_outdated.write(output_stream)

		if self._version > (0, 0, 0, 4):
			# data_type 6
			self._data_type_6.write(output_stream)
			# data_type 7
			self._data_type_7.write(output_stream)
		# data_type 4
		self.rail_docked.write(output_stream, self._version, relative_apth)
		# data_type 5
		self._data_type_5.write(output_stream)

	def write(self, directory_blueprint, relative_path=None):
		"""
		Write data to the meta file of a blueprint

		@param directory_blueprint: output directory
		@type directory_blueprint: str
		"""
		file_path = os.path.join(directory_blueprint, self._file_name)
		with open(file_path, 'wb') as output_stream:
			if relative_path is None:
				self._logger.warning("Writing dummy meta file.")
				self._write_dummy(ByteStream(output_stream))
				return
			self._write_file(ByteStream(output_stream), relative_path)

	# #######################################
	# ###  Else
	# #######################################

	def to_stream(self, output_stream=sys.stdout):
		"""
		Stream logic values

		@param output_stream: Output stream
		@type output_stream: fileIO
		"""
		output_stream.write("####\nMETA v{}\n####\n\n".format(self._version))
		if self._debug:
			self.seg_manager.to_stream(output_stream)
			self.docked_outdated.to_stream(output_stream)
			self._data_type_6.to_stream(output_stream)
			self._data_type_7.to_stream(output_stream)
			self.rail_docked.to_stream(output_stream)
			self._data_type_5.to_stream(output_stream)
		if self._debug:
			output_stream.write("Tail: {} bytes\n".format(len(self.tail_data)))
		output_stream.write("\n")