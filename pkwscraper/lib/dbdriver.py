
import os
import random

import pandas as pd


EXTENSIONS = ['csv', 'xls', 'xlsx']
SHORT_UUID = True


class Record:
    """
    `Record` class contains single record of table with its ID.

    If no ID is given in contructor - it is created as UUID. This
    prevents mistakes made when one tries to choose record by ID
    that comes from another table.
    """
    HEX_DIGITS = list('0123456789abcdef')
    if SHORT_UUID:
        # for memory performance
        UUID_PARTS = (6, 4, 4)
    else:
        UUID_PARTS = (8, 4, 4, 4, 12)

    def __init__(self, record, _id):
        self.__data = record
        self._id = _id

    @classmethod
    def from_dict(cls, record, _id=None):
        """ Just regular way of creating new Record. """
        # copy dict
        record = dict(record)

        # get record id and remove it from record
        record_id = record.pop("_id", None)
        if _id is None:
            _id = record_id
        if _id is None:
            _id = cls._make_uuid()

        # make record
        return cls(record, _id)

    @classmethod
    def from_df_dict_item(cls, item):
        """
        For creating records when reading a file - improved performance.
        """
        # unpack dict item
        _id, record = item

        # drop null values
        record = {name: value
                for name, value in record.items()
                if not pd.isna(value)}

        # make record
        return Record(record, _id)

    @staticmethod
    def _hex_string(k):
        """ Return k-length hex-digit string. """
        sample = random.choices(Record.HEX_DIGITS, k=k)
        return "".join(sample)

    @staticmethod
    def _make_uuid():
        """ This is just pretending to be UUID. """
        parts = [Record._hex_string(k) for k in Record.UUID_PARTS]
        return "-".join(parts)

    def get_field_or_id(self, name):
        """
        returns id or value of field
        """
        if name == "_id":
            return self._id
        return self.__data.get(name)

    def get_fields_list(self, fields):
        """
        return list of field values
        """
        # choose one value
        if isinstance(fields, str):
            return self.get_field_or_id(fields)

        # choose only values matching given fields
        if isinstance(fields, list):
            return [self.get_field_or_id(field) for field in fields]

        raise TypeError(f"`fields` should be of one of types: "
                        f"`None`, `str` or `list`. got: {type(fields)}")

    def to_id_dict(self):
        """
        return id and dict of other key-value pairs
        """
        return self._id, dict(self.__data)

    def to_dict(self):
        """
        return copy of dict data
        """
        return dict(self.__data)

    def check_condition(self, query_dict):
        """
        checks if record matches given query
        """
        return all(key in self.__data and self.__data[key] == value
                   for key, value in query_dict.items())

    def __getitem__(self, name):
        return self.get_field_or_id(name)

    def __eq__(self, other):
        if isinstance(other, Record):
            return self.__data == other.__data
        if isinstance(other, dict):
            return self.__data == other
        return false


