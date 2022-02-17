
"""
This example shows the sum of votes for individual political parties
members.

The committees are the formal units that are responsible for
aquiring candidates, composing and registering the lists of candidates
and conducting the formal election campaings. Some committees are
directly linked to some political party and take their name. Other
are created by private people or non-government organisations.

In each case - there are no constraints on political party membership
of individual candidates. A candidate of one party's committee can be
a member of different party or any political party. Also some political
party members can be put on lists of non-political organizations.

Therefore the result of a committee can be sometimes even very far from
the result of political party it represents. The common misunderstanding
is that the mandate winning politicians represents only parties that
are connected to committees they belong to. For example, in 2015 only
5 committees succeeded to win mandates, but the elected parliament
members belong to 11 different political parties. The number of
political parties having members in parliament in 2019 was even higher.

Therefore plotting the results of parties and not committees can show
very interesting and useful information.
"""

from pkwscraper.lib.dbdriver import DbDriver


SEJM_2015_DATA_DIRECTORY = "./pkwscraper/data/sejm/2015/preprocessed/"


def main():
    # open DB
    db = DbDriver(SEJM_2015_DATA_DIRECTORY, read_only=True)

    # get party membership/support for each candidate
    candidates = db["kandydaci"].find(
        {"is_crossed_out": False}, fields=["_id", "party"])

    for candidate in candidates:
        party = candidate[1]
        if party.startswith("nie należy do partii politycznej"):
            candidate[1] = None

    candidate_to_party = {cand_id: party for cand_id, party in candidates}

    # prepare data dicts
    party_list = list(set(party for _, party in candidates))
    party_results = {party: {"mandates": 0, "votes": 0}
                     for party in party_list}

    # mandate winners
    mandate_winners_ids = db["mandaty"].find({}, fields="candidate")

    for candidate_id in mandate_winners_ids:
        party = candidate_to_party[candidate_id]
        party_results[party]["mandates"] += 1

    # determine results table names
    constituency_nos = db["okręgi"].find({}, fields="number")
    table_names = [f"wyniki_{const_no}" for const_no in constituency_nos]

    # iterate over constituencies
    for table_name in table_names:
        voting_results = db[table_name].find({})
        for result_i in voting_results.values():
            for cand_id in result_i:
                if cand_id in ["_id", "obwod", "candidates_count"]:
                    continue
                party = candidate_to_party[cand_id]
                votes = int(result_i[cand_id])
                party_results[party]["votes"] += votes

    # sort results
    sorted_parties = sorted(
        party_results,
        key=lambda party: party_results[party]["votes"], reverse=True
    )

    # present results
    longest_name_length = max(len(p) for p in party_list if p)
    longest_votes_length = len(str(max(p["votes"]
                                       for p in party_results.values())))
    longest_mandates_length = len(str(max(p["mandates"]
                                          for p in party_results.values())))
    first_spaces = longest_name_length + longest_votes_length + 4
    second_spaces = longest_mandates_length + 3
    print("Kandydatki i kandydaci następujących partii uzyskały:")
    print()
    for party in sorted_parties:
        party_data = party_results[party]
        mandates = party_data["mandates"]
        votes = party_data["votes"]
        if party is None:
            party = "bezpartyjne/i"
        else:
            party = f'"{party}"'
        n_spaces_1 = first_spaces - len(party) - len(str(votes))
        n_spaces_2 = second_spaces - len(str(mandates))
        spacing_1 = " " * n_spaces_1
        spacing_2 = " " * n_spaces_2
        print(f'{party}:{spacing_1}{votes} głosów'
              f'{spacing_2}{mandates} mandatów')


if __name__ == "__main__":
    main()
