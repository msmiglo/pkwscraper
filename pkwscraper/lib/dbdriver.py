
import os
import random

import pandas as pd


EXTENSIONS = ['csv', 'xls', 'xlsx']


class Table:
    """
    `Table` can be loaded as read only - the modifying and
    deleting operations cannot be performed.

    Records can be read directly by record ID (if known). Then it
    needs to use square brackets to choose proper record.

    Searching a `Table` is done by `find` method - it can
    be called with criterions for fields with syntax:

    `find(query={"field_name_1": value_1, field_name_2: value_2})`

    This will return all records which have the given fields with
    given values.

    The returned value will be dict of records with its ID as key.
    Records are represented as "documents" which are dictionaries
    of `name: value` pairs. Names of fields in records are not
    restricted, except "_id" field, which is the record ID.

    The `find_one` method can be used to return just one result
    (first found). It takes the same kind of query. It returns the
    id of record, and the record itself (so the tuple is returned).
    If there aren't any record matching the query, the `None` is
    returned.
    NOTE: just a single None object will be returned, not a tuple.

    If the `fields` parameter is given - the returned value of `find`
    and `find_one` methods is list of results. Each result represent
    a single record that mathces the `query`. If `fields` parameter is
    just a single key name - each result will be just the key value,
    therefore a method will return list of values.

    If `fields` parameter is a list of keys (or column names) - a
    single result will be a list of the keys values from a record
    with order matching the order of `fields` parameter. Missing keys
    will also be included, containing `None` values. Therefore the
    method in such case will return list of lists of values.

    Writing records to `Table` can be done via `put` method. It takes
    the ID of new record and dict with name: value pairs. If the ID
    is not provided - a UUID is generated. If the provided ID
    duplicates an existing one - it will be overwritten. It can be
    used for modifying records also. The `__force` parameter can be
    used to write records to "read_only" Table, but still it will be
    impossible to save the changes to hadrdrive.

    Deleting or modifying records must be done manually. It is not
    supported as it is not needed for this project.

    `Table` can be converted to `pandas.DataFrame` without loss of data
    and vice versa - it can be loaded from `pandas.DataFrame`, but
    this time it is not guaranteed to support all strange features
    of `DataFrame`. Shortly said - `Table` can be converted to DF and
    back and they will stay the same.
    """
    HEX_DIGITS = list('0123456789abcdef')
    UUID_PARTS = (8, 4, 4, 4, 12)
    def __init__(self, read_only=False):
        self.__read_only = read_only
        self.__data = {}

    @classmethod
    def from_df(cls, df, limit=None, read_only=False):
        table = cls(read_only=read_only)
        try:
            print(df.columns[0])
        except IndexError:
            print(df)
        i = 0
        for _id, record_ser in df.iterrows():
            if i % 100 == 0:
                print(i, _id)
                if limit and i >= limit:
                    break
            i += 1
            record = dict(record_ser.dropna())
            table.put(record, _id=_id, _Table__force=True)
        return table

    def to_df(self):
        if self.__read_only:
            raise IOError("Table is for read only.")
        df = pd.DataFrame(self.__data).T
        df.index.name = "_id"
        return df

    @staticmethod
    def _hex_string(k):
        sample = random.choices(Table.HEX_DIGITS, k=k)
        return "".join(sample)

    @staticmethod
    def _make_uuid():
        parts = [Table._hex_string(k) for k in Table.UUID_PARTS]
        return "-".join(parts)

    def put(self, record, _id=None, __force=False):
        if self.__read_only and not __force:
            raise IOError("Table is for read only.")
        record = dict(record)
        if _id is not None:
            record["_id"] = _id
        _id = record.pop("_id", self._make_uuid())
        self.__data[_id] = record
        return _id

    def __getitem__(self, _id):
        return dict(self.__data[_id])

    @staticmethod
    def _get_id_or_field(_id, record, field):
        if field == "_id":
            return _id
        return record.get(field)

    def _find(self, query):
        if len(query) == 0:
            return dict(self.__data)
        result = {}
        for _id, record in self.__data.items():
            if all(key in record and record[key] == value
                   for key, value in query.items()):
                result[_id] = dict(record)
        return result

    def find(self, query, fields=None):
        results = self._find(query)
        if fields is None:
            return results
        if isinstance(fields, str):
            return [self._get_id_or_field(_id, record, fields)
                    for _id, record in results.items()]
        if isinstance(fields, list):
            return [[self._get_id_or_field(_id, record, field)
                    for field in fields]
                    for _id, record in results.items()]
        raise TypeError(f"`fields` should be of one of types: "
                        "`None`, `str` or `list`. got: {type(fields)}")

    def _find_one(self, query):
        for _id, record in self.__data.items():
            if all(key in record and record[key] == value
                   for key, value in query.items()):
                return _id, dict(record)

    def find_one(self, query, fields=None):
        one = self._find_one(query)
        if one is None:
            return None
        _id, record = one
        if fields is None:
            return _id, record
        if isinstance(fields, str):
            return self._get_id_or_field(_id, record, fields)
        if isinstance(fields, list):
            return [self._get_id_or_field(_id, record, field)
                    for field in fields]
        raise TypeError(f"`fields` should be of one of types: "
                        "`None`, `str` or `list`. got: {type(fields)}")