class Table:
    """
    `Table` class represents DB Table containing records with given
    id's. Constructor creates empty table. `from_df` method gets
    data from `pandas.DataFrame` object.

    `Table` can be created as read only - the modifying and
    deleting operations cannot be performed.

    Records can be read directly by record ID (if known). Then it
    needs to use square brackets to choose proper record.

    Searching a `Table` is done by `find` method - it can
    be called with criterions for fields with syntax:

    `find(query={field_name_1: value_1, field_name_2: value_2})`

    This will return all records which have the given fields with
    given values. The return structure is `dict` of records with its
    ID as key. Records are represented as "documents" which are
    dictionaries of `name: value` pairs. Names of fields in records
    can be anything, except "_id" field, which is the record ID.

    The `find_one` method can be used to return just one result
    (first found). It takes the same kind of query. It returns the
    id of record, and the record itself (so the tuple is returned).
    If there isn't any record matching the query, the `None` is
    returned.
    NOTE: just a single None object will be returned, not a tuple.

    If the `fields` parameter is given - the returned value of `find`
    and `find_one` methods is list of results. Each result represent
    a single record that mathces the `query`. If `fields` parameter is
    just a single key name - each result will be just the corresponding
    value, therefore a method will return list of values.

    If `fields` parameter is a list of keys (or column names) - a
    single result will be a list of the keys values from a record,
    with order matching the order of `fields` parameter. Missing keys
    will also be included, containing `None` values. Therefore the
    method in such case will return list of lists of values.

    Writing records to `Table` can be done via `put` method. It takes
    the ID of new record and dict with name: value pairs. If the ID
    is not provided - a UUID is generated. If the provided ID
    duplicates an existing one - the record will be overwritten. It
    can be used for modifying records also.

    Deleting or modifying records must be done manually. It is not
    supported as it is not needed for this project.

    `Table` can be converted to `pandas.DataFrame` without loss of data
    and vice versa - it can be loaded from `pandas.DataFrame`, but
    this time it is not guaranteed to support all strange features
    of `DataFrame`. Shortly said - `Table` can be converted to DF and
    back and it will stay the same.
    """
    def __init__(self, read_only=False):
        self.__read_only = read_only
        self.__data = {}

    @classmethod
    def from_df(cls, df, limit=None, read_only=False):
        """
        df: pandas.DataFrame - data structure containing table data
        limit: None/int - maximum number of records to be loaded
        read_only: bool - if table has to be protected from changing

        returns: Table
        """
        # create new table
        table = cls(read_only=read_only)

        # convert to python data structures
        dict_data = df.iloc[:limit].T.to_dict('dict')

        # make records
        records = [Record.from_df_dict_item(item)
                   for item in dict_data.items()]

        # make records dictionary
        records_data = {rec._id: rec for rec in records}

        # assign to new table
        table.__data = records_data
        return table

    def to_df(self):
        """
        returns: pandas.DataFrame
        """
        # check read only
        if self.__read_only:
            raise IOError("Table is for read only.")

        # convert data to dicts
        data = dict(record.to_id_dict()
                    for record in self.__data.values())

        # make data frame
        df = pd.DataFrame(data).T
        df.index.name = "_id"
        return df

    def put(self, record, _id=None, __force=False):
        """
        Put record in table. Note that `_id` is not stored in
        record dict, but as a record key in table. The `_id` can
        be however passed in record dict, and it will be used
        as a record ID, but the explicit passing of `_id` argument
        has the priority.

        record: dict - record with `name: value` pairs
        _id: key for record or None

        returns: record ID
        """
        # REFACTOR TODO - MAKE A RECORD INSTANCE FIRST, THAN GET ITS ID
        # check read only
        if self.__read_only and not __force:
            raise IOError("Table is for read only.")

        # make record
        record = Record.from_dict(record, _id)

        # add record to data
        _id = record._id
        self.__data[_id] = record
        return _id





        '''# copy dict
        record = dict(record)

        # get record id and remove it from record
        record_id = record.pop("_id", None)
        if _id is None:
            _id = record_id
        if _id is None:
            # usign UUID prevents from mistakes when someone choses
            # records, using ID from another table
            _id = self._make_uuid()

        # add record to data
        self.__data[_id] = record
        return _id'''

    def __getitem__(self, _id):
        return self.__data[_id].to_dict()

    '''@staticmethod
    def _get_id_or_field(_id, record, field):
        if field == "_id":
            return _id
        return record.get(field)'''

    '''def _find(self, query):
        # return all if no criterions
        if len(query) == 0:
            return dict(self.__data)
        # copy matching results and return
        result = {}
        for _id, record in self.__data.items():
            if all(key in record and record[key] == value
                   for key, value in query.items()):
                result[_id] = dict(record)
        return result'''

    def find(self, query, fields=None):
        """
        query: dict - dictionary with fields and values to be matched
            in searched records
        fields: key/list/None - keys that has to be included in results

        returns: dict/list
        """
        # get records matching query
        records = [rec for rec in self.__data.values()
                   if rec.check_condition(query)]

        # handle `fields` argument
        if fields is None:
            # return raw results if fields not given
            results = dict(rec.to_id_dict() for rec in records)
        elif isinstance(fields, str):
            # chose one value from each record
            results = [rec[fields] for rec in records]
        elif isinstance(fields, list):
            # chose only values matching given fields
            results = [rec.get_fields_list(fields) for rec in records]
        else:
            raise TypeError(f"`fields` should be of one of types: "
                            f"`None`, `str` or `list`. got: {type(fields)}")

        return results

    def _find_one(self, query):
        for record in self.__data.values():
            if record.check_condition(query):
                return record
            '''if all(key in record and record[key] == value
                   for key, value in query.items()):
                return _id, dict(record)'''

    def find_one(self, query, fields=None):
        """
        query: dict - dictionary with fields and values to be matched
            in searched records
        fields: key/list/None - keys that has to be included in results

        returns: dict/value/None
        """
        # get raw result
        record = self._find_one(query)
        # if no result found
        if record is None:
            return None
        # handle `fields` parameter
        if fields is None:
            # if fields not given - return raw result
            result = record.to_id_dict()
        elif isinstance(fields, str):
            # chose one value
            result = record[fields]
        elif isinstance(fields, list):
            # chose only values matching given fields
            result = record.get_fields_list(fields)
        else:
            raise TypeError(f"`fields` should be of one of types: "
                            f"`None`, `str` or `list`. got: {type(fields)}")
        return result


