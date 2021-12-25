
import os
from unittest import main, skip, TestCase
from unittest.mock import call, MagicMock, patch

from pandas import DataFrame, Series

from pkwscraper.lib.dbdriver import DbDriver, Table


class TestTable(TestCase):
    """
    - test uuid
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

    def assertUUID(self, string):
        self.assertEqual(string[8], "-")
        self.assertEqual(string[13], "-")
        self.assertEqual(string[18], "-")
        self.assertEqual(string[23], "-")
        s = string.replace("-", "")
        self.assertEqual(len(s), 32)
        self.assertSetEqual(set(s)-set("1234567890abcdef"), set())

    def test_uuid(self):
        self.assertUUID("ab4b42d3-2bcd-0a0c-c30b-f06988fdbc12")
        with self.assertRaises(AssertionError):
            self.assertUUID("ab4b42d3-2bcd-0a0c-cX0b-f06988fdbc12")
        with self.assertRaises(AssertionError):
            self.assertUUID("ab4b42d3-2bcd-0a0c-c30bf06988fdbc12")
        uuid = Table._make_uuid()
        self.assertUUID(uuid)

    def test_table_put(self):
        t = Table()
        id_1 = t.put({"a": 5, "b": 9})
        self.assertUUID(id_1)
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
    - test filepath
    - test create table
    - test delete table
    - test load tables
    - test dump tables

    - test init not exists
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
            raise RuntimeError("Cannot operate on testing directory on harddrive.")

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
        dbdriver = DbDriver.__new__(DbDriver) # MagicMock(DbDriver)
        table = MagicMock()
        dbdriver._DbDriver__tables = {"MyTable": table}

        with self.assertRaises(KeyError):
            dbdriver["NotExistingTable"]
        result = dbdriver["MyTable"]
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
        mock_db._DbDriver__tables = {table_name: mock_table, "other": mock_table_2}
        mock_db._DbDriver__dropped_tables = []

        # act
        DbDriver.delete_table(mock_db, table_name)

        # assert
        self.assertDictEqual(mock_db._DbDriver__tables, {"other": mock_table_2})
        self.assertListEqual(mock_db._DbDriver__dropped_tables, [table_name])

    def test_load_tables(self):
        """ Unit test """
        # arrange
        table_filenames = ["labada.csv", "macarena.csv"]
        mock_os_listdir = MagicMock()
        mock_os_listdir.return_value = table_filenames

        mock_db = MagicMock()
        mock_db.db_directory = self.directory
        mock_df = MagicMock()
        mock_df_2 = MagicMock()
        mock_db._load_csv.side_effect = [mock_df, mock_df_2]

        mock_db.limit = None
        mock_db._DbDriver__read_only = True
        mock_db._DbDriver__tables = {}

        mock_table = MagicMock()
        mock_table_2 = MagicMock()
        MockTableClass = MagicMock()
        MockTableClass.from_df.side_effect = [mock_table, mock_table_2]

        # act
        with patch("pkwscraper.lib.dbdriver.Table", MockTableClass):
            with patch("pkwscraper.lib.dbdriver.os.listdir", mock_os_listdir):
                DbDriver._load_tables(mock_db)

        # assert
        mock_os_listdir.assert_called_once_with(self.directory)

        mock_db._load_excel.assert_not_called()
        mock_db._load_csv.assert_has_calls([
            call(os.path.join(self.directory, "labada.csv")),
            call(os.path.join(self.directory, "macarena.csv"))
        ])

        MockTableClass.from_df.assert_has_calls([
            call(mock_df, limit=None, read_only=True),
            call(mock_df_2, limit=None, read_only=True)
        ])

        self.assertDictEqual(mock_db._DbDriver__tables, {
            "labada": mock_table,
            "macarena": mock_table_2
        })

    def test_dump_tables(self):
        """ Unit test """
        # arrange
        mock_table = MagicMock()
        mock_db = MagicMock()
        mock_db._DbDriver__read_only = False
        mock_db._DbDriver__tables = {"new_table": mock_table}
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

    def test_init_exists(self):
        # create some synthetic tables data
        self._make_synthetic_data()

        # test tables data
        dbdriver = DbDriver(db_directory=self.directory, read_only=True)
        self.assertEqual(len(dbdriver._DbDriver__tables), 2)
        self.assertDictEqual(dbdriver._DbDriver__tables["first_table"]._Table__data, {
            101: {'num': 9,  'char': 'a'},
            102: {'num': 16, 'char': 'b'},
            103: {'num': 25, 'char': 'c'},
        })
        self.assertDictEqual(dbdriver._DbDriver__tables["second_table"]._Table__data, {
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
        dbdriver.create_table("names")
        dbdriver.dump_tables()
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
