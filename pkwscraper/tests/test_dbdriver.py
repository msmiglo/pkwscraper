
import os
import shutil
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

import numpy as np
from pandas import DataFrame, Series

from pkwscraper.lib.dbdriver import DbDriver, Record, Table


'''
def assertUUID(self, string):
    """ UUID length changed for performance """
    self.assertEqual(string[8], "-")
    self.assertEqual(string[13], "-")
    self.assertEqual(string[18], "-")
    self.assertEqual(string[23], "-")
    s = string.replace("-", "")
    self.assertEqual(len(s), 32)
    self.assertSetEqual(set(s)-set("1234567890abcdef"), set())
'''

def assertUUID(self, string):
    self.assertEqual(string[6], "-")
    self.assertEqual(string[11], "-")
    s = string.replace("-", "")
    self.assertEqual(len(s), 14)
    self.assertSetEqual(set(s)-set("1234567890abcdef"), set())


class TestUUID(TestCase):
    '''
    def test_uuid(self):
        """ UUID length changed for performance """
        assertUUID(self, "ab4b42d3-2bcd-0a0c-c30b-f06988fdbc12")
        with self.assertRaises(AssertionError):
            assertUUID(self, "ab4b42d3-2bcd-0a0c-cX0b-f06988fdbc12")
        with self.assertRaises(AssertionError):
            assertUUID(self, "ab4b42d3-2bcd-0a0c-c30bf06988fdbc12")
        uuid = Table._make_uuid()
        assertUUID(self, uuid)
    '''

    def test_uuid(self):
        assertUUID(self, "ab4b42-2bcd-0a0c")
        with self.assertRaises(AssertionError):
            assertUUID(self, "ab4b42-2bXd-0a0c")
        with self.assertRaises(AssertionError):
            assertUUID(self, "ab4b42-2bcd0a0c")
        uuid = Record._make_uuid()
        assertUUID(self, uuid)