class DbDriver:
    """
    `DbDriver` operates on harddrive directories. One directory can be
    treated as one DB. Directory contains `Tables` represented by `csv` files.

    `DbDriver` loads or creates a DB on harddrive. DBs opened with "read_only"
    parameter set to `True`, will only allow to read data. `Tables` however can be
    modified by `put` method with `__force` parameter, but the changes cannot
    be saved to harddrive anyway.

    `Tables` can be accessed by square brackets by its name.

    DB can have `Table` added or deleted by `create_table` and `delete_table`
    methods, respectively.

    The `load_tables` method allows to load DB from harddrive, which is done in
    constructor anyway.

    The `dump_tables` method will save changes to harddrive.
    NOTE: when ending work with DbDriver, the changes will not be saved
    automatically. Each time the work needs to be saved - the `dump_tables`
    method must be called.
    - init
    - delete db
    - delete table
    - make table
    - load tables - make private maybe
    - dump_tables - delete not present tables maybe or register which to delete

    if the database is read only - it can be loaded from disc but not be changed
    otherwise all changes are saved to disc only when dump_tables() called
    """
    def __init__(self, db_directory, limit=None, read_only=False):
        self.delete_access_code = None
        self.limit = limit
        self.__read_only = read_only
        self.__dropped_tables = []
        
        self.db_directory = db_directory
        self.__tables = {}
        if os.path.exists(db_directory):
            self.load_tables()
        else:
            if self.__read_only:
                raise IOError("DB for read does not exist.")
            # TODO - test it maybe
            os.makedirs(db_directory, exist_ok=True)

    def __getitem__(self, name):
        return self.__tables[name]

    def __del__(self, access_code=None):
        # IT IS CALLED AFTER EXITING SCOPE
        print('entered deleting')
        if access_code is None or self.__read_only:
            return
        if access_code == self.delete_access_code:
            # REMOVE TO THE FIRST LEVEL
            for name in self.__tables:
                filepath = self._filepath(name)
                if os.path.exists(filepath):
                    os.remove(filepath)
            os.rmdir(self.db_directory)
            print("Directory with data base deleted.")
            return
        print("Incorrect access code, directory was not deleted.")

    def _filepath(self, name):
        filename = f"{name}.csv"
        filepath = os.path.join(self.db_directory, filename)
        return filepath

    @staticmethod
    def _load_csv(filepath):
        try:
            table_df = pd.read_csv(filepath, sep=";", index_col="_id")
        except ValueError:
            table_df = pd.read_csv(filepath, sep=";")
            table_df.index.name = "_id"
        return table_df

    @staticmethod
    def _load_excel(filepath):
        # MAKE TESTS
        book = xlrd.open_workbook(filepath)
        sheet = book.sheets()[0]
        n_rows = sheet.nrows
        column_names = sheet.row(0)
        column_names = [col.value for col in column_names]

        data = []
        for i in range(1, n_rows):
            row = sheet.row(i)
            record = {
                column_names[j]: cell.value
                for j, cell in enumerate(row)
            }
            data.append(record)

        table_df = pd.DataFrame(data)
        if column_names[0] == "_id":
            table_df = table_df.set_index("_id")
        return table_df

    def load_tables(self):
        for filename in os.listdir(self.db_directory):
            # check extension
            if not any(filename.endswith("."+ext) for ext in EXTENSIONS):
                continue

            # load file
            print()
            print(filename)
            filepath = os.path.join(self.db_directory, filename)
            if filename.endswith(".csv"):
                table_df = self._load_csv(filepath)
            elif filename.endswith(".xls"):
                table_df = self._load_excel(filepath)
            elif filename.endswith(".xlsx"):
                table_df = self._load_excel(filepath)

            # create table
            name = os.path.splitext(filename)[0]
            table = Table.from_df(table_df, limit=self.limit,
                                  read_only=self.__read_only)
            self.__tables[name] = table

    def dump_tables(self):
        """
        Delete from harddrive the `csv` files corresponding to
        deleted `Tables`. Overwrite other `Tables`.
        """
        # TODO - test it
        if self.__read_only:
            raise IOError("DB is for reading only.")
        for deleted_name in self.__dropped_tables:
            # TODO - reset state (ie empty the dropped tables list)
            filepath = self._filepath(deleted_name)
            if os.path.exists(filepath):
                os.remove(filepath)
        for name, table in self.__tables.items():
            print(f'dumping table "{name}", records: {len(table.find({}))}')
            filepath = self._filepath(name)
            # TODO - test it
            table.to_df().to_csv(filepath, sep=";")

    def create_table(self, name):
        if self.__read_only:
            raise IOError("DB is for reading only.")
        table = Table()
        self.__tables[name] = table
        if name in self.__dropped_tables:
            self.__dropped_tables.remove(name)

    def delete_table(self, name):
        if self.__read_only:
            raise IOError("DB is for reading only.")
        self.__tables.pop(name)
        self.__dropped_tables.append(name)

    def access_delete(self):
        if self.__read_only:
            raise IOError("DB is for reading only.")
        characters_list = ("1234567890`~!@#$%^&*()_+=-[]\;',./"
                           "{}|:\"<>?QWERTYUIOPLKJHGFDSAZXCVBNM")
        access_code = random.choices(population=characters_list, k=10)
        access_code = "".join(access_code)
        self.delete_access_code = access_code
        return f"The delete access code [characters 43-53]: {access_code}"
