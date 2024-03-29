
import json

from pkwscraper.lib.dbdriver import DbDriver
from pkwscraper.lib.preprocessing.base_preprocessing import BasePreprocessing
from pkwscraper.lib.region import Region
from pkwscraper.lib.utilities import get_parent_code


ELECTION_TYPE = "sejm"
YEAR = 2015
RAW_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/raw/"
RESCRIBED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/rescribed/"
PREPROCESSED_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


class Sejm2015Preprocessing(BasePreprocessing):
    def __init__(self, source_db=None, target_db=None):
        # source db
        if source_db is None:
            source_db = DbDriver(RESCRIBED_DATA_DIRECTORY, read_only=True)
        if not isinstance(source_db, DbDriver):
            raise TypeError("Please pass an instance of `DbDriver` or `None`.")
        if not source_db.read_only:
            raise RuntimeError(
                "Please pass `DbDriver` for read only or `None`.")
        self.source_db = source_db

        # target db
        if target_db is None:
            target_db = DbDriver(PREPROCESSED_DATA_DIRECTORY)
        if not isinstance(target_db, DbDriver):
            raise TypeError("Please pass an instance of `DbDriver` or `None`.")
        if target_db.read_only:
            raise RuntimeError(
                "Please pass `DbDriver` for writing or `None`.")
        self.target_db = target_db

    def run_all(self):
        self._preprocess_voivodships()
        self._preprocess_okregi()
        self._preprocess_powiaty()
        self._preprocess_gminy()
        self._preprocess_obwody()
        self._preprocess_protocoles()
        self._preprocess_lists()
        self._preprocess_candidates()
        self._preprocess_votes()
        self._check_votes()
        self._preprocess_mandates()
        print()

        print("dumping DB tables...")
        self.target_db.dump_tables()
        print("DB closed.")
        print()

    @staticmethod
    def clean_text(text):
        """
        Used to clean non-universal texts values like names of candidates,
        committees and commissions addresses. Remove surplus spaces, replace
        non-standard quotarion marks, etc.
        """
        # TODO - MAYBE MOVE TO UTILITIES
        if text is None:
            return None
        text = " ".join(text.split())
        text = text.replace('„', '"').replace('”', '"')
        text = text.replace(' , ', ', ')
        text = text.replace('( ', '(')
        return text

    @staticmethod
    def parse_full_name(full_name):
        """
        Split full name of candidate into names and surname, asserting
        names are styled `title case` and surname is styled `all upper
        case`. Parts are separated by spaces.
        """
        # TODO - ADD SPLITTING FIRST NAME MAYBE
        # TODO - MAYBE MOVE TO UTILITIES
        names, surname = full_name.rsplit(maxsplit=1)
        i = 0
        while names.title() != names and i < 10:
            names, rest = names.rsplit(maxsplit=1)
            surname = rest + " " + surname
            i += 1
        return names, surname

    @staticmethod
    def parse_commission_address(full_address, commission_name,
                                 obwod_identifier):
        """
        Split full address of commission. It should be in format:
        full_address = `{commission_name}, {commission_address}`
        """
        clean_text = Sejm2015Preprocessing.clean_text

        full_address = clean_text(full_address)
        commission_name = clean_text(commission_name)

        # address is missing or included in commission name
        if full_address == commission_name:
            if "," in full_address:
                # name contains address
                name, address = full_address.split(",", maxsplit=1)
                name = clean_text(name)
                address = clean_text(address)
                return name, address
            else:
                # address is missing
                return commission_name, ""

        if full_address.startswith(commission_name):
            # regular case
            name = commission_name
            address = full_address[len(name):]

            if address.startswith(", "):
                # correct format
                address = address[2:]
                address = clean_text(address)
                return name, address

            if address.count(",") == 1:
                # missing one comma
                address = clean_text(address)
                return name, address

        # there is a problem with commission name
        if full_address.count(",") == 2:
            # can be determined by commas
            name, address = full_address.split(",", maxsplit=1)
            name = clean_text(name)
            address = clean_text(address)
        elif "ul. " in full_address:
            # some comma is missing, try finding the street prefix
            name, address = full_address.split("ul. ", maxsplit=1)
            name = clean_text(name)
            address = clean_text("ul. " + address)
        else:
            raise ValueError(
                f"Cannot parse adress from:\n`{full_address}`\n"
                f"`{commission_name}`\n`{address}`\n"
                f"Unit identifier:\n{obwod_identifier}\n")

        if "(" in address:
            # there is a room/hall name in the address
            address, modifier = address.split("(")
            address = clean_text(address)
            modifier = clean_text(modifier)
            name += " (" + modifier

        # print information about malformed commission name
        if not name.startswith(commission_name):
            commune_code, polling_district_number = obwod_identifier
            print(f"Probable typo in commision name:\n"
                  f"{name}\n"
                  f"{commission_name}\n"
                  f"commune code {commune_code}, polling district no. "
                  f"{polling_district_number}\n")

        return name, address

    @staticmethod
    def urban_or_rural(commune_full_name, commune_code):
        district_code = get_parent_code(commune_code)
        if district_code == 146500:
            return "urban"
        if commune_full_name.startswith("gm. "):
            return "rural"
        if commune_full_name.startswith("m. "):
            return "urban"
        if commune_full_name.startswith("Statki "):
            return "marine"
        if commune_full_name.startswith("Zagranica"):
            return "abroad"
        raise ValueError(f"Cannot determine `urban_or_rural` "
                         f"value from name: {commune_full_name}.")

    @staticmethod
    def merge_commune_names(partial_name, full_name, code):
        # remove urban or rural prefix
        if full_name.startswith("gm. "):
            prefix = "gm. "
            commune_name = full_name[len(prefix):]
        elif full_name.startswith("m. "):
            prefix = "m. "
            commune_name = full_name[len(prefix):]
        else:
            prefix = ""
            commune_name = full_name

        # return original full name if everything is ok
        if commune_name == partial_name:
            return full_name

        # check if full name is abbreviated
        if commune_name.endswith("."):
            commune_name = commune_name.rstrip(".")
            if partial_name.startswith(commune_name):
                # return full form if name is abbreviated
                return prefix + partial_name

        # check if old name have some suffix (the case of Słupia
        # commune, code: 260207)
        if commune_name.startswith(partial_name):
            return prefix + partial_name

        raise ValueError(
            f"Problem with names: {full_name} / {partial_name}, code={code}.")

    @staticmethod
    def _parse_geo(geo_txt):
        region = Region.from_svg_d(geo_txt)
        jsoned_txt = region.to_json()
        return jsoned_txt

    def _preprocess_voivodships(self):
        voivodships = self.source_db["województwa"].find({})
        self.target_db.create_table("województwa")

        for v in voivodships.values():
            code = v["code"] * 10000
            name = v["name"]
            geo = v["geo"]

            self.target_db["województwa"].put({
                "code": code,
                "name": name,
                "geo": self._parse_geo(geo),
            })

    def _preprocess_okregi(self):
        constituencies = self.source_db["okręgi"].find({})
        self.target_db.create_table("okręgi")

        for o in constituencies.values():
            number = o["number"]
            headquarters = o["headquarters"]
            voivodship_name = o["voivodship"]
            mandates = o["mandates"]
            geo = o["geo"]

            voivod_id, voivod = self.target_db["województwa"].find_one(
                {"name": voivodship_name})

            self.target_db["okręgi"].put({
                "number": number,
                "headquarters": headquarters,
                "voivodship": voivod_id,
                "mandates": mandates,
                "geo": self._parse_geo(geo),
            })

    def _preprocess_powiaty(self):
        districts = self.source_db["powiaty"].find({})
        self.target_db.create_table("powiaty")

        consituencies_numbers = self.target_db["okręgi"].find(
            query={}, fields="number")
        districts_dict = {num: list() for num in consituencies_numbers}

        for d in districts.values():
            constituency_number = d["constituency_number"]
            code = d["code"] * 100
            name = d["name"]
            geo = d.get("geo", "")

            #if code == 146500:
            #    code = 146501
            voivod_code = get_parent_code(code)
            voivod_id, voivod = self.target_db["województwa"].find_one(
                {"code": voivod_code})

            district_id = self.target_db["powiaty"].put({
                "code": code,
                "name": name,
                "geo": self._parse_geo(geo),
                "parent": voivod_id,
            })

            districts_dict[constituency_number].append(district_id)

        # assign districts to consituencies
        for constituency_number, districts_list in districts_dict.items():
            # serialize list of districts
            jsoned_districts_list = json.dumps(districts_list)

            # add field in constituency record
            con_id, con_record = self.target_db["okręgi"].find_one(
                {"number": constituency_number})
            con_record["powiat_list"] = jsoned_districts_list

            # update the record
            self.target_db["okręgi"].put(con_record, _id=con_id)

    def _preprocess_gminy(self):
        communes = self.source_db["gminy"].find({})
        self.target_db.create_table("gminy")

        code_to_name_dict = {
            code: name for code, name in self.source_db["obwody"].find(
                {}, fields=["commune_code", "commune_name"])
        }

        for c in communes.values():
            code = c["code"]
            partial_name = c["partial_name"]
            geo = c.get("geo", "")

            district_code = get_parent_code(code)
            district_id, district = self.target_db["powiaty"].find_one(
                {"code": district_code})

            full_name = code_to_name_dict[code]
            if full_name is None:
                raise ValueError(
                    f"Cannot find commune '{partial_name}' with code {code}.")
            urban_or_rural = self.urban_or_rural(full_name, code)

            merged_name = self.merge_commune_names(
                partial_name, full_name, code)

            self.target_db["gminy"].put({
                "code": code,
                "name": merged_name,
                "urban_or_rural": urban_or_rural,
                "geo": self._parse_geo(geo),
                "parent": district_id,
            })

    def _preprocess_obwody(self):
        self.target_db.create_table("obwody")

        obwody = self.source_db["obwody"].find({})
        obwody_completion = self.source_db["obwody_uzupełnienie"].find({})

        code_to_obwod_dict = {
            (record["commune_code"], record["polling_district_number"]): _id
            for _id, record in obwody_completion.items()
        }

        gmina_code_to_id_dict = {
            code: _id
            for _id, code in self.target_db["gminy"].find(
                query={}, fields=["_id", "code"])
        }

        constituencies_number_to_id_dict = {
            number: _id
            for _id, number in self.target_db["okręgi"].find(
                query={}, fields=["_id", "number"])
        }

        for ob in obwody.values():
            # get basic data
            constituency_number = ob["constituency_number"]
            senate_constituency_number = ob["senate_constituency_number"]
            commune_code = ob["commune_code"]
            commune_name = ob["commune_name"]
            polling_district_number = ob["polling_district_number"]
            full_address = ob["full_address"]
            voters = ob["voters"]

            # get completion data
            obwod_identifier = (commune_code, polling_district_number)
            ob_compl_id = code_to_obwod_dict[obwod_identifier]
            ob_compl = obwody_completion[ob_compl_id]

            completion_commune_name = ob_compl["commune_name"]
            commission_name = ob_compl.get("commission_name", "")

            # check name of commune
            if completion_commune_name != commune_name:
                raise ValueError(
                    f"Problem with commune name: {commune_name}"
                    f" / {completion_commune_name}, code: {commune_code}")

            # check name and address of commission
            try:
                name, address = self.parse_commission_address(
                    full_address, commission_name, obwod_identifier)
            except ValueError as e:
                print(e)
                print(f"---Problem with commission name and address:\n"
                      f"{full_address}\n"
                      f"{commission_name}\n"
                      f"{commune_code}\n"
                      f"{polling_district_number}\n")
                name, address = commission_name, full_address

            # preprocess additional data
            constituency_id = constituencies_number_to_id_dict[
                constituency_number]
            commune_id = gmina_code_to_id_dict[commune_code]
            urban_or_rural = self.urban_or_rural(commune_name, commune_code)

            # add record
            self.target_db["obwody"].put({
                "constituency": constituency_id,
                "gmina": commune_id,
                "number": polling_district_number,
                "commission_name": name,
                "address": address,
                "senate_constituency_number": senate_constituency_number,
                "urban_or_rural": urban_or_rural,
                "voters": voters,
            })

    def _preprocess_protocoles(self):
        self.target_db.create_table("protokoły")
        obwody_data = self.source_db["obwody"].find({})

        # create index for communes and polling districts IDs
        commune_dict = {commune_code: commune_id for commune_code, commune_id
            in self.target_db["gminy"].find(query={}, fields=["code", "_id"])}
        obwod_dict = {
            (commune_id, obwod_number): obwod_id
            for commune_id, obwod_number, obwod_id
            in self.target_db["obwody"].find(
                query={},
                fields=["gmina", "number", "_id"]
            )
        }

        # iterate records
        for o in obwody_data.values():
            # get identifier of polling district
            commune_code = o["commune_code"]
            polling_district_number = o["polling_district_number"]
            commune_id = commune_dict[commune_code]
            obwod_id = obwod_dict[(commune_id, polling_district_number)]

            # get data
            voters = o["voters"]
            got_ballots = o["got_ballots"]
            unused_ballots = o["unused_ballots"]
            given_ballots = o["given_ballots"]
            proxy_voters = o["proxy_voters"]
            certificate_voters = o["certificate_voters"]
            voting_packets = o["voting_packets"]
            return_envelopes = o["return_envelopes"]
            envelopes_without_statement = o["envelopes_without_statement"]
            unsigned_statement = o["unsigned_statement"]
            without_voting_envelope = o["without_voting_envelope"]
            unseeled_voting_envelopes = o["unseeled_voting_envelopes"]
            envelopes_accepted = o["envelopes_accepted"]
            ballots_from_box = o["ballots_from_box"]
            envelopes_from_ballot_box = o["envelopes_from_ballot_box"]
            ballots_invalid = o["ballots_invalid"]
            ballots_valid = o["ballots_valid"]
            votes_invalid = o["votes_invalid"]
            invalid_2_candidates = o["invalid_2_candidates"]
            invalid_no_vote = o["invalid_no_vote"]
            invalid_candidate = o["invalid_candidate"]
            votes_valid = o["votes_valid"]

            # check correctness
            assert ballots_from_box == ballots_invalid + ballots_valid, \
                ("miscounted ballots taken", commune_code, polling_district_number)
            assert votes_valid + votes_invalid + ballots_invalid == ballots_from_box, \
                ("miscounted votes", commune_code, polling_district_number)
            assert votes_invalid >= invalid_2_candidates + invalid_no_vote + invalid_candidate, \
                ("miscounted invalid votes", commune_code, polling_district_number)
            if got_ballots != unused_ballots + given_ballots:
                print(f"miscounted ballots: obwód {commune_code}/{polling_district_number}", end=", ")
            if return_envelopes != envelopes_without_statement + unsigned_statement \
                + without_voting_envelope + unseeled_voting_envelopes + envelopes_accepted:
                print(f"miscounted envelopes: obwód {commune_code}/{polling_district_number}", end=", ")

            # add new record
            self.target_db["protokoły"].put({
                "obwod": obwod_id,
                "voters": voters,
                "got_ballots": got_ballots,
                "unused_ballots": unused_ballots,
                "given_ballots": given_ballots,
                "proxy_voters": proxy_voters,
                "certificate_voters": certificate_voters,
                "voting_packets": voting_packets,
                "return_envelopes": return_envelopes,
                "envelopes_without_statement": envelopes_without_statement,
                "unsigned_statement": unsigned_statement,
                "without_voting_envelope": without_voting_envelope,
                "unseeled_voting_envelopes": unseeled_voting_envelopes,
                "envelopes_accepted": envelopes_accepted,
                "ballots_from_box": ballots_from_box,
                "envelopes_from_ballot_box": envelopes_from_ballot_box,
                "ballots_invalid": ballots_invalid,
                "ballots_valid": ballots_valid,
                "votes_invalid": votes_invalid,
                "invalid_2_candidates": invalid_2_candidates,
                "invalid_no_vote": invalid_no_vote,
                "invalid_candidate": invalid_candidate,
                "votes_valid": votes_valid,
            })
        print()
        print()

    def _preprocess_lists(self):
        self.target_db.create_table("listy")

        lists_data = self.source_db["kandydaci_xls"].find(
            query={}, fields=["list_number", "committee_name"])
        lists_dict = {
            self.clean_text(committee_name): list_number
            for list_number, committee_name in lists_data
        }

        committees = self.source_db["komitety"].find({})

        for c in committees.values():
            committee_number = c["number"]
            committee_symbol = c["signature"]
            committee_type = c["type"]
            committee_name = c["name"]
            committee_shortname = c.get("shortname", "")
            sejm_candidates = c["sejm_candidates"]
            senat_candidates = c["senat_candidates"]
            committee_status = c["status"]

            committee_name = self.clean_text(committee_name)
            committee_shortname = self.clean_text(committee_shortname)

            if committee_name not in lists_dict:
                continue

            list_number = lists_dict[committee_name]

            self.target_db["listy"].put({
                "committee_number": committee_number,
                "committee_type": committee_type,
                "committee_name": committee_name,
                "committee_shortname": committee_shortname,
                "committee_symbol": committee_symbol,
                "committee_status": committee_status,
                "list_number": list_number,
            })

    def _preprocess_candidates(self):
        # committees shortnames dict
        committees_names = self.target_db["listy"].find(
            {}, fields=["committee_name", "committee_shortname"])
        committees_names_dict = {
            shortname: name
            for name, shortname in committees_names
        }

        # make list of valid candidates from website
        valid_candidates = dict()
        candidates_html_data = self.source_db["kandydaci_html"].find({})

        for c in candidates_html_data.values():
            constituency_number = int(c["okreg_number"])
            committee_shortname = self.clean_text(c["committee_shortname"])
            committee_name = committees_names_dict[committee_shortname]
            full_name = self.clean_text(c["full_name"])

            if c["crossed_out"]:
                continue

            candidate_identifier = (
                constituency_number,
                committee_name,
                full_name
            )
            valid_candidates[candidate_identifier] = True

        # find all candidates
        candidates = self.source_db["kandydaci_xls"].find({})
        self.target_db.create_table("kandydaci")

        for c in candidates.values():
            # get values
            constituency_number = c["okreg_number"]
            candidate_list_number = c["list_number"]
            committee_name = c["committee_name"]
            position = c["position"]
            surname = c["surname"]
            names = c["names"]
            gender = c["gender"]
            residence = c["residence"]
            occupation = c["occupation"]
            party = c["party"]

            # clean data
            surname = self.clean_text(surname)
            names = self.clean_text(names)
            first_name = names.split(maxsplit=1)[0]
            first_name = self.clean_text(first_name)
            committee_name = self.clean_text(committee_name)
            residence = self.clean_text(residence)
            occupation = self.clean_text(occupation)
            party = self.clean_text(party)

            # get constituency id
            constituency_id = self.target_db["okręgi"].find_one(
                query={"number": constituency_number}, fields="_id")

            # get list id
            list_id, list_number = self.target_db["listy"].find_one(
                query={"committee_name": committee_name,
                       "committee_status": "Zarejestrowany"},
                fields=["_id", "list_number"]
            )

            # check data correctness
            if not list_number == candidate_list_number:
                print(f"constituency: `{constituency_number}`")
                raise ValueError(
                    f"non-matching list number for committee"
                    f" `{committee_name}`:\n"
                    f"\t{list_number} / {other_list_number}\n"
                    f"constituency: {constituency_number}\n"
                )
            if gender not in "KM":
                raise ValueError(f"Wrong gender symbol: `{gender}`")

            # get candidate status
            full_name = " ".join([names, surname])
            candidate_identifier = (
                int(constituency_number), committee_name, full_name)

            if candidate_identifier not in valid_candidates:
                is_crossed_out = True
                print(f"Crossed out candidate: {candidate_identifier}")
            else:
                is_crossed_out = False

            # add record
            self.target_db["kandydaci"].put({
                "constituency": constituency_id,
                "list": list_id,
                "position": position,
                "surname": surname,
                "names": names,
                "first_name": first_name,
                "gender": gender,
                "residence": residence,
                "occupation": occupation,
                "party": party,
                "is_crossed_out": is_crossed_out
            })

        print()

    def _preprocess_votes(self):
        # make indexes for finding IDs
        table_name_template = "wyniki_{}"

        #     commune_code ==> commune_ID
        communes_dict = {
            commune_code: commune_id
            for commune_id, commune_code
            in self.target_db["gminy"].find(
                {}, fields=["_id", "code"])
        }

        #     commune_ID + polling_district_number ==> polling dist. ID
        polling_districts_dict = {
            (commune_id, poll_dist_number): poll_dist_id
            for poll_dist_id, commune_id, poll_dist_number
            in self.target_db["obwody"].find(
                {}, fields=["_id", "gmina", "number"])
        }

        #     constituency_no ==> constituency_ID
        constituency_dict = {
            constituency_no: constituency_id
            for constituency_id, constituency_no
            in self.target_db["okręgi"].find(
                {}, fields=["_id", "number"])
        }

        #     committee_shortname ==> list_ID
        list_dict = {
            committee_shortname: list_id
            for list_id, committee_shortname
            in self.target_db["listy"].find(
                {}, fields=["_id", "committee_shortname"])
        }

        #     committee_longname ==> list_ID
        list_longname_dict = {
            committee_longname: list_id
            for list_id, committee_longname
            in self.target_db["listy"].find(
                {}, fields=["_id", "committee_name"])
        }

        #     constituency_ID + candidate_names
        #     + candidate_surname + list_ID ==> candidate_ID
        candidate_dict = {
            (constituency_id, names, surname, list_id): candidate_id
            for candidate_id, constituency_id, list_id, surname, names
            in self.target_db["kandydaci"].find(
                {}, fields=["_id", "constituency", "list", "surname", "names"])
        }

        # iterate over constituencies
        errors = []

        constituencies = self.target_db["okręgi"].find({}, fields="number")
        for constituency_number in constituencies:
            # read data
            table_name = table_name_template.format(constituency_number)
            results_data = self.source_db[table_name].find({})

            # create new table
            self.target_db.create_table(table_name)

            # iterate over polling districts
            for district_data in results_data.values():
                commune_code = district_data["commune_code"]
                candidates_count = district_data["candidates_count"]
                polling_district_number = district_data[
                    "polling_district_number"]

                # get polling district id
                commune_id = communes_dict[commune_code]
                polling_district_id = polling_districts_dict[
                    (commune_id, polling_district_number)]

                # make new record
                record = {
                    "obwod": polling_district_id,
                    "candidates_count": candidates_count,
                }

                # iterate over candidates
                for candidate, votes in district_data.items():
                    if candidate in ["commune_code", "polling_district_number",
                                     "candidates_count"]:
                        continue

                    committee_shortname, candidate_full_name = \
                                         candidate.split("/")
                    committee_shortname = self.clean_text(committee_shortname)
                    candidate_full_name = self.clean_text(candidate_full_name)
                    names, surname = self.parse_full_name(candidate_full_name)

                    # get candidate id
                    constituency_id = constituency_dict[constituency_number]

                    try:
                        list_id = list_dict[committee_shortname]
                    except KeyError:
                        # this is to handle typo in raw data
                        list_id = list_longname_dict[committee_shortname]
                        message = (
                            f'A1 Typo in committee shortname: `{committee_shortname}`.'
                        )
                        errors.append(message)

                    try:
                        candidate_id = candidate_dict[
                            (constituency_id, names, surname, list_id)]
                    except KeyError:
                        # this is because few missing candidates in raw xls
                        candidate_id = None
                        message = (
                            f'A2 Candidate: `{candidate_full_name}` not present in raw data xls file.'
                        )
                        errors.append(message)

                    # check correctness
                    if candidate_id is None:
                        is_crossed_out = True
                    else:
                        is_crossed_out = self.target_db\
                            ["kandydaci"][candidate_id]["is_crossed_out"]

                    if is_crossed_out:
                        # assert there are no votes
                        assert votes == "XXXXX", votes
                    else:
                        # add entry to record
                        votes = int(votes)
                        record[candidate_id] = votes

                # add record to table
                self.target_db[table_name].put(record)

            print(f"Preprocessed voting results for constituency {constituency_number}.")

        # print errors
        print()
        errors = list(sorted(set(errors)))
        for e in errors:
            print(e)

    def _check_votes(self):
        print()
        print("Checking voting sums...")

        # sum votes in source DB and target DB
        source_votes_sum = 0
        target_votes_sum = 0

        constituencies = self.target_db["okręgi"].find({}, fields="number")
        for constituency_no in constituencies:
            table_name = f"wyniki_{constituency_no}"
            source_results = self.source_db[table_name].find({})
            target_results = self.target_db[table_name].find({})

            for source_record in source_results.values():
                for key, value in source_record.items():
                    if key in ["commune_code", "polling_district_number",
                               "candidates_count"]:
                        continue
                    try:
                        votes = int(value)
                        source_votes_sum += votes
                    except ValueError:
                        pass

            for target_record in target_results.values():
                for key, value in target_record.items():
                    if key in ["commune_code", "polling_district_number",
                               "candidates_count"]:
                        continue
                    try:
                        votes = int(value)
                        target_votes_sum += votes
                    except ValueError:
                        pass

        if not source_votes_sum == target_votes_sum:
            raise RuntimeError(
                f"Incompatible votes sum in source and target DBs:"
                f" {source_votes_sum} vs {target_votes_sum}.")

        print()
        print("Checking voting results...")
        votes_count = 0
        table_name_template = "wyniki_{}"

        # iterate over constituencies
        constituencies = self.target_db["okręgi"].find(
            {}, fields=["_id", "number"])

        for constituency_id, constituency_no in constituencies:
            # get table with results
            table_name = table_name_template.format(constituency_no)
            results_polling_districts_id = self.target_db[table_name].find(
                {}, fields="obwod")

            # list all polling district in the constituency
            polling_districts_ids = self.target_db["obwody"].find(
                {"constituency": constituency_id}, fields="_id")

            # check if all polling districts has been covered
            if not set() == set():
                RuntimeError("Not all polling districts has been"
                             " covered in voting results.")

            # list valid candidates IDs
            valid_candidates_ids = self.target_db["kandydaci"].find(
                {"constituency": constituency_id, "is_crossed_out": False},
                fields="_id"
            )

            # iterate results
            for result_data in self.target_db[table_name].find({}).values():
                if len(result_data) != len(valid_candidates_ids) + 2:
                    raise RuntimeError("Wrong candidates count in voting results.")
                for candidate_id in valid_candidates_ids:
                    votes = result_data[candidate_id]
                    votes_count += votes

        # print all votes count
        print()
        print(f"Found {votes_count} votes in whole elections.")

    def _preprocess_mandates(self):
        self.target_db.create_table("mandaty")

        mandates = self.source_db["mandaty"].find({})

        # iterate records
        for m in mandates.values():
            # get data
            constituency_number = m["constituency_number"]
            list_number = m["list_number"]
            position = m["position"]
            committee_name = m["committee_name"]
            candidate_name = m["full_name"]

            # clean texts
            committee_name = self.clean_text(committee_name)
            candidate_name = self.clean_text(candidate_name)
            first_name, surname = candidate_name.split(maxsplit=1)

            # get relations
            constituency_id = self.target_db["okręgi"].find_one(
                query={"number": constituency_number}, fields="_id")
            list_id = self.target_db["listy"].find_one(
                query={
                    "list_number": list_number,
                    "committee_name": committee_name
                },
                fields="_id"
            )

            # find candidate
            candidate_id, candidate_record = self.target_db["kandydaci"] \
                .find_one({
                    "constituency": constituency_id,
                    "list": list_id,
                    "position": position,
                })

            # check correctness
            assert candidate_record["names"].startswith(first_name)
            assert candidate_record["surname"] == surname

            # add record
            self.target_db["mandaty"].put({"candidate": candidate_id})

        # check number of mandates
        assert len(self.target_db["mandaty"].find({})) == 460
