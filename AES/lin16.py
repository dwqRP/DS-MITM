import numpy as np

dict_index = {}
dict_key = {}
dict_str = {}


def Init(R, Guessed_key):
    X = set()
    K = set()
    cnt = 0
    for rd in range(R + 1):
        if rd < R:
            for i in range(12, 16):
                Sk = (rd, i, 1)
                dict_str[cnt] = "S(k_" + str(rd) + "[" + str(i) + "])"
                dict_index[Sk] = cnt
                dict_key[cnt] = Sk
                cnt += 1
                X.add(Sk)
        for i in range(16):
            k = (rd, i, 0)
            dict_str[cnt] = "k_" + str(rd) + "[" + str(i) + "]"
            dict_index[k] = cnt
            dict_key[cnt] = k
            cnt += 1
            X.add(k)
            if Guessed_key[rd][i] == 1:
                K.add(k)
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
    if not (0 <= n <= p):
        raise ValueError("n must satisfy 0 <= n <= number of columns")
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
    str1 = dict_str[i]
    str2 = dict_str[j]
    dict_key[i] = k2
    dict_key[j] = k1
    dict_str[i] = str2
    dict_str[j] = str1
    dict_index[k1] = j
    dict_index[k2] = i
    M[:, [i, j]] = M[:, [j, i]]
    return M


def Find_pivot(M, col):
    m, p = M.shape
    if not (0 <= col <= p - 1):
        raise ValueError("col must satisfy 0 <= col < number of columns")
    for r in range(m):
        lst = [j for j in range(col) if M[r, j] != 0]
        if len(lst) == 0 and M[r, col] == 1:
            return r
    return -1


def Check_multiple(p, q):
    if len(p) != len(q):
        raise ValueError("length of p must equals length of q")
    pos = -1
    for i, e in enumerate(q):
        if e != 0:
            pos = i
            break
    if pos == -1:
        raise ValueError("q can not be an all zero list")
    factor = Gf_mul(p[pos], Gf_inv(q[pos]))
    for i in range(len(p)):
        if p[i] != Gf_mul(factor, q[i]):
            return 0
    return 1


def Knowledge_propagation(X, K, M):
    m, p = M.shape
    for idx, k in enumerate(K):
        M = Swap_column(M, dict_index[k], p - idx - 1)
    # print(M)
    print("------ Start Knowledge_propagation: ------")
    flag = True
    unk = p - len(K)
    while flag:
        flag = False
        M = Gauss_elimination(M, unk)
        # print(M)
        # print("dict_key: ", dict_key)
        # print("dict_index: ", dict_index)
        for r in range(m):
            lst = [j for j in range(unk) if M[r, j] != 0]
            if len(lst) == 1:
                flag = True
                k = dict_key[lst[0]]
                # Situation 2
                if k[2] == 0:
                    unk -= 1
                    M = Swap_column(M, lst[0], unk)
                    K.add(k)
                    print("Propagate to " + dict_str[dict_index[k]])
                    Sk = (k[0], k[1], 1)
                    if Sk in X:
                        unk -= 1
                        M = Swap_column(M, dict_index[Sk], unk)
                        K.add(Sk)
                        print("Propagate to " + dict_str[dict_index[Sk]])
                # Situation 3 case (ii)
                else:
                    Sk = k
                    k = (Sk[0], Sk[1], 0)
                    unk -= 1
                    M = Swap_column(M, dict_index[k], unk)
                    K.add(k)
                    print("Propagate to " + dict_str[dict_index[k]])
                    unk -= 1
                    M = Swap_column(M, dict_index[Sk], unk)
                    K.add(Sk)
                    print("Propagate to " + dict_str[dict_index[Sk]])
                break
            # Situation 3 case (ii)
            if len(lst) == 2:
                kx = dict_key[lst[0]]
                ky = dict_key[lst[1]]
                if not (kx[0] == ky[0] and kx[1] == ky[1]):
                    continue
                flag = True
                if kx[2] == 0:
                    k = kx
                    Sk = ky
                else:
                    k = ky
                    Sk = kx
                unk -= 1
                M = Swap_column(M, dict_index[k], unk)
                K.add(k)
                print("Propagate to " + dict_str[dict_index[k]])
                unk -= 1
                M = Swap_column(M, dict_index[Sk], unk)
                K.add(Sk)
                print("Propagate to " + dict_str[dict_index[Sk]])
                break
        if flag == True:
            continue
        for Sk in X:
            if Sk[2] == 0:
                continue
            k = (Sk[0], Sk[1], 0)
            if (Sk in K and not (k in K)) or (k in K and not (Sk in K)):
                raise ValueError("Sk and k must both in K")
            if Sk in K:
                continue
            # Situation 3 case (i)
            mn = min(dict_index[k], dict_index[Sk])
            mx = max(dict_index[k], dict_index[Sk])
            rx = Find_pivot(M, mn)
            ry = Find_pivot(M, mx)
            # print(unk)
            # print(M[rx, :], mn)
            # print(M[ry, :], mx)
            if rx != -1 and ry != -1:
                non_zero = [j for j in range(mn + 1, mx) if M[rx, j] != 0]
                coeff_x = [M[rx, j] for j in range(mx + 1, unk)]
                coeff_y = [M[ry, j] for j in range(mx + 1, unk)]
                # print(coeff_x)
                # print(coeff_y)
                if len(non_zero) == 0 and Check_multiple(coeff_x, coeff_y) == 1:
                    flag = True
                    unk -= 1
                    M = Swap_column(M, dict_index[k], unk)
                    K.add(k)
                    print("Propagate to " + dict_str[dict_index[k]])
                    unk -= 1
                    M = Swap_column(M, dict_index[Sk], unk)
                    K.add(Sk)
                    print("Propagate to " + dict_str[dict_index[Sk]])
                    break
    return K, M


