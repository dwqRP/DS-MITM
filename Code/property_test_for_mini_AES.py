import math
import sys
from multiprocessing import Pool, cpu_count

# AES S-box
SBOX = [
    0x63,
    0x7C,
    0x77,
    0x7B,
    0xF2,
    0x6B,
    0x6F,
    0xC5,
    0x30,
    0x01,
    0x67,
    0x2B,
    0xFE,
    0xD7,
    0xAB,
    0x76,
    0xCA,
    0x82,
    0xC9,
    0x7D,
    0xFA,
    0x59,
    0x47,
    0xF0,
    0xAD,
    0xD4,
    0xA2,
    0xAF,
    0x9C,
    0xA4,
    0x72,
    0xC0,
    0xB7,
    0xFD,
    0x93,
    0x26,
    0x36,
    0x3F,
    0xF7,
    0xCC,
    0x34,
    0xA5,
    0xE5,
    0xF1,
    0x71,
    0xD8,
    0x31,
    0x15,
    0x04,
    0xC7,
    0x23,
    0xC3,
    0x18,
    0x96,
    0x05,
    0x9A,
    0x07,
    0x12,
    0x80,
    0xE2,
    0xEB,
    0x27,
    0xB2,
    0x75,
    0x09,
    0x83,
    0x2C,
    0x1A,
    0x1B,
    0x6E,
    0x5A,
    0xA0,
    0x52,
    0x3B,
    0xD6,
    0xB3,
    0x29,
    0xE3,
    0x2F,
    0x84,
    0x53,
    0xD1,
    0x00,
    0xED,
    0x20,
    0xFC,
    0xB1,
    0x5B,
    0x6A,
    0xCB,
    0xBE,
    0x39,
    0x4A,
    0x4C,
    0x58,
    0xCF,
    0xD0,
    0xEF,
    0xAA,
    0xFB,
    0x43,
    0x4D,
    0x33,
    0x85,
    0x45,
    0xF9,
    0x02,
    0x7F,
    0x50,
    0x3C,
    0x9F,
    0xA8,
    0x51,
    0xA3,
    0x40,
    0x8F,
    0x92,
    0x9D,
    0x38,
    0xF5,
    0xBC,
    0xB6,
    0xDA,
    0x21,
    0x10,
    0xFF,
    0xF3,
    0xD2,
    0xCD,
    0x0C,
    0x13,
    0xEC,
    0x5F,
    0x97,
    0x44,
    0x17,
    0xC4,
    0xA7,
    0x7E,
    0x3D,
    0x64,
    0x5D,
    0x19,
    0x73,
    0x60,
    0x81,
    0x4F,
    0xDC,
    0x22,
    0x2A,
    0x90,
    0x88,
    0x46,
    0xEE,
    0xB8,
    0x14,
    0xDE,
    0x5E,
    0x0B,
    0xDB,
    0xE0,
    0x32,
    0x3A,
    0x0A,
    0x49,
    0x06,
    0x24,
    0x5C,
    0xC2,
    0xD3,
    0xAC,
    0x62,
    0x91,
    0x95,
    0xE4,
    0x79,
    0xE7,
    0xC8,
    0x37,
    0x6D,
    0x8D,
    0xD5,
    0x4E,
    0xA9,
    0x6C,
    0x56,
    0xF4,
    0xEA,
    0x65,
    0x7A,
    0xAE,
    0x08,
    0xBA,
    0x78,
    0x25,
    0x2E,
    0x1C,
    0xA6,
    0xB4,
    0xC6,
    0xE8,
    0xDD,
    0x74,
    0x1F,
    0x4B,
    0xBD,
    0x8B,
    0x8A,
    0x70,
    0x3E,
    0xB5,
    0x66,
    0x48,
    0x03,
    0xF6,
    0x0E,
    0x61,
    0x35,
    0x57,
    0xB9,
    0x86,
    0xC1,
    0x1D,
    0x9E,
    0xE1,
    0xF8,
    0x98,
    0x11,
    0x69,
    0xD9,
    0x8E,
    0x94,
    0x9B,
    0x1E,
    0x87,
    0xE9,
    0xCE,
    0x55,
    0x28,
    0xDF,
    0x8C,
    0xA1,
    0x89,
    0x0D,
    0xBF,
    0xE6,
    0x42,
    0x68,
    0x41,
    0x99,
    0x2D,
    0x0F,
    0xB0,
    0x54,
    0xBB,
    0x16,
]

