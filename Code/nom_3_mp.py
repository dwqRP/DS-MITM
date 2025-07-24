from multiprocessing import Pool, cpu_count
from collections import Counter
import itertools
import math
import time

# S-box and inverse (from PRINT cipher)
S = [0, 1, 3, 6, 7, 4, 5, 2]
S_inv = [0, 1, 7, 2, 5, 6, 3, 4]

# MixColumn multiplication table over GF(2^3) with x^3 + x + 1 as modulus
mul_table = [
    # 0  1  2  3  4  5  6  7
    [0, 0, 0, 0, 0, 0, 0, 0],  # 0 × *
    [0, 1, 2, 3, 4, 5, 6, 7],  # 1 × *
    [0, 2, 4, 6, 3, 1, 7, 5],  # 2 × *
    [0, 3, 6, 5, 7, 4, 1, 2],  # 3 × *
    [0, 4, 3, 7, 6, 2, 5, 1],  # 4 × *
    [0, 5, 1, 4, 2, 7, 3, 6],  # 5 × *
    [0, 6, 7, 1, 5, 3, 2, 4],  # 6 × *
    [0, 7, 5, 2, 1, 6, 4, 3],  # 7 × *
]

# MDS matrix
MC = [[2, 3], [3, 2]]


def mix_column(state):
    new = [[0, 0], [0, 0]]
    for c in range(2):
        s0, s1 = state[0][c], state[1][c]
        new[0][c] = mul_table[MC[0][0]][s0] ^ mul_table[MC[0][1]][s1]
        new[1][c] = mul_table[MC[1][0]][s0] ^ mul_table[MC[1][1]][s1]
    return new


def init_ddt():
    ddt = [[[] for _ in range(8)] for _ in range(8)]
    for d in range(8):
        for x in range(8):
            y = S[x] ^ S[x ^ d]
            ddt[d][y].append(x)
    return ddt


ddt = init_ddt()


def task(params):
    a, x2_0, x2_1, x4_0, x4_1, w4_0 = params
    if a == 0 or w4_0 == 0:
        return []

    delta_Z1 = [[a, 0], [0, 0]]
    delta_X2 = mix_column(delta_Z1)
    X2 = [[x2_0, 0], [x2_1, 0]]
    delta_Y2 = [
        [S[X2[i][j]] ^ S[X2[i][j] ^ delta_X2[i][j]] for j in range(2)] for i in range(2)
    ]
    delta_Z2 = [delta_Y2[0], [delta_Y2[1][1], delta_Y2[1][0]]]
    delta_X3 = mix_column(delta_Z2)

    delta_W4 = [[w4_0, 0], [0, 0]]
    delta_Z4 = mix_column(delta_W4)
    delta_Y4 = [delta_Z4[0], [delta_Z4[1][1], delta_Z4[1][0]]]
    X4 = [[x4_0, 0], [0, x4_1]]
    delta_X4 = [
        [X4[i][j] ^ S_inv[S[X4[i][j]] ^ delta_Y4[i][j]] for j in range(2)]
        for i in range(2)
    ]
    delta_Z3 = mix_column(delta_X4)
    delta_Y3 = [delta_Z3[0], [delta_Z3[1][1], delta_Z3[1][0]]]

    result = []
    for a0 in ddt[delta_X3[0][0]][delta_Y3[0][0]]:
        for b0 in ddt[delta_X3[0][1]][delta_Y3[0][1]]:
            for c0 in ddt[delta_X3[1][0]][delta_Y3[1][0]]:
                for d0 in ddt[delta_X3[1][1]][delta_Y3[1][1]]:
                    X3 = [[a0, b0], [c0, d0]]
                    res = []
                    for diff in range(1, 8):
                        dZ1 = [[diff, 0], [0, 0]]
                        dX2 = mix_column(dZ1)
                        dY2 = [
                            [S[X2[i][j]] ^ S[X2[i][j] ^ dX2[i][j]] for j in range(2)]
                            for i in range(2)
                        ]
                        dZ2 = [dY2[0], [dY2[1][1], dY2[1][0]]]
                        dX3 = mix_column(dZ2)
                        dY3 = [
                            [S[X3[i][j]] ^ S[X3[i][j] ^ dX3[i][j]] for j in range(2)]
                            for i in range(2)
                        ]
                        dZ3 = [dY3[0], [dY3[1][1], dY3[1][0]]]
                        dX4 = mix_column(dZ3)
                        dY4 = [
                            [S[X4[i][j]] ^ S[X4[i][j] ^ dX4[i][j]] for j in range(2)]
                            for i in range(2)
                        ]
                        dZ4 = [dY4[0], [dY4[1][1], dY4[1][0]]]
                        dW4 = mix_column(dZ4)
                        res.append(dW4[0][0])
                    result.append(tuple(sorted(res)))
    return result


if __name__ == "__main__":
    start = time.time()
    all_params = list(itertools.product(range(8), repeat=6))

    with Pool(processes=cpu_count()) as pool:
        results = pool.map(task, all_params)

    multisets = [r for group in results if group for r in group]
    print("Total multisets:", math.log2(len(multisets)))
    print("Distinct multisets (log2):", math.log2(len(set(multisets))))
    print("Elapsed time: {:.2f} seconds".format(time.time() - start))