class TestRecord(TestCase):
    """
    - test init
    - test from dict            # TODO
    - test from dict no id      # TODO
    - test from df dict item    # TODO
    - test get id
    - test get field
    - test get item
    - test get fields lists
    - test wrong fields
    - test to id dict
    - test check condition
    - test eq
    """
    def setUp(self):
        self.rec = Record({"num": 5, "char": "A"}, _id=123)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertDictEqual(self.rec._Record__data, {"num": 5, "char": "A"})
        self.assertEqual(self.rec._id, 123)

    def test_from_dict(self):
        rec_2 = Record.from_dict(
            {"num": 6, "char": "B", "_id": 456})
        self.assertDictEqual(rec_2._Record__data, {"num": 6, "char": "B"})
        self.assertEqual(rec_2._id, 456)

        rec_3 = Record.from_dict(
            {"num": 7, "char": "C", "_id": 456}, _id=789)
        self.assertDictEqual(rec_3._Record__data, {"num": 7, "char": "C"})
        self.assertEqual(rec_3._id, 789)

    def test_from_dict_no_id(self):
        rec = Record.from_dict({"num": 5, "char": "A"})
        self.assertDictEqual(rec._Record__data, {"num": 5, "char": "A"})
        assertUUID(self, rec._id)

    def test_from_df_dict_item(self):
        rec = Record.from_df_dict_item((
            123, {"num": 5, "char": "A"}))
        self.assertDictEqual(rec._Record__data, {"num": 5, "char": "A"})
        self.assertEqual(rec._id, 123)

        rec_2 = Record.from_df_dict_item((
            456, {"num": 6, "char": "B", "1null": None, "2null": np.nan}))
        self.assertDictEqual(rec_2._Record__data, {"num": 6, "char": "B"})
        self.assertEqual(rec_2._id, 456)

        rec_3 = Record.from_df_dict_item((
            789, {"num": 0, "text": "", "bool": False}))
        self.assertDictEqual(
            rec_3._Record__data, {"num": 0, "text": "", "bool": False})
        self.assertEqual(rec_3._id, 789)

    def test_get_id(self):
        rec_id = self.rec.get_field_or_id("_id")
        self.assertEqual(rec_id, 123)

    def test_get_field(self):
        rec_field = self.rec.get_field_or_id("char")
        self.assertEqual(rec_field, "A")

    def test_get_item(self):
        rec_id = self.rec["_id"]
        rec_field = self.rec["char"]
        self.assertEqual(rec_id, 123)
        self.assertEqual(rec_field, "A")

    def test_get_fields_list(self):
        result = self.rec.get_fields_list(["char", "_id", "char", "num"])
        self.assertListEqual(rec_field, ["A", 123, "A", 5])

    def test_get_fields_list(self):
        with self.assertRaises(TypeError) as e:
            self.rec.get_fields_list(("char", "num"))
        self.assertEqual(
            e.exception.args[0],
            "`fields` should be of one of types: `None`, `str` or `list`. "
            "got: <class 'tuple'>"
        )

    def test_to_id_dict(self):
        rec_id, rec_data = self.rec.to_id_dict()
        self.assertEqual(rec_id, 123)
        self.assertDictEqual(rec_data, {"num": 5, "char": "A"})

    def test_check_condition(self):
        self.assertTrue(self.rec.check_condition({}))
        self.assertTrue(self.rec.check_condition({"char": "A"}))
        self.assertFalse(self.rec.check_condition({"char": "B"}))
        self.assertTrue(self.rec.check_condition({"char": "A", "num": 5}))
        self.assertFalse(self.rec.check_condition({"char": "A", "num": 6}))
        self.assertFalse(self.rec.check_condition({"char": "B", "num": 6}))
        self.assertFalse(self.rec.check_condition(
            {"char": "A", "other": None}))
        self.assertFalse(self.rec.check_condition({"other": "A"}))
        self.assertFalse(self.rec.check_condition({"_id": 123}))
        self.assertFalse(self.rec.check_condition({"_id": 147}))

    def test_eq(self):
        rec_2 = Record.from_dict({"char": "A", "num": 5}, _id=456)
        self.assertEqual(self.rec, rec_2)

        rec_3 = Record.from_dict({"char": "B", "num": 5}, _id=123)
        self.assertNotEqual(self.rec, rec_3)

        self.assertEqual(self.rec, {"char": "A", "num": 5})


