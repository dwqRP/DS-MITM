import numpy as np

dict_index = {}
dict_key = {}


def Init(R, K0):
    X = set()
    K = set()
    cnt = 0
    for rd in range(R + 1):
        if rd < R:
            for i in range(12, 16):
                dict_index[(rd, i, 1)] = cnt
                dict_key[cnt] = (rd, i, 1)
                cnt += 1
                X.add((rd, i, 1))
        for i in range(16):
            dict_index[(rd, i, 0)] = cnt
            dict_key[cnt] = (rd, i, 0)
            cnt += 1
            X.add((rd, i, 0))
            if K0[rd][i] == 1:
                K.add((rd, i, 0))
                if (rd, i, 1) in X:
                    K.add((rd, i, 1))

    row_number = 16 * R
    col_number = len(X)
    # print(row_number, col_number, cnt)
    M = np.zeros((row_number, col_number))
    for rd in range(R):
        for i in range(4):
            M[16 * rd + i, dict_index[(rd, i, 0)]] = 1
            M[16 * rd + i, dict_index[(rd + 1, i, 0)]] = 1
            M[16 * rd + i, dict_index[(rd, 12 + (1 + i) % 4, 1)]] = 1
        for i in range(4, 16):
            M[16 * rd + i, dict_index[(rd, i, 0)]] = 1
            M[16 * rd + i, dict_index[(rd + 1, i, 0)]] = 1
            M[16 * rd + i, dict_index[(rd + 1, i - 4, 0)]] = 1
    return X, K, M.astype(np.uint8)


def Gf_mul(a: int, b: int) -> int:
    """Multiply two bytes in GF(2^8) with AES modulus 0x11b. Inputs 0..255, returns 0..255"""
    a &= 0xFF
    b &= 0xFF
    res = 0
    while b:
        if b & 1:
            res ^= a
        b >>= 1
        carry = a & 0x80
        a = (a << 1) & 0xFF
        if carry:
            a ^= 0x1B  # 0x11b without the x^8 bit
    return res & 0xFF


def Gf_pow(a: int, e: int) -> int:
    """Fast exponentiation in GF(256) using Gf_mul."""
    a &= 0xFF
    result = 1
    while e > 0:
        if e & 1:
            result = Gf_mul(result, a)
        a = Gf_mul(a, a)
        e >>= 1
    return result & 0xFF


def Gf_inv(a: int) -> int:
    """Multiplicative inverse in GF(256). a must be non-zero. Use a^(254)."""
    if a == 0:
        raise ZeroDivisionError("0 has no multiplicative inverse in GF(2^8)")
    return Gf_pow(a, 254)


def Gauss_elimination(M, n):
    m, p = M.shape
    if not (1 <= n <= p):
        raise ValueError("n must satisfy 1 <= n <= number of columns")
    A = M.copy()
    row = 0
    for col in range(n):
        if row >= m:
            break
        pivot_row = None
        for r in range(row, m):
            if A[r, col] != 0:
                pivot_row = r
                break
        if pivot_row == None:
            continue
        if pivot_row != row:
            A[[row, pivot_row], :] = A[[pivot_row, row], :]
        pivot_val = A[row, col]
        inv = Gf_inv(pivot_val)
        for j in range(p):
            A[row, j] = Gf_mul(A[row, j], inv)
        for r in range(m):
            if r == row:
                continue
            factor = A[r, col]
            if factor != 0:
                for j in range(p):
                    prod = Gf_mul(A[row, j], factor)
                    A[r, j] ^= prod
        row += 1
    return A


def Swap_column(M, i, j):
    if i == j:
        return M
    k1 = dict_key[i]
    k2 = dict_key[j]
    dict_key[i] = k2
    dict_key[j] = k1
    dict_index[k1] = j
    dict_index[k2] = i
    M[:, [i, j]] = M[:, [j, i]]
    return M


def Knowledge_propagation(X, K, M):
    m, p = M.shape
    for idx, k in enumerate(K):
        M = Swap_column(M, dict_index[k], p - idx - 1)
    # print(M)
    print("Start Knowledge_propagation:")
    flag = True
    unk = p - len(K)
    while flag:
        flag = False
        M = Gauss_elimination(M, unk)
        # print(M)
        # print("dict_key: ", dict_key)
        # print("dict_index: ", dict_index)
        for r in range(m):
            # Situation 2
            lst = [j for j in range(unk) if M[r, j] == 1]
            if len(lst) == 1:
                key_byte = dict_key[lst[0]]
                if key_byte[2] == 1:
                    continue
                flag = True
                unk -= 1
                M = Swap_column(M, lst[0], unk)
                K.add(key_byte)
                print(
                    "Propagate to k_" + str(key_byte[0]) + "[" + str(key_byte[1]) + "]"
                )
                S_key_byte = (key_byte[0], key_byte[1], 1)
                if S_key_byte in X:
                    unk -= 1
                    M = Swap_column(M, dict_index[S_key_byte], unk)
                    K.add(S_key_byte)
                    print(
                        "Propagate to S(k_"
                        + str(S_key_byte[0])
                        + "["
                        + str(S_key_byte[1])
                        + "])"
                    )
                break
    return K, M


if __name__ == "__main__":
    R = 7
    K0 = [
        [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
    ]
    X, K, M = Init(R, K0)
    print("Known Set: {", end=" ")
    for k in K:
        if k[2] == 0:
            print("k_" + str(k[0]) + "[" + str(k[1]) + "],", end=" ")
        if k[2] == 1:
            print("S(k_" + str(k[0]) + "[" + str(k[1]) + "]),", end=" ")
    print("}")
    # print(dic)
    # print(X)
    # print(K)
    # print(M.dtype)
    # print(M[0])
    K, M = Knowledge_propagation(X, K, M)
    print("Known Set: {", end=" ")
    for k in K:
        if k[2] == 0:
            print("k_" + str(k[0]) + "[" + str(k[1]) + "],", end=" ")
        if k[2] == 1:
            print("S(k_" + str(k[0]) + "[" + str(k[1]) + "]),", end=" ")
    print("}")
    print(len(X) - len(K), len(K))
    np.set_printoptions(threshold=np.inf, linewidth=np.inf)
    f = open("./Note/output.log", "w")
    f.write(str(M))
    f.close()
