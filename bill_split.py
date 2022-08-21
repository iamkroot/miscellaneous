"""
This is a simple tool to split the bill expenses among various people.
It's main inputs are
1. A TSV file of Bill with columns- quantity,name,price. Usually OCR'd from some service
2. A description of the people who consumed each item in the bill. Sample-

    # drinks
    lemonade: Killua, Gon
    Rose punch: Leorio x2 (leorio had two servings)
    Tea: Kurapika

    # starters: everyone
    nachos
    fries
    (the above two items will be split across all the people named here)

    # main course
    pizza: -Gon, Ging x3 (Gon didn't eat it, Ging had thrice as much as others)
    pasta: everyone
    fried rice: -Kurapika (everyone except Kurapika ate this)

The names of items in the description should closely match the names in the bill.

Final output will be each person's share to the total amount in the bill.
"""

import csv
import re
from collections import Counter, defaultdict
from csv import DictReader
from dataclasses import dataclass
from difflib import get_close_matches
from fractions import Fraction
from pathlib import Path
from pprint import pprint

bill_path = Path("./bill.txt")
expenses_data = Path("./expenses.txt").read_text()
# TAX_MULT = Fraction(1)
TAX_MULT = Fraction("1.011124")
"""Taxation rate on top of bill item prices"""


@dataclass
class BillItem:
    name: str
    price: Fraction
    quantity: int = 1


def parse_bill(path: Path, tax_mult: Fraction):
    bill_data = path.read_text()
    bill_data2 = DictReader(
        bill_data.splitlines(),
        fieldnames=["quantity", "name", "price"],
        dialect=csv.excel_tab)

    return [BillItem(
                r['name'],
                Fraction(r['price'].replace(',', '')) * tax_mult,
                int(r['quantity']))
            for r in bill_data2]


EVERYONE = "everyone"
MULT_PAT = re.compile(r'(?P<name>.*?)\s+x(?P<mult>\d+)$')


@dataclass
class Name:
    name: str
    negate: bool = False
    multiplier: int = 1

    @staticmethod
    def from_names(names: list[str]):
        return [Name(name) for name in names]


everyone_name = Name(EVERYONE)


def parse_names(names_str: str) -> list[Name]:
    names: list[Name] = []
    for name in names_str.split(","):
        name = name.strip()
        if name == EVERYONE:
            names.append(everyone_name)
            continue
        neg = False
        if name.startswith("-"):
            neg = True
            name = name.lstrip("-").lstrip()
        if match := MULT_PAT.match(name):
            names.append(Name(match['name'].title(), neg, int(match['mult'])))
        else:
            names.append(Name(name.title(), neg))
    return names


def parse_expenses(data: str):
    cat_names = None
    people = set()
    items: dict[str, list[Name]] = {}
    for line in data.splitlines():
        if not line:
            continue
        if line.startswith("#"):
            # new category
            split = line.split(":")
            if len(split) > 1:
                # names of people
                names_str = split[1].strip()
                cat_names = parse_names(names_str)
                people.update(name.name for name in cat_names if name != everyone_name)
            else:
                # reset the cat_names
                cat_names = None
            continue
        # now at a food line
        split = line.split(":")
        item_name = split[0].strip()
        if len(split) == 1:
            assert cat_names
            cur_people = cat_names
        else:
            cur_people = parse_names(split[1])
            people.update(name.name for name in cur_people if name != everyone_name)
        items[item_name] = cur_people
    return finalize_names(items, people)


def finalize_names(items: dict[str, list[Name]], people: set[str]):
    # do a second pass to handle negations and "everyone"
    # our final return value will only have the names and their multipliers
    final_items: dict[str, Counter] = {}
    for item, names in items.copy().items():
        final_names = Counter()
        removed_names = Counter()
        added_everyone = False
        for name in names:
            if name.negate:
                removed_names[name.name] += name.multiplier
                if not added_everyone:
                    final_names.update({name: 1 for name in people})
                    added_everyone = True
            elif name == everyone_name:
                if not added_everyone:
                    final_names.update({name: 1 for name in people})
                    added_everyone = True
            else:
                final_names[name.name] = name.multiplier
        final_names -= removed_names
        final_items[item] = final_names
    return final_items


def is_sampler(name):
    return name.lower().startswith("sampler")


def assign_shares(items: dict[str, Counter[str]], bill: list[BillItem]):
    samplers = [name for name, val in items.items() if is_sampler(name)]
    shares = defaultdict(Fraction)
    details = defaultdict(dict)

    for bill_item in bill:
        candidates = items.keys()
        if is_sampler(bill_item.name):
            candidates = samplers
        matches = get_close_matches(bill_item.name, candidates, n=1, cutoff=0.3)
        assert matches, f"no match for {bill_item} in {', '.join(candidates)}"
        people = items[matches[0]]
        per_person = bill_item.price / Fraction(people.total())
        for person, mult in people.items():
            share = per_person * Fraction(mult)
            shares[person] += share
            details[person][bill_item.name] = share
    print("total", float(sum(shares.values())))
    pprint({name: round(float(share), 2) for name, share in shares.items()})
    pprint(dict(details))


bill = parse_bill(bill_path, TAX_MULT)
items = parse_expenses(expenses_data)
assign_shares(items, bill)
