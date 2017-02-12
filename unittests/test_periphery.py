import os
from unittest import TestCase
from lib.utils.blockconfig import block_config
from lib.utils.periphery import Periphery
from lib.utils.annotate import Annotate
from lib.smblueprint.smd3.smd import Smd

__author__ = 'Peter Hofmann'


class DefaultSetup(TestCase):
    """
    @type object: Periphery
    """

    def __init__(self, methodName='runTest'):
        super(DefaultSetup, self).__init__(methodName)
        self.object = None
        self._blueprint = {
            1: os.path.join("test_blueprints", "B_Wedge"),
            2: os.path.join("test_blueprints", "B_Corner"),
            3: os.path.join("test_blueprints", "B_Tetra"),
            4: os.path.join("test_blueprints", "B_Hepta"),
        }

    def setUp(self):
        block_config.from_hard_coded()
        self.object = None

    def tearDown(self):
        self.object = None
        # if os.path.exists(self.directory_output):
        #     os.rmdir(self.directory_output)


class TestPeriphery(DefaultSetup):
    def test_get_periphery_simple_wedge(self):
        shape_id = block_config.get_shape_id("wedge")
        smd = Smd()
        smd.read(self._blueprint[shape_id])
        annotation = Annotate(smd.get_block_list())
        min_position, max_position = smd.get_min_max_vector()
        marked, border = annotation.flood(min_position, min_position, max_position)
        # block_list, marked, border
        self.object = Periphery(smd.get_block_list(), marked=marked, border=border)
        periphery = self.object.get_periphery_simple(shape_id)
        self.assertDictEqual(periphery, self.object.peripheries[shape_id])

    def test_get_periphery_simple_tetra(self):
        shape_id = block_config.get_shape_id("tetra")
        smd = Smd()
        smd.read(self._blueprint[shape_id])
        annotation = Annotate(smd.get_block_list())
        min_position, max_position = smd.get_min_max_vector()
        marked, border = annotation.flood(min_position, min_position, max_position)
        # block_list, marked, border
        self.object = Periphery(smd.get_block_list(), marked=marked, border=border)
        periphery = self.object.get_periphery_simple(shape_id)
        self.assertDictEqual(periphery, self.object.peripheries[shape_id])

    def test_get_periphery_complex_corner(self):
        shape_id = block_config.get_shape_id("corner")
        smd = Smd()
        smd.read(self._blueprint[shape_id])
        annotation = Annotate(smd.get_block_list())
        min_position, max_position = smd.get_min_max_vector()
        marked, border = annotation.flood(min_position, min_position, max_position)
        # block_list, marked, border
        self.object = Periphery(smd.get_block_list(), marked=marked, border=border)
        periphery = self.object.get_periphery_complex(shape_id)
        self.assertSetEqual(set(periphery.keys()), set(self.object.peripheries[shape_id].keys()))

    def test_get_periphery_complex_hepta(self):
        shape_id = block_config.get_shape_id("hepta")
        smd = Smd()
        smd.read(self._blueprint[shape_id])
        annotation = Annotate(smd.get_block_list())
        min_position, max_position = smd.get_min_max_vector()
        marked, border = annotation.flood(min_position, min_position, max_position)
        # block_list, marked, border
        self.object = Periphery(smd.get_block_list(), marked=marked, border=border)
        periphery = self.object.get_periphery_complex(shape_id)
        # for periphery_index, periphery_shapes in periphery.items():
        #     print(periphery_index, ": {")
        #     for periphery_shape, periphery_orientations in periphery_shapes.items():
        #         print("\t", periphery_shape, ": {")
        #         for periphery_orientation, orientation in periphery_orientations.items():
        #             # axis_rotation, rotations = orientation
        #             print("\t\t", periphery_orientation, ": ", orientation, ",")
        #         print("\t", "},")
        #     print("},")
        self.assertSetEqual(set(periphery.keys()), set(self.object.peripheries[shape_id].keys()))