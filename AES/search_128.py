# MC involved in last round
# Consider AES-128 first
# Consider sequence first
# r_dist >= 2

from gurobipy import *

SR = [0, 5, 10, 15, 4, 9, 14, 3, 8, 13, 2, 7, 12, 1, 6, 11]

AES = Model("AES")
# l -(ARK,SB,SR)-> nl -(MC)-> l
state_X_l = {}  # VAR X: parameters
state_X_nl = {}
dummy_MC_st = AES.addVars(4, vtype=GRB.BINARY, name="dummy_MC_st")
state_Y_l = {}  # VAR Y: parameters
state_Y_nl = {}
dummy_MC_ed = AES.addVars(4, vtype=GRB.BINARY, name="dummy_MC_ed")
state_Z = {}  # VAR Z: parameters
state_W_l = {}  # VAR W
state_W_nl = {}
state_M_l = {}  # VAR M
state_M_nl = {}
involved_k = {}
involved_u = {}
kb_state_k = {}
kb_path_k = {}
kb_state_u = {}
kb_path_u = {}
Deg = LinExpr()
Data = LinExpr()
Key = LinExpr()
Obj = AES.addVar(vtype=GRB.INTEGER, name="Obj")


def Evaluate_expr(le):
    val = 0
    for i in range(le.size()):
        coeff = le.getCoeff(i)
        var = le.getVar(i)
        val += coeff * round(var.Xn)
    return val


def Build_mixcolumn(var1, r1, var2, r2):
    for i in range(4):
        AES.addConstrs(var1[r1][i] >= var2[r2][j] for j in range(4))
        AES.addConstr(var1[r1][i] <= quicksum(var2[r2][j] for j in range(4)))
        AES.addConstrs(var1[r1][i + 4] >= var2[r2][j + 4] for j in range(4))
        AES.addConstr(var1[r1][i + 4] <= quicksum(var2[r2][j + 4] for j in range(4)))
        AES.addConstrs(var1[r1][i + 8] >= var2[r2][j + 8] for j in range(4))
        AES.addConstr(var1[r1][i + 8] <= quicksum(var2[r2][j + 8] for j in range(4)))
        AES.addConstrs(var1[r1][i + 12] >= var2[r2][j + 12] for j in range(4))
        AES.addConstr(var1[r1][i + 12] <= quicksum(var2[r2][j + 12] for j in range(4)))


