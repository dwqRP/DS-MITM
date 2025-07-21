S = [1, 10, 4, 12, 6, 15, 3, 9, 2, 13, 11, 7, 5, 0, 8, 14]

S_inv = [13, 0, 8, 6, 2, 12, 4, 11, 14, 7, 1, 10, 3, 9, 15, 5]


def func(k):
    setl = set()
    for i in range(16):
        for j in range(16):
            if (S[i] ^ S[j]) >> 2 == k:
                val1 = i >> 2
                val2 = j >> 2
                val3 = (i ^ j) & 3
                val = (val1 << 4) | (val2 << 2) | val3
                setl.add(val)
    print(len(setl))
    for e in setl:
        print(bin(e))


def func_inv(k):
    setl = set()
    for i in range(16):
        for j in range(16):
            if (S_inv[i] ^ S_inv[j]) >> 2 == k:
                val1 = i >> 2
                val2 = j >> 2
                val3 = (i ^ j) & 3
                val = (val1 << 4) | (val2 << 2) | val3
                setl.add(val)
    print(len(setl))
    for e in setl:
        print(bin(e))


def test():
    ans = 0
    for i in range(16):
        for j in range(16):
            dy = S[i] ^ S[j]
            if (dy & 3 == 0) and (dy >> 3 == 1):
                print(i, j)
                ans += 1
    print(ans)


if __name__ == "__main__":
    # func(0)
    # func_inv(0)
    test()