class TestTable(TestCase):
    """
    - test put
    - test get
    - test find
    - test find multiple criteria
    - test find one
    - test find one with fields
    - test find with fields
    - test to df
    """
    def setUp(self):
        self.table = Table()
        id_1 = self.table.put({"char": "a", "num": 1, "num2": 10})
        id_2 = self.table.put({"char": "a", "num": 2, "num2": 11, "_id": "aid"})
        id_3 = self.table.put({"char": "b", "num": 3, "num2": 10}, _id="kid")
        id_4 = self.table.put({"char": "b", "num": 3, "val": 20})
        self.ids = (id_1, id_2, id_3, id_4)

    def tearDown(self):
        pass

    def test_table_put(self):
        t = Table()
        id_1 = t.put({"a": 5, "b": 9})
        assertUUID(self, id_1)
        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 5, "b": 9}
        })

        id_2 = t.put({"a": 4, "b": 8, "_id": "rid"})
        self.assertEqual(id_2, "rid")
        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 5, "b": 9},
            "rid": {"a": 4, "b": 8}
        })

        id_3 = t.put({"a": 3, "b": 7, "_id": id_1})
        self.assertEqual(id_3, id_1)
        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 3, "b": 7},
            "rid": {"a": 4, "b": 8}
        })

        id_3 = t.put({"a": 2, "b": 6}, _id=id_2)
        self.assertEqual(id_3, id_2)
        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 3, "b": 7},
            "rid": {"a": 2, "b": 6}
        })

        id_3 = t.put({"a": 0, "b": 1}, _id="lid")
        self.assertEqual(id_3, "lid")
        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 3, "b": 7},
            "rid": {"a": 2, "b": 6},
            "lid": {"a": 0, "b": 1}
        })

    def test_table_get(self):
        t = Table()

        id_1 = t.put({"a": 20, "b": 101})
        id_2 = t.put({"c": 21, "b": 102, "_id": "rid"})

        self.assertDictEqual(t._Table__data, {
            id_1: {"a": 20, "b": 101},
            "rid": {"c": 21, "b": 102},
        })
        self.assertDictEqual(t[id_1], {"a": 20, "b": 101})
        self.assertDictEqual(t[id_2], {"c": 21, "b": 102})
        with self.assertRaises(KeyError) as e:
            t["456"]
        self.assertEqual(e.exception.args[0], "456")

    def test_table_find(self):
        t = self.table
        id_1, id_2, id_3, id_4 = self.ids

        res_1 = t.find({"num": 2})
        self.assertSetEqual(set(res_1), {id_2})
        self.assertDictEqual(res_1, {
            "aid": {"char": "a", "num": 2, "num2": 11},
        })

        res_2 = t.find({"num2": 10})
        self.assertSetEqual(set(res_2), {id_1, id_3})
        self.assertDictEqual(res_2, {
            id_1: {"char": "a", "num": 1, "num2": 10},
            "kid": {"char": "b", "num": 3, "num2": 10},
        })

        res_3 = t.find({})
        self.assertEqual(len(res_3), 4)
        self.assertSetEqual(set(res_3), set(self.ids))

    def test_table_find_multiple_criteria(self):
        t = self.table
        id_1, id_2, id_3, id_4 = self.ids

        res_1 = t.find({"num": 3, "num2": 10})
        self.assertSetEqual(set(res_1), {id_3})
        self.assertDictEqual(res_1, {
            "kid": {"char": "b", "num": 3, "num2": 10},
        })

        res_2 = t.find({"num": 3, "char": "b"})
        self.assertSetEqual(set(res_2), {id_3, id_4})
        self.assertDictEqual(res_2, {
            id_4: {"char": "b", "num": 3, "val": 20},
            "kid": {"char": "b", "num": 3, "num2": 10},
        })

    def test_table_find_one(self):
        t = self.table
        id_1, id_2, id_3, id_4 = self.ids

        _id, rec = t.find_one({"num": 2})
        self.assertIn(_id, [id_2])
        self.assertDictEqual(rec, {"char": "a", "num": 2, "num2": 11})

        _id, rec = t.find_one({"num2": 10})
        self.assertIn(_id, [id_1, id_3])
        self.assertEqual(rec["num2"], 10)

        res = t.find_one({"num2": 667})
        self.assertIsNone(res)

        res = t.find_one({"xyz": 3})
        self.assertIsNone(res)

        res = t.find_one({"num": 3, "char": "a"})
        self.assertIsNone(res)

        _id, rec = t.find_one({"num": 3, "num2": 10})
        self.assertIn(_id, [id_3])
        self.assertDictEqual(rec, {"char": "b", "num": 3, "num2": 10})

        _id, rec = t.find_one({})
        self.assertIsInstance(_id, str)
        self.assertIsInstance(rec, dict)
        self.assertIn(_id, self.ids)

    def test_find_one_with_fields(self):
        t = self.table
        id_1, id_2, id_3, id_4 = self.ids

        res = t.find_one({}, "_id")
        self.assertIn(res, self.ids)

        res = t.find_one({}, ["_id"])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 1)
        self.assertIn(res[0], self.ids)

        res = t.find_one({}, ["val", "_id"])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 2)
        self.assertTrue(
            res == [None, id_1]
            or res == [None, id_2]
            or res == [None, id_3]
            or res == [20, id_4]
        )

        res = t.find_one({}, "val")
        self.assertIn(res, [None, 20])

        res = t.find_one({"num2": 11}, "_id")
        self.assertEqual(res, id_2)

        res = t.find_one({"num2": 11}, ["_id"])
        self.assertListEqual(res, [id_2])

        res = t.find_one({"num2": 11}, ["val", "_id"])
        self.assertListEqual(res, [None, id_2])

        res = t.find_one({"num2": 11}, "val")
        self.assertEqual(res, None)

    def test_find_with_fields(self):
        t = self.table
        id_1, id_2, id_3, id_4 = self.ids

        # choose all records
        res = t.find({}, "_id")
        self.assertListEqual(res, list(self.ids))

        res = t.find({}, ["_id"])
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 4)
        self.assertListEqual(res, [[id_1], [id_2], [id_3], [id_4]])

        res = t.find({}, ["num2", "_id"])
        self.assertListEqual(
            res, [[10, id_1], [11, id_2], [10, id_3], [None, id_4]])

        res = t.find({}, "num2")
        self.assertListEqual(res, [10, 11, 10, None])

        res = t.find({}, [])
        self.assertListEqual(res, [[], [], [], []])

        # find record by criteria
        res = t.find({"num2": 11}, "_id")
        self.assertListEqual(res, [id_2])

        res = t.find({"num2": 11}, ["_id"])
        self.assertListEqual(res, [[id_2]])

        res = t.find({"num2": 11}, ["num2", "_id"])
        self.assertListEqual(res, [[11, id_2]])

        res = t.find({"num2": 11}, "num2")
        self.assertListEqual(res, [11])

        res = t.find({"num2": 11}, [])
        self.assertListEqual(res, [[]])

    def test_table_to_df(self):
        t = self.table
        df = t.to_df()
        self.assertIsInstance(df, DataFrame)
        self.assertIsInstance(df.loc["kid"], Series)
        self.assertEqual(df.loc["kid"]["num2"], 10)
        t2 = Table.from_df(df)
        self.assertEqual(len(t2._Table__data), 4)
        self.assertDictEqual(t._Table__data, t2._Table__data)