# Offline phase
def Build_distinguisher(r_dist):
    # VAR X - forward differential
    state_X_nl[0] = AES.addVars(16, vtype=GRB.BINARY, name="state_X_nl_0")
    for rd in range(1, r_dist):
        state_X_l[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_X_l_" + str(rd))
        state_X_nl[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_X_nl_" + str(rd))
        # MC
        if rd == 1:  # GDS-MITM
            for i in range(4):
                AES.addConstr(
                    quicksum(state_X_l[rd][j + 4 * i] for j in range(4))
                    + quicksum(state_X_nl[rd - 1][j + 4 * i] for j in range(4))
                    >= 5 * dummy_MC_st[i]
                )
                for j in range(4):
                    AES.addConstr(dummy_MC_st[i] >= state_X_l[rd][j + 4 * i])
                    AES.addConstr(dummy_MC_st[i] >= state_X_nl[rd - 1][j + 4 * i])
        else:
            Build_mixcolumn(state_X_l, rd, state_X_nl, rd - 1)
        # SR
        AES.addConstrs(state_X_nl[rd][i] == state_X_l[rd][SR[i]] for i in range(16))

    # VAR Y - backward determination
    state_Y_l[r_dist] = AES.addVars(
        16, vtype=GRB.BINARY, name="state_Y_l_" + str(r_dist)
    )
    for rd in range(r_dist - 1, 0, -1):
        state_Y_nl[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_Y_nl_" + str(rd))
        state_Y_l[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_Y_l_" + str(rd))
        # MC
        if rd == r_dist - 1:  # GDS-MITM
            for i in range(4):
                AES.addConstr(
                    quicksum(state_Y_l[rd + 1][j + 4 * i] for j in range(4))
                    + quicksum(state_Y_nl[rd][j + 4 * i] for j in range(4))
                    >= 5 * dummy_MC_ed[i]
                )
                for j in range(4):
                    AES.addConstr(dummy_MC_ed[i] >= state_Y_l[rd + 1][j + 4 * i])
                    AES.addConstr(dummy_MC_ed[i] >= state_Y_nl[rd][j + 4 * i])
        else:
            Build_mixcolumn(state_Y_nl, rd, state_Y_l, rd + 1)
        # SR
        AES.addConstrs(state_Y_l[rd][SR[i]] == state_Y_nl[rd][i] for i in range(16))

    # VAR Z
    for rd in range(1, r_dist):
        state_Z[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_Z_" + str(rd))
        for i in range(16):
            AES.addGenConstrAnd(state_Z[rd][i], [state_X_l[rd][i], state_Y_l[rd][i]])
            # Add to Deg
            Deg.add(state_Z[rd][i])

    # Non trival
    AES.addConstr(quicksum(state_X_nl[0][i] for i in range(16)) >= 1)
    AES.addConstr(quicksum(state_Y_l[r_dist][i] for i in range(16)) >= 1)


# Online phase
def Build_key_recovery(r_in, r_dist, r_out):
    # VAR M - backward determination
    state_M_nl[r_in] = AES.addVars(16, vtype=GRB.BINARY, name="state_M_nl_" + str(r_in))
    state_M_l[r_in] = AES.addVars(16, vtype=GRB.BINARY, name="state_M_l_" + str(r_in))
    AES.addConstrs(state_M_nl[r_in][i] == state_X_nl[0][i] for i in range(16))
    # SR
    AES.addConstrs(state_M_l[r_in][SR[i]] == state_M_nl[r_in][i] for i in range(16))
    for rd in range(r_in - 1, -1, -1):
        state_M_nl[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_M_nl_" + str(rd))
        state_M_l[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_M_l_" + str(rd))
        # MC
        Build_mixcolumn(state_M_nl, rd, state_M_l, rd + 1)
        # SR
        AES.addConstrs(state_M_l[rd][SR[i]] == state_M_nl[rd][i] for i in range(16))
    for i in range(16):
        Data.add(state_M_l[0][i])

    # VAR W - forward determination
    state_W_l[0] = AES.addVars(16, vtype=GRB.BINARY, name="state_W_l_0")
    AES.addConstrs(state_W_l[0][i] == state_Y_l[r_dist][i] for i in range(16))
    for rd in range(r_out):
        state_W_nl[rd] = AES.addVars(16, vtype=GRB.BINARY, name="state_W_nl_" + str(rd))
        state_W_l[rd + 1] = AES.addVars(
            16, vtype=GRB.BINARY, name="state_W_l_" + str(rd + 1)
        )
        # SR
        AES.addConstrs(state_W_l[rd][SR[i]] == state_W_nl[rd][i] for i in range(16))
        # MC
        # if rd < r_out - 1:
        Build_mixcolumn(state_W_l, rd + 1, state_W_nl, rd)
        # else:
        #     AES.addConstrs(state_W_l[rd + 1][i] == state_W_nl[rd][i] for i in range(16))

    # for rd in range(r_in + 1):
    #     # Multiset method -> r_in
    #     # Sequence method -> r_in + 1
    #     for i in range(16):
    #         Key.add(state_M_l[rd][i])

    # for rd in range(r_out):
    #     for i in range(16):
    #         Key.add(state_W_nl[rd][i])


def calc(x, y):
    return 4 * x + y


def Get_idx_k(m, x, y, typ):
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


def Get_idx_u(m, x, y, typ):
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


def Build_key_bridging(r_in, r_dist, r_out):
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
            idx = 4 * (rd + r_in + 1) + i
            AES.addConstrs(involved_k[idx][j] == 0 for j in range(4))
            AES.addConstrs(involved_u[idx][j] == 0 for j in range(4))

    # Last round: MC omit - k; MC exsit - u
    for rd in range(r_out):
        for i in range(4):
            idx = 4 * (rd + r_in + r_dist + 1) + i
            # if rd == r_out - 1:
            #     AES.addConstrs(
            #         involved_k[idx][j] == state_W_nl[rd][4 * i + j] for j in range(4)
            #     )
            #     AES.addConstrs(involved_u[idx][j] == 0 for j in range(4))
            # else:
            AES.addConstrs(involved_k[idx][j] == 0 for j in range(4))
            AES.addConstrs(
                involved_u[idx][j] == state_W_nl[rd][4 * i + j] for j in range(4)
            )

    beta = 1  # How many steps need to deduce a variable at most
    n = 16 * (r_in + r_dist + r_out + 1)
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
                a, b = Get_idx_k(m, col, row, k)
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
                <= kb_state_k[i][j]
                + quicksum(kb_path_k[i + 1][j][k] for k in range(10))
            )

        kb_state_u[i + 1] = AES.addVars(
            n, vtype=GRB.BINARY, name="kb_state_u_" + str(i + 1)
        )
        kb_path_u[i + 1] = {}
        for j in range(n):  # For each variable in u
            kb_path_u[i + 1][j] = AES.addVars(
                7, vtype=GRB.BINARY, name="kb_path_u_" + str(i + 1) + "_" + str(j)
            )
            col = j >> 2
            row = j % 4
            # For 7 relation
            # len = 4 does not suit for u
            for k in range(6):
                a, b = Get_idx_u(m, col, row, k)
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
            AES.addConstrs(
                kb_state_u[i + 1][j] >= kb_path_u[i + 1][j][k] for k in range(7)
            )
            AES.addConstr(
                kb_state_u[i + 1][j]
                <= kb_state_u[i][j] + quicksum(kb_path_u[i + 1][j][k] for k in range(7))
            )

    for i in range(m):
        AES.addConstrs(
            kb_state_k[beta][4 * i + j] >= involved_k[i][j] for j in range(4)
        )
        AES.addConstrs(
            kb_state_u[beta][4 * i + j] >= involved_u[i][j] for j in range(4)
        )
    Key.add(
        quicksum(kb_state_k[0][i] for i in range(n))
        + quicksum(kb_state_u[0][i] for i in range(n))
    )


# Objective function
def Set_objective():
    # 1 represents the complexity of enumerating the delta-set
    AES.addConstr(Key <= 15)
    AES.addConstr(Obj >= Deg)
    AES.addConstr(Obj >= Key)
    AES.setObjective(Obj, GRB.MINIMIZE)


def Print_var(rd, var):
    for i in range(4):
        print(
            round(var[rd][i].Xn),
            round(var[rd][i + 4].Xn),
            round(var[rd][i + 8].Xn),
            round(var[rd][i + 12].Xn),
        )


def Print_variable_Z(r_dist):
    print("---------- Var Z ----------")
    for rd in range(1, r_dist):
        print("Z[", rd, "]")
        Print_var(rd, state_Z)


def Print_variable_X(r_dist):
    print("---------- Var X ----------")
    for rd in range(r_dist):
        if rd > 0:
            print("X_linear[", rd, "]")
            Print_var(rd, state_X_l)
            print("-- (ARK, SB, SR) ->")
        print("X_non_linear[", rd, "]")
        Print_var(rd, state_X_nl)
        if rd < r_dist - 1:
            print("-- (MC) ->")


def Print_variable_Y(r_dist):
    print("---------- Var Y ----------")
    for rd in range(1, r_dist + 1):
        print("Y_linear[", rd, "]")
        Print_var(rd, state_Y_l)
        if rd < r_dist:
            print("-- (ARK, SB, SR) ->")
            print("Y_non_linear[", rd, "]")
            Print_var(rd, state_Y_nl)
            print("-- (MC) ->")


def Print_variable_M(r_in):
    print("---------- Var M ----------")
    for rd in range(r_in + 1):
        print("M_linear[", rd, "]")
        Print_var(rd, state_M_l)
        print("-- (ARK, SB, SR) ->")
        print("M_non_linear[", rd, "]")
        Print_var(rd, state_M_nl)
        if rd < r_in:
            print("-- (MC) ->")


def Print_variable_W(r_dist, r_out):
    print("---------- Var W ----------")
    for rd in range(r_out + 1):
        print("W_linear[", rd + r_dist + r_in, "]")
        Print_var(rd, state_W_l)
        if rd < r_out:
            print("-- (ARK, SB, SR) ->")
            print("W_non_linear[", rd + r_dist + r_in, "]")
            Print_var(rd, state_W_nl)
            print("-- (MC) ->")


def Start_solver(r_in, r_dist, r_out):
    # AES.setParam("OutputFlag", 0)
    AES.Params.PoolSearchMode = 2
    AES.Params.PoolSolutions = 1  # Number of sols
    AES.Params.PoolGap = 2.0
    AES.Params.Threads = 128
    AES.Params.TimeLimit = 100
    # AES.setParam("IntFeasTol", 1e-9)
    AES.optimize()
    print("Model Status:", AES.Status)
    if AES.Status == 2 or AES.Status == 9:
        print("Min_Obj: %g" % AES.ObjVal)

        # All solutions
        for k in range(AES.SolCount):
            AES.Params.SolutionNumber = k
            print(
                "******** Sol no.{}    Obj = {}    Deg = {}    Key = {}    Data = {} ********".format(
                    k + 1,
                    round(Obj.Xn),
                    round(Evaluate_expr(Deg)),
                    round(Evaluate_expr(Key)),
                    round(Evaluate_expr(Data)),
                )
            )
            strr = "A = [ "
            for i in range(16):
                if round(state_Z[1][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]    B = [ "
            for i in range(16):
                if round(state_Z[r_dist - 1][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]"
            print(strr)

            Print_variable_Z(r_dist)
            Print_variable_X(r_dist)
            Print_variable_Y(r_dist)

            Print_variable_M(r_in)
            Print_variable_W(r_dist, r_out)
            print("---------- Involved k ----------")
            for i in range(r_in + r_dist + r_out + 1):
                print("Round[", i, "]")
                for j in range(4):
                    print(
                        round(involved_k[4 * i][j].Xn),
                        round(involved_k[4 * i + 1][j].Xn),
                        round(involved_k[4 * i + 2][j].Xn),
                        round(involved_k[4 * i + 3][j].Xn),
                    )
            print("---------- Involved u ----------")
            for i in range(r_in + r_dist + r_out + 1):
                print("Round[", i, "]")
                for j in range(4):
                    print(
                        round(involved_u[4 * i][j].Xn),
                        round(involved_u[4 * i + 1][j].Xn),
                        round(involved_u[4 * i + 2][j].Xn),
                        round(involved_u[4 * i + 3][j].Xn),
                    )

            print("---------- Initial k ----------")
            for i in range(r_in + r_dist + r_out + 1):
                print("Round[", i, "]")
                for j in range(4):
                    print(
                        round(kb_state_k[0][16 * i + j].Xn),
                        round(kb_state_k[0][16 * i + 4 + j].Xn),
                        round(kb_state_k[0][16 * i + 8 + j].Xn),
                        round(kb_state_k[0][16 * i + 12 + j].Xn),
                    )

            print("---------- Initial u ----------")
            for i in range(r_in + r_dist + r_out + 1):
                print("Round[", i, "]")
                for j in range(4):
                    print(
                        round(kb_state_u[0][16 * i + j].Xn),
                        round(kb_state_u[0][16 * i + 4 + j].Xn),
                        round(kb_state_u[0][16 * i + 8 + j].Xn),
                        round(kb_state_u[0][16 * i + 12 + j].Xn),
                    )


if __name__ == "__main__":
    r_dist = 4
    r_in = 1
    r_out = 2
    Build_distinguisher(r_dist)
    Build_key_recovery(r_in, r_dist, r_out)
    Build_key_bridging(r_in, r_dist, r_out)
    Set_objective()
    Start_solver(r_in, r_dist, r_out)
