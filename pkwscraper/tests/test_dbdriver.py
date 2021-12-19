
import os
from unittest import main, skip, TestCase

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


    '''
    id_1 = self.table.put({"char": "a", "num": 1, "num2": 10})
    id_2 = self.table.put({"char": "a", "num": 2, "num2": 11, "_id": "aid"})
    id_3 = self.table.put({"char": "b", "num": 3, "num2": 10}, _id="kid")
    id_4 = self.table.put({"char": "b", "num": 3, "val": 20})
    '''

    def test_table_to_df(self):
        t = self.table
        df = t.to_df()
        self.assertIsInstance(df, DataFrame)
        self.assertIsInstance(df.loc["kid"], Series)
        self.assertEqual(df.loc["kid"]["num2"], 10)
        t2 = Table.from_df(df)
        self.assertEqual(len(t2._Table__data), 4)
        self.assertDictEqual(t._Table__data, t2._Table__data)



















@skip
class TestDbDriver(TestCase):
    """
    - test not deleting
    - test db driver
    - test load ids
    - test read only
    - test existing db
    """
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_not_deleting(self):
        path = "./testing_tables_2/"
        def inner():
            db = DbDriver(db_directory=path)
            db.create_table("names")
            db.dump_tables()
        inner()
        print("after calling inner scope")
        assert os.path.exists(path)
        
        db2 = DbDriver(db_directory=path)
        delete_access_code = db2.access_delete()
        delete_access_code = delete_access_code[43:53]
        db2.__del__(delete_access_code)
        assert not os.path.exists(path)

    def test_db_driver(self):
        path = "./testing_tables/"
        db = DbDriver(db_directory=path)
        assert os.path.exists(path)
        db.create_table("names")
        db.dump_tables()
        del db
        assert os.path.exists(path)
        db2 = DbDriver(db_directory=path)
        delete_access_code = db2.access_delete()
        print(delete_access_code)
        delete_access_code = delete_access_code[43:53]
        print(delete_access_code)
        # TODO - RMDIR RECURSIVE NEEDED
        db2.__del__(delete_access_code)
        del db2
        
        assert not os.path.exists(path)
        try:
            print(db2)
            raise RuntimeError('error not raised')
        except UnboundLocalError:
            pass

    def test_db_driver_load_ids(self):
        # arrange
        record_1 = {"a": 1, "b": 2}
        record_2 = {"c": 8, "b": 4}

        # make and save db
        path = "./testing_tables/"
        db = DbDriver(db_directory=path)
        db.create_table("my_table")
        id_1 = db["my_table"].put(record_1)
        id_2 = db["my_table"].put(record_2)
        db.dump_tables()
        del db

        # open the db again
        db = DbDriver(db_directory=path)
        my_table = db["my_table"]
        records = my_table.find({})
        assert len(records) == 2
        print(list(records))
        assert records[id_1] == record_1
        assert records[id_2] == record_2

        # remove db
        delete_access_code = db.access_delete()
        delete_access_code = delete_access_code[43:53]
        db.__del__(delete_access_code)
        del db

    def test_db_read_only(self):
        path = "./testing_tables/"
        # test non-existing
        try:
            db = DbDriver(path, read_only=True)
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "DB for read does not exist."

        # create testing db
        db = DbDriver(path)
        db.create_table("my_table")
        id_1 = db["my_table"].put({"a": 1, "b": 2})
        db.dump_tables()
        del db

        # test saving of read only
        db = DbDriver(path, read_only=True)

        try:
            db.dump_tables()
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "DB is for reading only."

        try:
            db.create_table("test_table")
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "DB is for reading only."

        try:
            db["my_table"].put({"c": 5})
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "Table is for read only."

        try:
            db.delete_table("my_table")
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "DB is for reading only."

        try:
            db.access_delete()
            raise RuntimeError('error not raised')
        except IOError as e:
            assert str(e) == "DB is for reading only."

        # remove db
        db = DbDriver(path)
        delete_access_code = db.access_delete()
        delete_access_code = delete_access_code[43:53]
        db.__del__(delete_access_code)
        del db

    ##def test_existing_db():
    ##    source_db = DbDriver(db_directory="./xlsx_data", limit=500, read_only=True)
    ##    print(list(source_db._DbDriver__tables))
    ##    id_s = list(source_db["okregi_sejm"].find({}))
    ##    my_id = id_s[-1]
    ##    print(source_db["okregi_sejm"].get(my_id))


if __name__ == "__main__":
    main()

