#!/usr/bin/env python3.9
from itertools import chain, repeat
from math import ceil
import random
import argparse
from multiprocessing import Pool
from pathlib import Path
import shutil
import z3


def gen_uniform_digit(n: int, k: int):
    """Generate k n-digit integers"""
    low = pow(10, n - 1)
    high = pow(10, n)
    num = high - low
    count = ceil(k / num)
    return random.sample(range(low, high), k=k, counts=repeat(count, num))


def gen_uniform_num(low, high, k):
    """Generate k numbers between [low, high), each number has equal probability"""
    num = len(range(low, high))
    count = ceil(k / num)
    return random.sample(range(low, high), k=k, counts=repeat(count, num))


def gen_skewed(k):
    # count of every digit
    skew_factors = tuple(map(int, (1e7, 1e4, 1e2, 1e1)))
    return random.sample(
        range(0, 10000), k=k,
        counts=chain(repeat(skew_factors[0], 10),  # skewed towards first 10
                     repeat(skew_factors[1], 90),
                     repeat(skew_factors[2], 900),
                     repeat(skew_factors[3], 9000),
                     ))


def write(ints, name: str, mode="w"):
    with open(name, mode) as f:
        f.writelines(map(lambda n: "%d\n" % n, ints))


def gen_ints(name):
    nums = []
    if name == "skewed":
        nums = gen_skewed(1e6)
    elif name == "uniform_dig":
        for i in range(1, 5):
            nums.extend(gen_uniform_digit(i, int(1e6)))
        random.shuffle(nums)
    elif name == "uniform_num":
        nums = gen_uniform_num(0, int(1e4), int(2.25e6))
    return nums


def fit_bytes(digs, total_bytes):
    """Generate population sizes of digs such that total size of their
    str representation ~= total_bytes.

    n-digit number takes n bytes"""
    assert 0 <= total_bytes

    lines = total_bytes // sum(digs)
    sizes = [lines] * len(digs)
    actual_bytes = sum(size * dig for size, dig in zip(sizes, digs))
    direction = 1 if total_bytes > actual_bytes else -16
    num_iters = 0
    while abs(total_bytes - actual_bytes) > 4 and num_iters < 1000:
        i = random.randrange(0, len(digs))
        sizes[i] += direction
        actual_bytes = sum(size * dig for size, dig in zip(sizes, digs))
        direction = 1 if total_bytes > actual_bytes else -1
        num_iters += 1
    return sizes


def approx_eq(a, b, delta):
    diff = a - b
    return z3.And(-delta<diff, diff < delta)


def gen_expected(n, expected_ratio, k, total_bytes, all_digs=tuple(range(1, 10))):
    """Generate k numbers with fixed % of them having n digits.

    Total size of generated numbers (in bytes) ~= total_bytes"""
    assert 0 <= expected_ratio <= 1
    num_target = int(expected_ratio * k)
    target_bytes = n * num_target
    num_other = k - num_target
    other_digs = tuple(sorted(set(all_digs) - {n}))
    other_bytes = total_bytes - target_bytes
    assert 0 <= other_bytes
    
    # x = z3.Int('x')
    solver = z3.Solver()
    xn = z3.Int(f'x{n}')
    e0 = approx_eq(xn, num_target, int(k * 0.01))
    solver.add(e0)

    sizes = [z3.Int(f'x{i}') for i in other_digs]

    avg = sum(sizes) / len(sizes)
    e_other_sizes_eq = z3.And(*(approx_eq(size, avg, 10000) for size in sizes))
    solver.add(e_other_sizes_eq)

    sizes.append(xn)
    e2 = approx_eq(sum(sizes), k, int(k*0.1))
    solver.add(e2)

    m_total_bytes = sum(x * dig for x, dig in zip(sizes, other_digs)) + target_bytes
    e1 = approx_eq(m_total_bytes, total_bytes, int(0.1 * total_bytes))
    solver.add(e1)

    e5 = z3.And(*[size >= 0 for size in sizes])
    solver.add(e5)

    print(other_bytes, num_other, e1, e2, e0, sep="\n")
    # a = z3.solve(e0, e1, e2, e5)
    a = solver.check()
    # z3.
    print(a == z3.sat and solver.model() or None)
    return

    nums = gen_uniform_digit(n, num_target)
    print(nums)
    other_sizes = fit_bytes(other_digs, other_bytes)
    print(other_sizes, sum(other_sizes), other_bytes)
    for size, dig in zip(other_sizes, other_digs):
        print(dig)
        nums += gen_uniform_digit(dig, size)
    return nums


def gen_expected_model(n: int, ratio: float, total_bytes: int, all_digs=tuple(range(1, 10))):
    solver = z3.Solver()
    total_lines = z3.Int('total_lines')
    target_lines = z3.Int(f'lines{n}')
    target_bytes = target_lines * z3.IntVal(n)
    e_target_lines = approx_eq(target_lines, z3.RealVal(ratio) * total_lines, z3.RealVal(100))
    solver.add(e_target_lines)

    other_digs = tuple(sorted(set(all_digs) - {n}))
    # other_bytes = z3.RealVal(total_bytes) - target_bytes
    other_lines = [z3.Int(f'lines{d}') for d in other_digs]
    total_lines_eqn = sum(other_lines, target_lines)
    e_total_lines = approx_eq(total_lines_eqn, total_lines, 1000)
    solver.add(e_total_lines)

    other_bytes = [d * lines for d, lines in zip(other_digs, other_lines)]
    total_bytes_eqn = sum(other_bytes, target_bytes)
    e_total_bytes = approx_eq(total_bytes_eqn, total_bytes, 100)
    solver.add(e_total_bytes)
    print(e_target_lines)

    # make others equal
    other_lines_avg = sum(other_lines) / len(other_lines)
    e_other_lines_avg = z3.And(*(approx_eq(lines, other_lines_avg, 1000) for lines in other_lines))
    solver.add(e_other_lines_avg)

    # sanity checks:
    e_all_geq0 = z3.And([lines > 0 for lines in other_lines])
    solver.add(e_all_geq0)
    print(solver.check())
    model = (solver.model())
    print(model)
    actual_size = model.eval(total_bytes_eqn)
    print(actual_size)
    pass

def worker(worker_id, name):
    for _ in range(25):
        nums = gen_ints(name)
        write(nums, f"/tmp/ints_{name}{worker_id:02}.csv", "a")
        del nums


def concat(output, inputs):
    with open(output, "wb") as f:
        for part in inputs:
            with open(part, "rb") as f_in:
                shutil.copyfileobj(f_in, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=["skewed", "uniform_dig", "uniform_num"])
    parser.add_argument("--num-procs", type=int, default=8)
    parser.add_argument("--output-dir", type=Path, default=Path("inputs/ints/"))
    args = parser.parse_args()
    name = args.name
    num_procs = args.num_procs
    with Pool(num_procs) as pool:
        pool.starmap(worker, enumerate(repeat(name, num_procs)))
        pool.close()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    concat(output_dir / f"{name}.csv", Path("/tmp").glob(f"ints_{name}*"))


from collections import defaultdict


def read_nums(file: Path):
    lens = defaultdict(int)
    with open(file) as f:
        for line in f:
            lens[len(line)] += 1
    print(lens)


if __name__ == '__main__':
    # read_nums(Path("inputs/ints/skewed_small.csv"))
    n = gen_expected_model(2, 0.3, 2000000, tuple(range(1,6)))
    print(n)