ddt = [[0] * 256 for _ in range(256)]


def init_ddt():
    for d in range(256):
        for x in range(256):
            y = SBOX[x] ^ SBOX[x ^ d]
            ddt[d][y] += 1


def test_Sbox():
    cnt0 = 0
    cnt2 = 0
    cnt4 = 0
    for i in range(1, 1 << 8):
        for j in range(1, 1 << 8):
            if ddt[i][j] == 0:
                cnt0 += 1
            if ddt[i][j] == 2:
                cnt2 += 1
            if ddt[i][j] == 4:
                cnt4 += 1
    print(cnt0, cnt2, cnt4)


def xtime(a: int) -> int:
    """在 GF(2^8) 上实现乘以 0x02 的“xtime”"""
    return ((a << 1) ^ 0x1B) & 0xFF if (a & 0x80) else (a << 1) & 0xFF


def gmul(a: int, b: int) -> int:
    """
    在 GF(2^8) 上计算乘法 a * b。
    利用移位和条件异或，适用于任意字节 a, b。
    """
    res = 0
    for _ in range(8):
        if b & 1:
            res ^= a
        b >>= 1
        a = xtime(a)
    return res


MC = [[0x02, 0x03], [0x03, 0x02]]
MC_INV = [[0x02, 0x03], [0x03, 0x02]]


def mix_columns_2x2(state: list[list[int]]) -> list[list[int]]:
    """
    对 2x2 状态执行 MixColumns：new = MC * state
    state 也是一个 2x2 的列表，按列主序存储字节。
    """
    new = [[0, 0], [0, 0]]
    for c in range(2):
        s0, s1 = state[0][c], state[1][c]
        new[0][c] = gmul(MC[0][0], s0) ^ gmul(MC[0][1], s1)
        new[1][c] = gmul(MC[1][0], s0) ^ gmul(MC[1][1], s1)
    return new


def inv_mix_columns_2x2(state: list[list[int]]) -> list[list[int]]:
    """执行逆 MixColumns："new = MC_INV * state"。"""
    new = [[0, 0], [0, 0]]
    for c in range(2):
        s0, s1 = state[0][c], state[1][c]
        new[0][c] = gmul(MC_INV[0][0], s0) ^ gmul(MC_INV[0][1], s1)
        new[1][c] = gmul(MC_INV[1][0], s0) ^ gmul(MC_INV[1][1], s1)
    return new


def compute_for_a(a: int) -> int:
    """
    对固定的 a 值遍历 b, c, d，并计算累加值。
    返回对这一 a 的局部 ans。
    """
    # 确保 ddt 已经初始化
    # 如果你在主进程里已经调用过 init_ddt()，且使用 'fork' 启动，那么子进程会继承好状态。
    partial = 0
    for b in range(1, 256):
        for c in range(1, 256):
            for d in range(1, 256):
                A = [[a, 0], [0, b]]
                B = [[c, 0], [0, d]]
                B_inv = inv_mix_columns_2x2(B)
                A1 = mix_columns_2x2(A)
                # 注意 B1 的第二行做了列交换
                B1 = [B_inv[0], [B_inv[1][1], B_inv[1][0]]]
                tmp = 1
                for i in range(2):
                    for j in range(2):
                        tmp *= ddt[A1[i][j]][B1[i][j]]
                partial += tmp
    return partial


if __name__ == "__main__":
    # 1. 初始化 DDT
    init_ddt()

    # 2. 构造任务：a 从 1 到 255
    tasks = list(range(1, 256))

    # 3. 启动进程池
    n_proc = min(cpu_count(), len(tasks))
    print(f"检测到 {cpu_count()} 个核心，使用 {n_proc} 个进程并行计算…")
    with Pool(processes=n_proc) as pool:
        # 并行计算每个 a 的部分结果
        partial_results = pool.map(compute_for_a, tasks)

    # 4. 汇总结果并打印 log2(ans)
    total = sum(partial_results)
    print("log2(ans) =", math.log2(total))
