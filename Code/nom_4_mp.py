from multiprocessing import Pool, cpu_count
from collections import Counter
import itertools
import math
import time

# S-box and inverse (from PRESENT cipher)
S = [12, 5, 6, 11, 9, 0, 10, 13, 3, 14, 15, 8, 4, 7, 1, 2]
S_inv = [5, 14, 15, 8, 12, 1, 2, 13, 11, 4, 6, 3, 0, 7, 9, 10]

# MixColumn multiplication table over GF(2^4) with x^4 + x + 1 as modulus
mul_table = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [0, 2, 4, 6, 8, 10, 12, 14, 3, 1, 7, 5, 11, 9, 15, 13],
    [0, 3, 6, 5, 12, 15, 10, 9, 11, 8, 13, 14, 7, 4, 1, 2],
    [0, 4, 8, 12, 3, 7, 11, 15, 6, 2, 14, 10, 5, 1, 13, 9],
    [0, 5, 10, 15, 7, 2, 13, 8, 14, 11, 4, 1, 9, 12, 3, 6],
    [0, 6, 12, 10, 11, 13, 7, 1, 5, 3, 9, 15, 14, 8, 2, 4],
    [0, 7, 14, 9, 15, 8, 1, 6, 13, 10, 3, 4, 2, 5, 12, 11],
    [0, 8, 3, 11, 6, 14, 5, 13, 12, 4, 15, 7, 10, 2, 9, 1],
    [0, 9, 1, 8, 2, 11, 3, 10, 4, 13, 5, 12, 6, 15, 7, 14],
    [0, 10, 7, 13, 14, 4, 9, 3, 15, 5, 8, 2, 1, 11, 6, 12],
    [0, 11, 5, 14, 10, 1, 15, 4, 7, 12, 2, 9, 13, 6, 8, 3],
    [0, 12, 11, 7, 5, 9, 14, 2, 10, 6, 1, 13, 15, 3, 4, 8],
    [0, 13, 9, 4, 1, 12, 8, 5, 2, 15, 11, 6, 3, 14, 10, 7],
    [0, 14, 15, 1, 13, 3, 2, 12, 9, 7, 6, 8, 4, 10, 11, 5],
    [0, 15, 13, 2, 9, 6, 4, 11, 1, 14, 12, 3, 8, 7, 5, 10],
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
    ddt = [[[] for _ in range(16)] for _ in range(16)]
    for d in range(16):
        for x in range(16):
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
                    for diff in range(1, 16):
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
    all_params = list(itertools.product(range(16), repeat=6))

    with Pool(processes=cpu_count()) as pool:
        results = pool.map(task, all_params)

    multisets = [r for group in results if group for r in group]
    print("Total multisets (log2):", math.log2(len(multisets)))
    print("Distinct multisets (log2):", math.log2(len(set(multisets))))
    print("Elapsed time: {:.2f} seconds".format(time.time() - start))
