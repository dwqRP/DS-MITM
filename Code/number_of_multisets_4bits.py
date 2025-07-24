from collections import Counter
import time
import math

# GF(2^4)
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


# MC = MC_inv
MC = [[2, 3], [3, 2]]

S = [12, 5, 6, 11, 9, 0, 10, 13, 3, 14, 15, 8, 4, 7, 1, 2]
S_inv = [5, 14, 15, 8, 12, 1, 2, 13, 11, 4, 6, 3, 0, 7, 9, 10]

ddt = [
    [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []] for _ in range(16)
]

data = []


def output(state: list[list[int]]):
    for row in state:
        print([x for x in row])


def mix_column(state: list[list[int]]) -> list[list[int]]:
    new = [[0, 0], [0, 0]]
    for c in range(2):
        s0, s1 = state[0][c], state[1][c]
        new[0][c] = mul_table[MC[0][0]][s0] ^ mul_table[MC[0][1]][s1]
        new[1][c] = mul_table[MC[1][0]][s0] ^ mul_table[MC[1][1]][s1]
    return new


def init_ddt():
    for d in range(16):
        for x in range(16):
            y = S[x] ^ S[x ^ d]
            ddt[d][y].append(x)


def compute_multiset(X2, X3, X4):
    res = []
    for diff in range(1, 16):
        delta_Z1 = [[diff, 0], [0, 0]]
        delta_X2 = mix_column(delta_Z1)
        delta_Y2 = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                delta_Y2[i][j] = S[X2[i][j]] ^ S[X2[i][j] ^ delta_X2[i][j]]
        delta_Z2 = [delta_Y2[0], [delta_Y2[1][1], delta_Y2[1][0]]]
        delta_X3 = mix_column(delta_Z2)
        delta_Y3 = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                delta_Y3[i][j] = S[X3[i][j]] ^ S[X3[i][j] ^ delta_X3[i][j]]
        delta_Z3 = [delta_Y3[0], [delta_Y3[1][1], delta_Y3[1][0]]]
        delta_X4 = mix_column(delta_Z3)
        delta_Y4 = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                delta_Y4[i][j] = S[X4[i][j]] ^ S[X4[i][j] ^ delta_X4[i][j]]
        delta_Z4 = [delta_Y4[0], [delta_Y4[1][1], delta_Y4[1][0]]]
        delta_W4 = mix_column(delta_Z4)
        res.append(delta_W4[0][0])
    data.append(res)


if __name__ == "__main__":
    start = time.time()
    last = 0
    prog = 0
    # output(mix_column(MC))
    init_ddt()
    # output(ddt)

    for p in range(1 << 24):
        parameters = []
        tmp = p
        for i in range(6):
            parameters.append(tmp & 15)
            tmp >>= 4
        # parameters:
        # 0 -> delta_Z1[0]
        # 1,2 -> X2[0,1]
        # 3,4 -> X4[0,3]
        # 5 -> delta_W4[0]
        if parameters[0] == 0 or parameters[5] == 0:
            continue

        # Compute delta_X3
        delta_Z1 = [[parameters[0], 0], [0, 0]]
        delta_X2 = mix_column(delta_Z1)
        X2 = [[parameters[1], 0], [parameters[2], 0]]
        delta_Y2 = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                delta_Y2[i][j] = S[X2[i][j]] ^ S[X2[i][j] ^ delta_X2[i][j]]
        delta_Z2 = [delta_Y2[0], [delta_Y2[1][1], delta_Y2[1][0]]]
        delta_X3 = mix_column(delta_Z2)

        # Compute delta_Y3
        delta_W4 = [[parameters[5], 0], [0, 0]]
        delta_Z4 = mix_column(delta_W4)
        delta_Y4 = [delta_Z4[0], [delta_Z4[1][1], delta_Z4[1][0]]]
        X4 = [[parameters[3], 0], [0, parameters[4]]]
        delta_X4 = [[0, 0], [0, 0]]
        for i in range(2):
            for j in range(2):
                delta_X4[i][j] = X4[i][j] ^ S_inv[S[X4[i][j]] ^ delta_Y4[i][j]]
        delta_Z3 = mix_column(delta_X4)
        delta_Y3 = [delta_Z3[0], [delta_Z3[1][1], delta_Z3[1][0]]]

        # Compute X3
        for i in range(2):
            for j in range(2):
                assert delta_X3[i][j] != 0
                assert delta_Y3[i][j] != 0
                if len(ddt[delta_X3[i][j]][delta_Y3[i][j]]) == 0:
                    break
        for a in ddt[delta_X3[0][0]][delta_Y3[0][0]]:
            for b in ddt[delta_X3[0][1]][delta_Y3[0][1]]:
                for c in ddt[delta_X3[1][0]][delta_Y3[1][0]]:
                    for d in ddt[delta_X3[1][1]][delta_Y3[1][1]]:
                        X3 = [[a, b], [c, d]]
                        compute_multiset(X2, X3, X4)
                        if len(data) - last >= (1 << 16):
                            last = len(data)
                            prog += 0.4
                            print(
                                "Time: {:.2f} s    Percent: {} %".format(
                                    time.time() - start, prog
                                ),
                                flush=True,
                            )

    # canonical = map(lambda lst: frozenset(Counter(lst).items()), data)
    # distinct = set(canonical)
    canonical = map(lambda lst: tuple(sorted(lst)), data)
    distinct = set(canonical)

    print(math.log2(len(data)))
    print(f"Number of distinct multisets: {math.log2(len(distinct))}")