class DbDriver:
    """
    `DbDriver` is a class that implements over-simplified NoSQL DB
    engine based on pure python data structures. Syntax of queries is
    inspired by MongoDB.

    It operates on harddrive directories. One directory can be treated
    as one DB. Directory contains `Tables` represented by `csv` files.

    `DbDriver` loads or creates a DB on harddrive. DBs opened with
    "read_only" parameter set to `True`, will only allow to read data.
    `Tables` can be accessed by square brackets by its name.

    DB can have `Table` added or deleted by `create_table` and
    `delete_table` methods, respectively.

    The `load_tables` method allows to load DB from harddrive, which
    is done in constructor anyway.

    The `dump_tables` method will save changes to harddrive.
    NOTE: when ending work with DbDriver, the changes will not be
    saved automatically. Each time the work needs to be saved - the
    `dump_tables` method must be called.
    """
    def __init__(self, db_directory, limit=None, read_only=False):
        """
        db_directory: str - directory which contains DB tables
        limit: int/None - max numbers of records to be loaded in one table
        read_only: bool - whether to protect DB from changes
        """
        # initialize attributes
        self.delete_access_code = None
        self.limit = limit
        self.__read_only = read_only
        self.__dropped_tables = []

        # TODO - consider adding option "local"/None or something
        # that will indicate the DB is only in runtime memory, not
        # stored on harddrive
        self.db_directory = db_directory
        self.__tables = {}

        if os.path.exists(db_directory):
            # load existing directory
            self._load_tables()
        else:
            # create new directory if not read_only
            if self.__read_only:
                raise IOError("DB for read does not exist.")
            os.makedirs(db_directory, exist_ok=True)

    def __getitem__(self, name):
        return self.__tables[name]

    def _filepath(self, name):
        filename = f"{name}.csv"
        filepath = os.path.join(self.db_directory, filename)
        return filepath

    @property
    def read_only(self):
        return bool(self.__read_only)

    @staticmethod
    def _load_csv(filepath):
        try:
            # if there is index column in csv file
            table_df = pd.read_csv(filepath, sep=";", index_col="_id")
        except ValueError:
            # if the index column is not present in csv file
            table_df = pd.read_csv(filepath, sep=";")
            table_df.index.name = "_id"
        return table_df

    @staticmethod
    def _load_excel(filepath):
        """ DEPRECATED """
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

    def _load_tables(self):
        for filename in os.listdir(self.db_directory):
            # check extension
            if not any(filename.endswith("."+ext) for ext in EXTENSIONS):
                continue

            # load file
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
        deleted `Tables` and overwrite other `Tables`.
        """
        # check read only
        if self.__read_only:
            raise IOError("DB is for reading only.")
        # remove files for deleted tables
        for deleted_name in self.__dropped_tables:
            filepath = self._filepath(deleted_name)
            if os.path.exists(filepath):
                os.remove(filepath)
        # reset the state of dbdriver
        self.__dropped_tables.clear()
        # overwrite existing tables
        for name, table in self.__tables.items():
            filepath = self._filepath(name)
            table.to_df().to_csv(filepath, sep=";")

    def create_table(self, name):
        """
        Creates new table with given name, or overwrites the existing
        one with empty table.
        """
        # check read only
        if self.__read_only:
            raise IOError("DB is for reading only.")
        # add new table to data
        table = Table()
        self.__tables[name] = table
        # if table previously removed - unmark it
        if name in self.__dropped_tables:
            self.__dropped_tables.remove(name)

    def delete_table(self, name):
        """
        Deletes table from DB by given name. It does not take effect
        on harddrive directory until `dump_tables` is called.
        """
        # check read only
        if self.__read_only:
            raise IOError("DB is for reading only.")
        # delete table
        self.__tables.pop(name)
        # add table name as deleted
        self.__dropped_tables.append(name)

    def get_deleting_access(self):
        """
        Enables the deletion of whole DB from harddrive directory.
        It returns the special code, which needs to be passed to
        the `delete` method.
        """
        # check read only
        if self.__read_only:
            raise IOError("DB is for reading only.")
        # create access code
        characters_list = ("1234567890`~!@#$%^&*()_+=-[]\;',./"
                           "{}|:\"<>?QWERTYUIOPLKJHGFDSAZXCVBNM")
        access_code = random.choices(population=characters_list, k=10)
        access_code = "".join(access_code)
        self.deleting_access_code = access_code
        # return the access code with message
        return f"The delete access code [characters 43-53]: {access_code}"

    def delete(self, access_code):
        """
        Deletion of entire DB from harddrive directory, including the
        directory. The access code must be extracted from
        `get_deleting_access` method for the security reason. Deleting
        the directories on harddrive needs confirmation, because it
        cannot be undone.
        """
        # check read only
        if self.__read_only:
            raise IOError("DB is for reading only.")
        # check if access granted
        if self.deleting_access_code is None:
            raise RuntimeError(
                "Access for deleting not granted. Call `get_deleting_access` first.")
        # check access code and remove first-level files and directory
        if access_code == self.deleting_access_code:
            for name in self.__tables:
                filepath = self._filepath(name)
                if os.path.exists(filepath):
                    os.remove(filepath)
            os.rmdir(self.db_directory)
        else:
            raise PermissionError("Incorrect access code, directory "
                                  "was not deleted. See method docstring.")
