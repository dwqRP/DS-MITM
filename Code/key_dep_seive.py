import numpy as np

S1 = np.array([[1, 1, 0, 1], [1, 1, 0, 0], [1, 1, 1, 1], [1, 0, 1, 0]])

MC_inv = np.array([[0, 1, 0, 0], [0, 1, 1, 1], [0, 1, 0, 1], [1, 0, 0, 1]])

tmp = np.empty([4, 4])
for i in range(4):
    for j in range(4):
        tmp[i][j] = 1
        for k in range(4):
            if MC_inv[i][k] == 1 and S1[k][j] == 0:
                tmp[i][j] = 0
                break

ans = np.empty([4, 4])
for i in range(4):
    for j in range(4):
        ans[i][j] = tmp[i][(i + j) % 4]

print(ans)
