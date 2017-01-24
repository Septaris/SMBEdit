from unittest import TestCase
from lib.smblueprint.smd3.smdblock.block import Block

__author__ = 'Peter Hofmann'


class DefaultSetup(TestCase):
    """
    @type object: Block
    """

    def __init__(self, methodName='runTest'):
        super(DefaultSetup, self).__init__(methodName)
        self.object = None

    def setUp(self):
        self.object = Block()
        # wedge 599 0, 0, 0, 3
        # corner 600
        # hepta 601
        # tetra 602
        self.object.update(
            block_id=599,
            hit_points=75,
            active=None,
            block_side_id=None,
            bit_19=0,
            bit_23=0,
            bit_22=0,
            rotations=3
        )

    def tearDown(self):
        self.object = None
        # if os.path.exists(self.directory_output):
        #     os.rmdir(self.directory_output)


class TestBlock(DefaultSetup):
    def test_get_id(self):
        self.assertEqual(self.object.get_id(), 599)

    def test_get_hit_points(self):
        self.assertEqual(self.object.get_id(), 100)

    def test_get_style(self):
        self.assertEqual(self.object.get_style(), 1)

    def test_is_active(self):
        self.assertFalse(self.object.is_active())

    def test__get_active_value(self):
        self.fail()

    def test_get_orientation(self):
        self.fail()

    def test_get_int_24bit(self):
        self.fail()

    def test_set_int_24bit(self):
        self.fail()

    def test_convert_to_type_6(self):
        self.fail()

    def test_update(self):
       self.fail()

    def test_set_id(self):
        self.fail()

    def test_set_hit_points(self):
        self.fail()

    def test_set_active(self):
        self.fail()

    def test_mirror(self):
        self.fail()
