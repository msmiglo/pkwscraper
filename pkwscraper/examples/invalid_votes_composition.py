
from pkwscraper.lib.controller import Controller

"""
This example shows the invalid votes percentage in communes (gminy).
It also shows how much of these votes where invalid because of
putting voting mark next to 2 or more candidates. This is considered to
be main indication of probability of elections falsification.

The ballots are counted by hand by voting commissions. Considering that
most members of commission are loyal and lawful (or even at least one of
them), the easiest known way of falsifying votes is to secretly put
additional mark on ballots with valid vote given to undesired candidates
during counting them. It makes this particular vote invalid, without
further possibility to determine if the ballot was falsified or if the
voter gave an invalid vote. This can be prevented by putting away pens
during counting ballots.

Last years there is a problem with finding enough people for voting
commissions (there must be more than 100 000 of them throughout the
country), so the salary was raised noticibly. Therefore much of these
people are just random people not involved in politics and can be
considered honest. Nevertheless commissions are created by local
authorities, so there is bigger risk of unthrustworthy commission
members in rural areas where one of parties has vast majority of
support.

However, demographic structure and value of turnout also can cause
differences in ammount of invalid votes. It is also important to mention
that giving invalid votes is considered a form of boycott or protest
against the voting system, in some groups of voters. But ballots with
invalid votes made as a protest most often does not contain any voting
mark, which is differentiated in protocoles.

To sum up - probability of elections falsification can be somewhat
detected by applying statistical analysis to voting results. This
example shows relatively easiest analysis of it.

Color code:
- red: MANY invalid votes, MANY of them due to multiple voting marks
- blue: MANY invalid votes, LITTLE of them due to multiple voting marks
- green: LITTLE invalid votes, LITTLE of them due to multiple voting marks
- yellow: LITTLE invalid votes, MANY of them due to multiple voting marks

Red color may indicate units with highest probability of using the
described falsification method. This should be further checked with the
total number of voters and results for individual committees.
"""


def function(db):
    # read protocoles data from polling districts from DB
    protocoles = db["protokoły"].find(
        query={},
        fields=["voters", "ballots_valid", "votes_invalid",
                "invalid_2_candidates", "votes_valid"]
    )

    # initiate sums
    voters = 0
    ballots_valid = 0
    votes_invalid = 0
    invalid_2_candidates = 0
    votes_valid = 0

    # iterate over protocoles and sum votes
    for protocole_record in protocoles:
        voters += protocole_record[0]
        ballots_valid += protocole_record[1]
        votes_invalid += protocole_record[2]
        invalid_2_candidates += protocole_record[3]
        votes_valid += protocole_record[4]

    # calculate measures
    invalid_percent = votes_invalid / ballots_valid
    too_many_candidates_percent = invalid_2_candidates / votes_invalid
    too_many_absolute = invalid_2_candidates / ballots_valid

    # return vector of values
    return invalid_percent, too_many_candidates_percent


def colormap(values):
    # unpack values
    invalid_fraction, too_many_candidates_fraction = values
    # determine color channels
    red = too_many_candidates_fraction
    green = 1 - invalid_fraction
    blue = 1 - max(red, green)
    alpha = 0.82
    # compose color
    return (red, green, blue, alpha)


def main():
    # run
    ctrl = Controller(
        ("Sejm", 2015), function, colormap, granularity="communes",
        outlines_granularity="constituencies", normalization=True,
        output_filename="głosy_nieważne.png"
    )
    ctrl.run()

    # print measures extremes
    min_invalid, min_multiple = ctrl.vis.mins
    max_invalid, max_multiple = ctrl.vis.maxs
    print(f"Invalid votes percentage ranges from"
          f" {round(100*min_invalid, 1)} % to"
          f" {round(100*max_invalid, 1)} %.")
    print(f"Fraction of them, caused by marking more than"
          f" 1 candidate, ranges from {round(100*min_multiple, 1)} %"
          f" to {round(100*max_multiple, 1)} %.")


if __name__ == "__main__":
    main()
