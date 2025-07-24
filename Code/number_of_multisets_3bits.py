from collections import Counter
import time
import math

# GF(2^3)
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


# MC = MC_inv
MC = [[2, 3], [3, 2]]

S = [0, 1, 3, 6, 7, 4, 5, 2]
S_inv = [0, 1, 7, 2, 5, 6, 3, 4]

ddt = [[[], [], [], [], [], [], [], []] for _ in range(8)]

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
    for d in range(8):
        for x in range(8):
            y = S[x] ^ S[x ^ d]
            ddt[d][y].append(x)


def compute_multiset(X2, X3, X4):
    res = []
    for diff in range(1, 8):
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
    for p in range(1 << 18):
        parameters = []
        tmp = p
        for i in range(6):
            parameters.append(tmp & 7)
            tmp >>= 3
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
                        if len(data) - last >= (1 << 14):
                            last = len(data)
                            prog += 6.25
                            print(
                                "Time: {:.2f} s    Percent: {} %".format(
                                    time.time() - start, prog
                                )
                            )

    # canonical = map(lambda lst: frozenset(Counter(lst).items()), data)
    # distinct = set(canonical)
    canonical = map(lambda lst: tuple(sorted(lst)), data)
    distinct = set(canonical)

    # with open("result", "w") as f:
    #     f.write(str(data))
    print(math.log2(len(data)))
    print(f"Number of distinct multisets: {math.log2(len(distinct))}")