class TestDbDriver(TestCase):
    """
    This is more like integration test, as it is mainly the interface
    for underlying pandas library and file system communication.

    - test get item
    - test get item no loaded
    - test filepath
    - test read only
    - test create table
    - test delete table
    - test load table names
    - test load table
    - test dump tables

    - test init not exists
    - test init nested directory
    - test init exists
    - test read only errors
    - test load csv
    - test load excel (rejected)
    - test delete
    - test whole
    """


    # ===== SETUP METHODS =====

    def setUp(self):
        # set up example data
        self.directory = "./_DB_unittesting_temp_dir_1410_1945/"
        self.csv_content_1 = """_id;num;char\n101;9;a\n102;16;b\n103;25;c"""
        self.csv_content_2 = """num;char\n36;d\n49;e\n64;f"""
        self.path_1 = os.path.join(self.directory, "first_table.csv")
        self.path_2 = os.path.join(self.directory, "second_table.csv")

        # check if there is directory left from previous tests
        if os.path.exists(self.directory):
            raise RuntimeError("Cannot operate on not-cleaned testing directory on harddrive.")

    def tearDown(self):
        # check if the testing directory was cleared by test
        if os.path.exists(self.directory):
            # remove the testing trash
            files = os.listdir(self.directory)
            if any(not fname.endswith(".csv") for fname in files):
                # unexpected files found, stop cleaning for safety measures
                raise RuntimeError("Testing directory had unexpected content.")
            filepaths = [os.path.join(self.directory, fname) for fname in files]
            [os.remove(filepath) for filepath in filepaths]
            os.rmdir(self.directory)
            # raise an error when cleaned
            raise RuntimeError("Testing directory was not cleared by test!")

    def _make_synthetic_data(self):
        os.makedirs(self.directory)
        with open(self.path_1, 'w') as f:
            f.write(self.csv_content_1)
        with open(self.path_2, 'w') as f:
            f.write(self.csv_content_2)

    def _clean_synthetic_data(self):
        os.remove(self.path_1)
        os.remove(self.path_2)
        os.rmdir(self.directory)


    # ===== UNIT TESTS =====

    def test_get_item(self):
        """ Unit test """
        dbdriver = DbDriver.__new__(DbDriver)
        table = MagicMock()
        dbdriver._DbDriver__tables = {"MyTable": table}
        dbdriver._load_table = MagicMock()

        with self.assertRaises(KeyError):
            dbdriver["NotExistingTable"]
        result = dbdriver["MyTable"]
        dbdriver._load_table.assert_not_called()
        self.assertIs(result, table)

    def test_get_item_not_loaded(self):
        """ Unit test """
        # arrange
        dbdriver = DbDriver.__new__(DbDriver)
        table = MagicMock()
        dbdriver._DbDriver__tables = {"MyTable": None}
        dbdriver._load_table = MagicMock()
        dbdriver._load_table.return_value = table
        # act
        result = dbdriver["MyTable"]
        # assert
        dbdriver._load_table.assert_called_once_with("MyTable")
        self.assertIs(result, table)

    def test_filepath(self):
        """ Unit test """
        # arrange
        dbdriver = MagicMock()
        dbdriver.db_directory = "./some_directory"
        name = "table_name"
        expected = ["./some_directory\\table_name.csv",
                    "./some_directory/table_name.csv"]
        # act
        result = DbDriver._filepath(dbdriver, name)
        # assert
        self.assertIn(result, expected)

    def test_read_only(self):
        """ Unit test """
        dbdriver = DbDriver.__new__(DbDriver)

        dbdriver._DbDriver__read_only = True
        self.assertTrue(dbdriver.read_only)
        dbdriver._DbDriver__read_only = False
        self.assertFalse(dbdriver.read_only)

        with self.assertRaises(TypeError):
            dbdriver.read_only()

    def test_create_table(self):
        """ Unit test """
        # arrange
        new_table_name = "labada"
        MockTableClass = MagicMock()
        mock_table = MagicMock()
        MockTableClass.return_value = mock_table

        mock_db = MagicMock()
        mock_db._DbDriver__read_only = False
        mock_db._DbDriver__tables = {}
        mock_db._DbDriver__dropped_tables = [new_table_name, "other"]

        # act
        with patch("pkwscraper.lib.dbdriver.Table", MockTableClass):
            DbDriver.create_table(mock_db, new_table_name)

        # assert
        self.assertDictEqual(mock_db._DbDriver__tables, {new_table_name: mock_table})
        self.assertListEqual(mock_db._DbDriver__dropped_tables, ["other"])

    def test_delete_table(self):
        """ Unit test """
        # arrange
        table_name = "labada"
        mock_table = MagicMock()
        mock_table_2 = MagicMock()

        mock_db = MagicMock()
        mock_db._DbDriver__read_only = False
        mock_db._DbDriver__tables = {
            table_name: mock_table, "other": mock_table_2}
        mock_db._DbDriver__dropped_tables = []

        # act
        DbDriver.delete_table(mock_db, table_name)

        # assert
        self.assertDictEqual(mock_db._DbDriver__tables, {"other": mock_table_2})
        self.assertListEqual(mock_db._DbDriver__dropped_tables, [table_name])

    def test_load_table_names(self):
        """ Unit test """
        # arrange
        table_filenames = ["labada.csv", "macarena.csv"]
        mock_os_listdir = MagicMock()
        mock_os_listdir.return_value = table_filenames

        mock_db = MagicMock()
        mock_db.db_directory = self.directory

        mock_db.limit = None
        mock_db._DbDriver__read_only = True
        mock_db._DbDriver__tables = {}

        # act
        with patch("pkwscraper.lib.dbdriver.os.listdir", mock_os_listdir):
            DbDriver._load_table_names(mock_db)

        # assert
        mock_os_listdir.assert_called_once_with(self.directory)

        mock_db._load_excel.assert_not_called()
        mock_db._load_csv.assert_not_called()
        mock_db._load.assert_not_called()

        self.assertDictEqual(mock_db._DbDriver__tables, {
            "labada": None,
            "macarena": None
        })

    def test_load_table(self):
        """ Unit test """
        # arrange
        table_name = "labada"
        filepath = os.path.join(self.directory, "labada.csv")

        mock_db = MagicMock()
        mock_db.db_directory = self.directory
        mock_df = MagicMock()
        mock_db._load_csv.return_value = mock_df
        mock_db._filepath.return_value = filepath

        mock_db.limit = None
        mock_db._DbDriver__read_only = True
        mock_db._DbDriver__tables = {}

        mock_table = MagicMock()
        MockTableClass = MagicMock()
        MockTableClass.from_df.return_value = mock_table

        mock_os_path_size = MagicMock()
        mock_os_path_size.return_value = 1000

        # act
        with patch("pkwscraper.lib.dbdriver.Table", MockTableClass):
            with patch("pkwscraper.lib.dbdriver.os.path.getsize",
                       mock_os_path_size):
                result = DbDriver._load_table(mock_db, table_name)

        # assert
        mock_db._filepath.assert_called_once_with(table_name)
        mock_db._load_excel.assert_not_called()
        mock_db._load_csv.assert_called_once_with(filepath)
        mock_os_path_size.assert_called_once_with(filepath)

        MockTableClass.from_df.assert_called_once_with(
            mock_df, limit=None, read_only=True)

        self.assertDictEqual(mock_db._DbDriver__tables, {
            "labada": mock_table
        })
        self.assertIs(result, mock_table)

    def test_dump_tables(self):
        """ Unit test """
        # arrange
        mock_table = MagicMock()
        mock_db = MagicMock()
        mock_db._DbDriver__read_only = False
        mock_db._DbDriver__tables = {
            "new_table": mock_table, "not_changed_table": None}
        mock_db._DbDriver__dropped_tables = ["old_table", "missing_table"]
        mock_db._filepath.side_effect = [
            "./here/old_table.csv",
            "./here/missing_table.csv",
            "./here/new_table.csv"
        ]

        mock_os = MagicMock()
        mock_os.path.exists.side_effect = [True, False]

        mock_df = MagicMock()
        mock_table.to_df.return_value = mock_df

        # act
        with patch("pkwscraper.lib.dbdriver.os", mock_os):
            DbDriver.dump_tables(mock_db)

        # assert
        mock_db._filepath.assert_has_calls([
            call("old_table"), call("missing_table"), call("new_table")])

        mock_os.path.exists.assert_has_calls([
            call("./here/old_table.csv"),
            call("./here/missing_table.csv")
        ])
        mock_os.remove.assert_called_once_with("./here/old_table.csv")

        mock_df.to_csv.assert_called_once_with("./here/new_table.csv", sep=";")

        self.assertListEqual(mock_db._DbDriver__dropped_tables, [])


    # ===== INTEGRATION TESTS =====

    def test_init_not_exists(self):
        # test error if read only and not exists
        with self.assertRaises(IOError):
            dbdriver = DbDriver(db_directory=self.directory, read_only=True)

        # test fields and creating directory
        dbdriver = DbDriver(db_directory=self.directory, limit=50)
        self.assertEqual(dbdriver.db_directory, self.directory)
        self.assertEqual(dbdriver.limit, 50)
        self.assertFalse(dbdriver._DbDriver__read_only)
        self.assertListEqual(dbdriver._DbDriver__dropped_tables, [])
        self.assertDictEqual(dbdriver._DbDriver__tables, {})
        self.assertTrue(os.path.exists(self.directory))

        # clean up
        os.rmdir(self.directory)

    def test_init_nested_directory(self):
        db_directory = self.directory + "other/directory/level/"

        # prepare DB
        dbdriver = DbDriver(db_directory=db_directory)
        dbdriver.create_table("test")
        dbdriver.dump_tables()

        # assert
        self.assertEqual(dbdriver.db_directory, db_directory)
        self.assertTrue(os.path.exists(db_directory))
        self.assertTrue(os.path.exists(db_directory + "test.csv"))

        # clean up
        shutil.rmtree(self.directory)

        self.assertFalse(os.path.exists(db_directory))

    def test_init_exists(self):
        # create some synthetic tables data
        self._make_synthetic_data()

        # test tables data
        dbdriver = DbDriver(db_directory=self.directory, read_only=True)
        self.assertEqual(len(dbdriver._DbDriver__tables), 2)
        self.assertDictEqual(dbdriver._DbDriver__tables, {
            "first_table": None, "second_table": None})

        dbdriver["first_table"]
        dbdriver["second_table"]

        self.assertDictEqual(
            dbdriver._DbDriver__tables["first_table"]._Table__data, {
                101: {'num': 9,  'char': 'a'},
                102: {'num': 16, 'char': 'b'},
                103: {'num': 25, 'char': 'c'},
        })
        self.assertDictEqual(
            dbdriver._DbDriver__tables["second_table"]._Table__data, {
                0: {'num': 36, 'char': 'd'},
                1: {'num': 49, 'char': 'e'},
                2: {'num': 64, 'char': 'f'},
        })

        # clean up
        self._clean_synthetic_data()

    def test_read_only_errors(self):
        # arrange
        self._make_synthetic_data()
        db = DbDriver(self.directory, read_only=True)

        # saving to harddrive
        with self.assertRaises(IOError) as e:
            db.dump_tables()
        self.assertEqual(e.exception.args[0], "DB is for reading only.")

        # adding table
        with self.assertRaises(IOError) as e:
            db.create_table("test_table")
        self.assertEqual(e.exception.args[0], "DB is for reading only.")

        # puting records
        with self.assertRaises(IOError) as e:
            db["first_table"].put({"c": 5})
        self.assertEqual(e.exception.args[0], "Table is for read only.")

        # dropping table
        with self.assertRaises(IOError) as e:
            db.delete_table("first_table")
        self.assertEqual(e.exception.args[0], "DB is for reading only.")

        # obtaining deleting access code
        with self.assertRaises(IOError) as e:
            db.get_deleting_access()
        self.assertEqual(e.exception.args[0], "DB is for reading only.")

        # deleting db
        with self.assertRaises(IOError) as e:
            db.delete(access_code="something")
        self.assertEqual(e.exception.args[0], "DB is for reading only.")

        # clean up
        self._clean_synthetic_data()

    def test_load_csv(self):
        # arrange
        self._make_synthetic_data()

        # act
        df_1 = DbDriver._load_csv(self.path_1)
        df_2 = DbDriver._load_csv(self.path_2)

        # assert
        self.assertEqual(len(df_1.columns), 2)
        self.assertEqual(len(df_1), 3)
        self.assertEqual(df_1.index.name, "_id")
        self.assertEqual(len(df_2.columns), 2)
        self.assertEqual(len(df_2), 3)
        self.assertEqual(df_2.index.name, "_id")

        # absterge
        self._clean_synthetic_data()

    def test_load_excel(self):
        """ DEPRECATED """
        pass

    def test_delete(self):
        # arrange
        self._make_synthetic_data()
        self.assertTrue(os.path.exists(self.directory))
        dbdriver = DbDriver(db_directory=self.directory)
        dbdriver.create_table("foo")
        dbdriver.dump_tables()
        dbdriver.delete_table("foo")
        # act
        deleting_access_code = dbdriver.get_deleting_access()
        deleting_access_code = deleting_access_code[43:53]
        dbdriver.delete(deleting_access_code)
        # assert
        self.assertFalse(os.path.exists(self.directory))

    def test_whole(self):
        """ Main integration test """
        # arrange
        record_1 = {"a": 1, "b": 2}
        record_2 = {"c": 8, "b": 4}

        # make and save db
        db = DbDriver(db_directory=self.directory)
        db.create_table("my_table")
        id_1 = db["my_table"].put(record_1)
        id_2 = db["my_table"].put(record_2)
        db.dump_tables()

        # open the db again
        db2 = DbDriver(db_directory=self.directory)
        my_table = db2["my_table"]
        records = my_table.find({})
        self.assertEqual(len(records), 2)
        self.assertDictEqual(records[id_1], record_1)
        self.assertDictEqual(records[id_2], record_2)

        # remove db
        deleting_access_code = db2.get_deleting_access()
        deleting_access_code = deleting_access_code[43:53]
        db2.delete(deleting_access_code)
        assert not os.path.exists(self.directory)


if __name__ == "__main__":
    main()