def Relation_derivation(K0, K, A2, offset):
    vis = set()
    m, p = A2.shape
    # print(m, p, offset)
    cnt = p + offset
    print("------ Start Relation_derivation: ------")
    flag = True
    # print(len(K0), len(K), m, p)
    exk = p - len(K0)
    while flag:
        flag = False
        A2 = Gauss_elimination(A2, exk)
        # print(A2)
        for r in range(m):
            lst = [j for j in range(exk) if A2[r, j] != 0]
            if len(lst) == 1:
                k = dict_key[lst[0] + offset]
                # print(dict_str[lst[0] + offset])
                if k[2] == 0 and (k[0], k[1], 1) in K:
                    if k in vis:
                        continue
                    # coeff = [i for i in range(exk, p) if A2[r, i] != 0]
                    # if len(coeff) == 1:
                    #     continue
                    flag = True
                    vis.add(k)
                    vis.add((k[0], k[1], 1))
                    dict_str[cnt] = "S("
                    for i in range(exk, p):
                        if A2[r, i] != 0:
                            if dict_str[cnt] != "S(":
                                dict_str[cnt] += " + "
                            if A2[r, i] == 1:
                                dict_str[cnt] += dict_str[i + offset]
                            else:
                                dict_str[cnt] += (
                                    str(A2[r, i]) + "*" + dict_str[i + offset]
                                )
                    dict_str[cnt] += ")"
                    print(dict_str[dict_index[((k[0], k[1], 1))]], "=", dict_str[cnt])
                    p += 1
                    m += 1
                    cnt += 1
                    A2 = np.pad(
                        A2, ((0, 1), (0, 1)), mode="constant", constant_values=0
                    )
                    A2[-1, -1] = 1
                    A2[-1, dict_index[(k[0], k[1], 1)] - offset] = 1
                    break
                if k[2] == 1:
                    if k in vis:
                        continue
                    # coeff = [i for i in range(exk, p) if A2[r, i] != 0]
                    # if len(coeff) == 1:
                    #     continue
                    flag = True
                    vis.add(k)
                    vis.add((k[0], k[1], 0))
                    dict_str[cnt] = "inv_S("
                    for i in range(exk, p):
                        if A2[r, i] != 0:
                            if dict_str[cnt] != "inv_S(":
                                dict_str[cnt] += " + "
                            if A2[r, i] == 1:
                                dict_str[cnt] += dict_str[i + offset]
                            else:
                                dict_str[cnt] += (
                                    str(A2[r, i]) + "*" + dict_str[i + offset]
                                )
                    dict_str[cnt] += ")"
                    print(dict_str[dict_index[((k[0], k[1], 0))]], "=", dict_str[cnt])
                    p += 1
                    m += 1
                    cnt += 1
                    A2 = np.pad(
                        A2, ((0, 1), (0, 1)), mode="constant", constant_values=0
                    )
                    A2[-1, -1] = 1
                    A2[-1, dict_index[(k[0], k[1], 0)] - offset] = 1
                    break
    Relations = []
    A2 = Gauss_elimination(A2, p)
    # print(p)
    # print(A2)
    st = -1
    for r in range(m):
        if not (A2[r, :exk].any()):
            st = r
            break
    # print(st)
    if st != -1:
        B2 = A2[st:, exk:]
        print("B2:", B2)
        row, col = B2.shape
        for r in range(row):
            rel = ""
            for j in range(col):
                if B2[r, j] != 0:
                    if rel != "":
                        rel += " + "
                    if B2[r, j] == 1:
                        rel += dict_str[j + offset + exk]
                    else:
                        rel += str(B2[r, j]) + "*" + dict_str[j + offset + exk]
            rel += " = 0"
            Relations.append(rel)
    return Relations


def Key_relation_search(Guessed_key):
    R = len(Guessed_key) - 1
    X, K, M = Init(R, Guessed_key)
    K0 = K.copy()
    print("Number of Known Key Bytes:", len(K0))
    print("Known Set: {", end=" ")
    for k in K0:
        print(dict_str[dict_index[k]], end=", ")
    print("}")
    # print(X)
    # print(K)
    # print(M.dtype)
    # print(M[0])
    K, M = Knowledge_propagation(X, K, M)
    m, p = M.shape
    print("Unknown:", p - len(K))
    print("Known:", len(K))
    print("Extended Set: {", end=" ")
    for k in K:
        print(dict_str[dict_index[k]], end=", ")
    print("}")
    np.set_printoptions(threshold=np.inf, linewidth=np.inf)
    # f = open("./Note/output.log", "w")
    # f.write(str(M[:, : (len(X) - len(K))]))
    for r in range(m):
        if not (M[r, : p - len(K)].any()):
            st = r
            break
    # print("st:", st)
    # f.write(str(M[st:, : p - len(K)]))
    A2 = M[st:, p - len(K) :]
    print("rank of A2:", np.linalg.matrix_rank(A2))
    row_A2, col_A2 = A2.shape
    print("number of row of A2:", row_A2, "; number of column of A2:", col_A2)
    print("A2:", A2)
    Relations = Relation_derivation(K0, K, A2, p - len(K))
    print("Number of Relations:", len(Relations))
    print("Relations Found:")
    for rel in Relations:
        print(rel)
    return Relations
    # f.close()


if __name__ == "__main__":
    Guessed_key = [
        [1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0],
    ]
    Key_relation_search(Guessed_key)
