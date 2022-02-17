
import math

from pkwscraper.lib.controller import Controller
from pkwscraper.lib.visualizer import Colormap

"""
This example shows some mathematics-based funny analysis. It takes
the votes sum for each polling districts and checks if this sum is a
prime number or not. The plot shows count of such prime numbers
in each commune.

Color code:
- white: zero prime numbers
- blue: many prime numbers
"""

def is_prime(n):
    if n < 2:
        return False
    max_i = int(n**0.5)
    for i in range(2, max_i+1):
        if n % i == 0:
            return False
    return True


def function(db):
    votes_sums = db["protokoły"].find({}, fields="votes_valid")
    prime_count = sum(map(is_prime, votes_sums))
    primes_log = math.log(prime_count + 1)
    return primes_log ** 0.5


def colormap(value):
    return [1-value, 1-value, 1]


def main():
    ctrl = Controller(
        ("Sejm", 2015), function, colormap, granularity="communes",
        outlines_granularity="voivodships", normalization=True,
        output_filename="prime_votes.png"
    )
    ctrl.run()


if __name__ == "__main__":
    main()
