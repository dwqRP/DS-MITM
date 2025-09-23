from gurobipy import *

AES = Model("AES")

r_in = 1
r_dist = 4
r_out = 2

K_in = [
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
    [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
]
K_out = [
    [[0, 0, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],
    [[0, 1, 1, 0], [1, 1, 0, 0], [1, 0, 0, 1], [0, 0, 1, 1]],
]
# K_in = [[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]
# K_out = [
#     [[0, 0, 0, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]],
#     [[0, 1, 1, 1], [1, 1, 1, 0], [1, 1, 0, 1], [1, 0, 1, 1]],
# ]

state_M_l = {}  # VAR M
state_W_nl = {}  # VAR W

for rd in range(r_in + 1):
    state_M_l[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_M_l_" + str(rd))
    for i in range(4):
        lst = K_in[rd][i]
        for j in range(4):
            AES.addConstr(state_M_l[rd][j + 4 * i] == lst[j])

for rd in range(r_out):
    state_W_nl[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_W_nl_" + str(rd))
    for i in range(4):
        lst = K_out[rd][i]
        for j in range(4):
            AES.addConstr(state_W_nl[rd][j + 4 * i] == lst[j])

involved_k = {}
involved_u = {}
# k = MC(u)
m = 4 * (r_in + r_dist + r_out + 1)
for i in range(m):
    involved_k[i] = AES.addVars(4, vtype=GRB.BINARY, name="involved_k_" + str(i))
    involved_u[i] = AES.addVars(4, vtype=GRB.BINARY, name="involved_u_" + str(i))

for rd in range(r_in + 1):
    for i in range(4):
        AES.addConstrs(
            involved_k[4 * rd + i][j] == state_M_l[rd][4 * i + j] for j in range(4)
        )
        AES.addConstrs(involved_u[4 * rd + i][j] == 0 for j in range(4))

for rd in range(r_dist):
    for i in range(4):
        AES.addConstrs(involved_k[4 * (rd + r_in + 1) + i][j] == 0 for j in range(4))
        AES.addConstrs(involved_u[4 * (rd + r_in + 1) + i][j] == 0 for j in range(4))

# Last round: MC omit - k; MC exsit - u
for rd in range(r_out):
    for i in range(4):
        idx = 4 * (rd + r_in + r_dist + 1) + i
        AES.addConstrs(involved_k[idx][j] == 0 for j in range(4))
        AES.addConstrs(
            involved_u[idx][j] == state_W_nl[rd][4 * i + j] for j in range(4)
        )
        # AES.addConstrs(involved_u[idx][j] == 0 for j in range(4))
        # AES.addConstrs(
        #     involved_k[idx][j] == state_W_nl[rd][4 * i + j] for j in range(4)
        # )


def calc(x, y):
    return 4 * x + y


def Get_idx_k(x, y, typ):
    # typ0: len = 1 & (x-4,x-1) -> x
    a, b = -1, -1
    if typ == 0:
        if x - 4 < 0:
            return -1, -1
        a = calc(x - 4, y)
        if x % 4 == 0:  # column 0
            b = calc(x - 1, (y + 1) % 4)
        else:  # column 1,2,3
            b = calc(x - 1, y)
    # typ1: len = 1 & (x+3,x+4) -> x
    if typ == 1:
        if x + 4 >= m:
            return -1, -1
        a = calc(x + 4, y)
        if x % 4 == 0:  # column 0
            b = calc(x + 3, (y + 1) % 4)
        else:  # column 1,2,3
            b = calc(x + 3, y)
    # typ2: len = 1 & (x-3,x+1) -> x
    if typ == 2:
        if x + 1 >= m or x - 3 < 0:
            return -1, -1
        if x % 4 == 3:  # column 3
            a = calc(x - 3, (y + 3) % 4)
            b = calc(x + 1, (y + 3) % 4)
        else:  # column 0,1,2
            a = calc(x - 3, y)
            b = calc(x + 1, y)
    # typ3: len = 2 & (x-8,x-2) -> x
    if typ == 3:
        if x - 8 < 0:
            return -1, -1
        a = calc(x - 8, y)
        if x % 4 <= 1:  # column 0,1
            b = calc(x - 2, (y + 1) % 4)
        else:  # column 2,3
            b = calc(x - 2, y)
    # typ4: len = 2 & (x+6,x+8) -> x
    if typ == 4:
        if x + 8 >= m:
            return -1, -1
        a = calc(x + 8, y)
        if x % 4 <= 1:  # column 0,1
            b = calc(x + 6, (y + 1) % 4)
        else:  # column 2,3
            b = calc(x + 6, y)
    # typ5: len = 2 & (x-6,x+2) -> x
    if typ == 5:
        if x + 2 >= m or x - 6 < 0:
            return -1, -1
        if x % 4 >= 2:  # column 2,3
            a = calc(x - 6, (y + 3) % 4)
            b = calc(x + 2, (y + 3) % 4)
        else:  # column 0,1
            a = calc(x - 6, y)
            b = calc(x + 2, y)
    # typ6: len = 3 & (x-16,x-4) -> x
    if typ == 6:
        if x - 16 < 0:
            return -1, -1
        a = calc(x - 8, y)
        b = calc(x - 4, (y + 1) % 4)
    # typ7: len = 3 & (x+12,x+16) -> x
    if typ == 7:
        if x + 16 >= m:
            return -1, -1
        a = calc(x + 16, y)
        b = calc(x + 12, (y + 1) % 4)
    # typ8: len = 3 & (x-12,x+4) -> x
    if typ == 7:
        if x + 4 >= m or x - 12 < 0:
            return -1, -1
        a = calc(x - 12, (y + 3) % 4)
        b = calc(x + 4, (y + 3) % 4)
    return a, b


def Get_idx_u(x, y, typ):
    a, b = -1, -1
    # typ0: len = 1 & (x-4,x-1) -> x
    if typ == 0:
        if x - 4 < 0 or x % 4 == 0:
            return -1, -1
        a = calc(x - 4, y)
        b = calc(x - 1, y)
    # typ1: len = 1 & (x+3,x+4) -> x
    if typ == 1:
        if x + 4 >= m or x % 4 == 0:
            return -1, -1
        a = calc(x + 4, y)
        b = calc(x + 3, y)
    # typ2: len = 1 & (x-3,x+1) -> x
    if typ == 2:
        if x + 1 >= m or x - 3 < 0 or x % 4 == 3:
            return -1, -1
        a = calc(x - 3, y)
        b = calc(x + 1, y)
    # typ3: len = 2 & (x-8,x-2) -> x
    if typ == 3:
        if x - 8 < 0 or x % 4 <= 1:
            return -1, -1
        a = calc(x - 8, y)
        b = calc(x - 2, y)
    # typ4: len = 2 & (x+6,x+8) -> x
    if typ == 4:
        if x + 8 >= m or x % 4 <= 1:
            return -1, -1
        a = calc(x + 8, y)
        b = calc(x + 6, y)
    # typ5: len = 2 & (x-6,x+2) -> x
    if typ == 5:
        if x + 2 >= m or x - 6 < 0 or x % 4 >= 2:
            return -1, -1
        a = calc(x - 6, y)
        b = calc(x + 2, y)
    return a, b


beta = 2  # How many steps need to deduce a variable at most
n = 16 * (r_in + r_dist + r_out + 1)
kb_state_k = {}
kb_path_k = {}
kb_state_u = {}
kb_path_u = {}
kb_state_k[0] = AES.addVars(n, vtype=GRB.BINARY, name="kb_state_k_0")
kb_state_u[0] = AES.addVars(n, vtype=GRB.BINARY, name="kb_state_u_0")
for i in range(beta):  # For each step
    kb_state_k[i + 1] = AES.addVars(
        n, vtype=GRB.BINARY, name="kb_state_k_" + str(i + 1)
    )
    kb_path_k[i + 1] = {}
    for j in range(n):  # For each variable in k
        kb_path_k[i + 1][j] = AES.addVars(
            10, vtype=GRB.BINARY, name="kb_path_k_" + str(i + 1) + "_" + str(j)
        )
        col = j >> 2
        row = j % 4
        # For 10 relation
        for k in range(9):
            a, b = Get_idx_k(col, row, k)
            if a != -1 and b != -1:
                AES.addGenConstrAnd(
                    kb_path_k[i + 1][j][k], [kb_state_k[i][a], kb_state_k[i][b]]
                )
            else:
                AES.addConstr(kb_path_k[i + 1][j][k] == 0)
        # Relation: k = MC(u)
        sum = LinExpr()
        sum = quicksum(kb_state_k[i][calc(col, r)] for r in range(4)) + quicksum(
            kb_state_u[i][calc(col, r)] for r in range(4)
        )
        AES.addGenConstrIndicator(kb_path_k[i + 1][j][9], 1, sum >= 4)
        AES.addGenConstrIndicator(kb_path_k[i + 1][j][9], 0, sum <= 3)
        AES.addConstr(kb_state_k[i + 1][j] >= kb_state_k[i][j])  # already 1
        AES.addConstrs(
            kb_state_k[i + 1][j] >= kb_path_k[i + 1][j][k] for k in range(10)
        )
        AES.addConstr(
            kb_state_k[i + 1][j]
            <= kb_state_k[i][j] + quicksum(kb_path_k[i + 1][j][k] for k in range(10))
        )

    kb_state_u[i + 1] = AES.addVars(
        n, vtype=GRB.BINARY, name="kb_state_u_" + str(i + 1)
    )
    kb_path_u[i + 1] = {}
    for j in range(n):  # For each variable in u
        kb_path_u[i + 1][j] = AES.addVars(
            10, vtype=GRB.BINARY, name="kb_path_u_" + str(i + 1) + "_" + str(j)
        )
        col = j >> 2
        row = j % 4
        # For 7 relation
        # len = 4 does not suit for u
        for k in range(6):
            a, b = Get_idx_u(col, row, k)
            if a != -1 and b != -1:
                AES.addGenConstrAnd(
                    kb_path_u[i + 1][j][k], [kb_state_u[i][a], kb_state_u[i][b]]
                )
            else:
                AES.addConstr(kb_path_u[i + 1][j][k] == 0)
        # Relation: k = MC(u)
        sum = LinExpr()
        sum = quicksum(kb_state_k[i][calc(col, r)] for r in range(4)) + quicksum(
            kb_state_u[i][calc(col, r)] for r in range(4)
        )
        AES.addGenConstrIndicator(kb_path_u[i + 1][j][6], 1, sum >= 4)
        AES.addGenConstrIndicator(kb_path_u[i + 1][j][6], 0, sum <= 3)
        AES.addConstr(kb_state_u[i + 1][j] >= kb_state_u[i][j])  # already 1
        AES.addConstrs(kb_state_u[i + 1][j] >= kb_path_u[i + 1][j][k] for k in range(7))
        AES.addConstr(
            kb_state_u[i + 1][j]
            <= kb_state_u[i][j] + quicksum(kb_path_u[i + 1][j][k] for k in range(7))
        )

for i in range(m):
    AES.addConstrs(kb_state_k[beta][4 * i + j] >= involved_k[i][j] for j in range(4))
    AES.addConstrs(kb_state_u[beta][4 * i + j] >= involved_u[i][j] for j in range(4))


Obj = LinExpr()
Obj = quicksum(kb_state_k[0][i] for i in range(n)) + quicksum(
    kb_state_u[0][i] for i in range(n)
)
AES.setObjective(Obj, GRB.MINIMIZE)


def Print_var(rd, var):
    for i in range(4):
        print(
            round(var[rd][i].Xn),
            round(var[rd][i + 4].Xn),
            round(var[rd][i + 8].Xn),
            round(var[rd][i + 12].Xn),
        )


# AES.setParam("OutputFlag", 0)
AES.Params.PoolSearchMode = 2
AES.Params.PoolSolutions = 1  # Number of sols
AES.Params.PoolGap = 2.0
# AES.Params.TimeLimit = 200
AES.optimize()
print("Model Status:", AES.Status)
if AES.Status == 2 or AES.Status == 9:
    print("---------- Var M ----------")
    for rd in range(r_in + 1):
        print("M_linear[", rd, "]")
        Print_var(rd, state_M_l)
        if rd < r_in:
            print("-- R ->")

    print("---------- Var W ----------")
    for rd in range(r_out):
        print("W_linear[", rd + r_dist, "]")
        Print_var(rd, state_W_nl)
        if rd < r_out - 1:
            print("-- R ->")

    print("****** Min_Obj: %g ******" % AES.ObjVal)

    # print("---------- Involved key ----------")
    # for i in range(m):
    #     print(
    #         round(involved_k[i][0].Xn),
    #         round(involved_k[i][1].Xn),
    #         round(involved_k[i][2].Xn),
    #         round(involved_k[i][3].Xn),
    #     )
    # print("----------------------------------")
    # for i in range(m):
    #     print(
    #         round(involved_u[i][0].Xn),
    #         round(involved_u[i][1].Xn),
    #         round(involved_u[i][2].Xn),
    #         round(involved_u[i][3].Xn),
    #     )
