# Key-dependent-sieve
# Differential enumeration

from gurobipy import *

PosPerm = [
    0,
    25,
    18,
    15,
    4,
    1,
    30,
    19,
    8,
    29,
    22,
    7,
    12,
    9,
    26,
    23,
    20,
    5,
    10,
    31,
    16,
    13,
    2,
    27,
    28,
    17,
    6,
    3,
    24,
    21,
    14,
    11,
]

PK = [
    8,
    24,
    28,
    23,
    9,
    31,
    14,
    17,
    20,
    19,
    26,
    5,
    18,
    2,
    6,
    30,
    4,
    15,
    11,
    25,
    10,
    29,
    12,
    3,
    21,
    16,
    7,
    0,
    27,
    13,
    22,
    1,
]

uLBC = Model("uLBC")
# l -(AddRoundKey, SubNib, PosPerm)-> nl -(MixColumn)-> l
state_X_l = {}  # VAR X: parameters
state_X_nl = {}
state_Y_l = {}  # VAR Y: parameters
state_Y_nl = {}
state_Z = {}  # VAR Z: parameters
state_W_l = {}  # VAR W
state_W_nl = {}
state_M_l = {}  # VAR M
state_M_nl = {}
key_bri = {}
Deg = LinExpr()
Key = LinExpr()
Data = LinExpr()
Obj = uLBC.addVar(vtype=GRB.INTEGER, name="Obj")


def Evaluate_expr(le):
    val = 0
    for i in range(le.size()):
        coeff = le.getCoeff(i)
        var = le.getVar(i)
        val += coeff * round(var.Xn)
    return val


def Build_mixcolumn(var1, r1, var2, r2):
    for i in range(8):
        # 0
        uLBC.addConstr(
            var1[r1][4 * i]
            <= var2[r2][4 * i + 1] + var2[r2][4 * i + 2] + var2[r2][4 * i + 3]
        )
        uLBC.addConstr(var1[r1][4 * i] >= var2[r2][4 * i + 1])
        uLBC.addConstr(var1[r1][4 * i] >= var2[r2][4 * i + 2])
        uLBC.addConstr(var1[r1][4 * i] >= var2[r2][4 * i + 3])
        # 1
        uLBC.addConstr(
            var1[r1][4 * i + 1]
            <= var2[r2][4 * i] + var2[r2][4 * i + 2] + var2[r2][4 * i + 3]
        )
        uLBC.addConstr(var1[r1][4 * i + 1] >= var2[r2][4 * i])
        uLBC.addConstr(var1[r1][4 * i + 1] >= var2[r2][4 * i + 2])
        uLBC.addConstr(var1[r1][4 * i + 1] >= var2[r2][4 * i + 3])
        # 2
        uLBC.addConstr(
            var1[r1][4 * i + 2]
            <= var2[r2][4 * i] + var2[r2][4 * i + 1] + var2[r2][4 * i + 3]
        )
        uLBC.addConstr(var1[r1][4 * i + 2] >= var2[r2][4 * i])
        uLBC.addConstr(var1[r1][4 * i + 2] >= var2[r2][4 * i + 1])
        uLBC.addConstr(var1[r1][4 * i + 2] >= var2[r2][4 * i + 3])
        # 3
        uLBC.addConstr(
            var1[r1][4 * i + 3]
            <= var2[r2][4 * i] + var2[r2][4 * i + 1] + var2[r2][4 * i + 2]
        )
        uLBC.addConstr(var1[r1][4 * i + 3] >= var2[r2][4 * i])
        uLBC.addConstr(var1[r1][4 * i + 3] >= var2[r2][4 * i + 1])
        uLBC.addConstr(var1[r1][4 * i + 3] >= var2[r2][4 * i + 2])


# Offline phase
def Build_distinguisher(r_dist):
    # VAR X - forward differential
    state_X_nl[0] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_X_nl_0")
    for rd in range(1, r_dist):
        state_X_l[rd] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_X_l_" + str(rd))
        state_X_nl[rd] = uLBC.addVars(
            32, vtype=GRB.BINARY, name="state_X_nl_" + str(rd)
        )
        # MixColumn
        if rd == 1:  # GDS-MITM
            dummy_MC_st_allzero = uLBC.addVars(
                8, vtype=GRB.BINARY, name="dummy_MC_st_allzero"
            )
            dummy_MC_st_equal = uLBC.addVars(
                8, vtype=GRB.BINARY, name="dummy_MC_st_equal"
            )
            for i in range(8):
                lsum = LinExpr()
                rsum = LinExpr()
                lsum = quicksum(state_X_nl[rd - 1][j + 4 * i] for j in range(4))
                rsum = quicksum(state_X_l[rd][j + 4 * i] for j in range(4))
                uLBC.addConstr(lsum + rsum == 4 * dummy_MC_st_allzero[i])
                uLBC.addConstr(lsum <= 3)
                uLBC.addConstr(rsum <= 3)
                for j in range(4):
                    uLBC.addConstr(
                        state_X_l[rd][j + 4 * i] - state_X_nl[rd - 1][j + 4 * i]
                        <= dummy_MC_st_equal[i]
                    )
                    uLBC.addConstr(
                        state_X_nl[rd - 1][j + 4 * i] - state_X_l[rd][j + 4 * i]
                        <= dummy_MC_st_equal[i]
                    )
                    uLBC.addConstr(
                        state_X_l[rd][j + 4 * i] + state_X_nl[rd - 1][j + 4 * i]
                        <= 2 - dummy_MC_st_equal[i]
                    )
                    uLBC.addConstr(
                        state_X_l[rd][j + 4 * i] + state_X_nl[rd - 1][j + 4 * i]
                        >= dummy_MC_st_equal[i]
                    )
        else:
            Build_mixcolumn(state_X_l, rd, state_X_nl, rd - 1)
        # PosPerm
        uLBC.addConstrs(
            state_X_nl[rd][i] == state_X_l[rd][PosPerm[i]] for i in range(32)
        )

    # VAR Y - backward determination
    state_Y_l[r_dist] = uLBC.addVars(
        32, vtype=GRB.BINARY, name="state_Y_l_" + str(r_dist)
    )
    for rd in range(r_dist - 1, 0, -1):
        state_Y_nl[rd] = uLBC.addVars(
            32, vtype=GRB.BINARY, name="state_Y_nl_" + str(rd)
        )
        state_Y_l[rd] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_Y_l_" + str(rd))
        # MC
        if rd == r_dist - 1:  # GDS-MITM
            dummy_MC_ed_allzero = uLBC.addVars(
                8, vtype=GRB.BINARY, name="dummy_MC_ed_allzero"
            )
            dummy_MC_ed_equal = uLBC.addVars(
                8, vtype=GRB.BINARY, name="dummy_MC_ed_equal"
            )
            for i in range(8):
                lsum = LinExpr()
                rsum = LinExpr()
                lsum = quicksum(state_Y_l[rd + 1][j + 4 * i] for j in range(4))
                rsum = quicksum(state_Y_nl[rd][j + 4 * i] for j in range(4))
                uLBC.addConstr(lsum + rsum == 4 * dummy_MC_ed_allzero[i])
                uLBC.addConstr(lsum <= 3)
                uLBC.addConstr(rsum <= 3)
                for j in range(4):
                    uLBC.addConstr(
                        state_Y_l[rd + 1][j + 4 * i] - state_Y_nl[rd][j + 4 * i]
                        <= dummy_MC_ed_equal[i]
                    )
                    uLBC.addConstr(
                        state_Y_nl[rd][j + 4 * i] - state_Y_l[rd + 1][j + 4 * i]
                        <= dummy_MC_ed_equal[i]
                    )
                    uLBC.addConstr(
                        state_Y_nl[rd][j + 4 * i] + state_Y_l[rd + 1][j + 4 * i]
                        <= 2 - dummy_MC_ed_equal[i]
                    )
                    uLBC.addConstr(
                        state_Y_nl[rd][j + 4 * i] + state_Y_l[rd + 1][j + 4 * i]
                        >= dummy_MC_ed_equal[i]
                    )
        else:
            Build_mixcolumn(state_Y_nl, rd, state_Y_l, rd + 1)
        # SR
        uLBC.addConstrs(
            state_Y_l[rd][PosPerm[i]] == state_Y_nl[rd][i] for i in range(32)
        )

    # VAR Z
    for rd in range(1, r_dist):
        state_Z[rd] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_Z_" + str(rd))
        for i in range(32):
            uLBC.addGenConstrAnd(state_Z[rd][i], [state_X_l[rd][i], state_Y_l[rd][i]])
            # Add to Deg
            Deg.add(state_Z[rd][i])

    # Non trival
    uLBC.addConstr(quicksum(state_X_nl[0][i] for i in range(32)) >= 1)
    uLBC.addConstr(quicksum(state_Y_l[r_dist][i] for i in range(32)) >= 1)


# Online phase
def Build_key_recovery(r_in, r_dist, r_out):
    # VAR M - backward determination
    state_M_nl[r_in] = uLBC.addVars(
        32, vtype=GRB.BINARY, name="state_M_nl_" + str(r_in)
    )
    state_M_l[r_in] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_M_l_" + str(r_in))
    uLBC.addConstrs(state_M_nl[r_in][i] == state_X_nl[0][i] for i in range(32))
    # PosPerm
    uLBC.addConstrs(
        state_M_l[r_in][PosPerm[i]] == state_M_nl[r_in][i] for i in range(32)
    )
    for rd in range(r_in - 1, -1, -1):
        state_M_nl[rd] = uLBC.addVars(
            32, vtype=GRB.BINARY, name="state_M_nl_" + str(rd)
        )
        state_M_l[rd] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_M_l_" + str(rd))
        # MixColumn
        Build_mixcolumn(state_M_nl, rd, state_M_l, rd + 1)
        # PosPerm
        uLBC.addConstrs(
            state_M_l[rd][PosPerm[i]] == state_M_nl[rd][i] for i in range(32)
        )
    for i in range(32):
        Data.add(state_M_l[0][i])

    # VAR W - forward determination
    state_W_l[0] = uLBC.addVars(32, vtype=GRB.BINARY, name="state_W_l_0")
    uLBC.addConstrs(state_W_l[0][i] == state_Y_l[r_dist][i] for i in range(32))
    for rd in range(r_out):
        state_W_nl[rd] = uLBC.addVars(
            32, vtype=GRB.BINARY, name="state_W_nl_" + str(rd)
        )
        state_W_l[rd + 1] = uLBC.addVars(
            32, vtype=GRB.BINARY, name="state_W_l_" + str(rd + 1)
        )
        # PosPerm
        uLBC.addConstrs(
            state_W_l[rd][PosPerm[i]] == state_W_nl[rd][i] for i in range(32)
        )
        # MC
        Build_mixcolumn(state_W_l, rd + 1, state_W_nl, rd)


# Key-bridging technique
def Build_key_bridging(r_in, r_dist, r_out):
    # for rd in range(r_in + 1):
    #     for i in range(32):
    #         Key.add(state_M_l[rd][i])

    # for rd in range(r_out):
    #     for i in range(32):
    #         Key.add(state_W_nl[rd][i])
    for i in range(32):
        key_bri[i] = LinExpr()
    tmp = list(range(32))
    # print(tmp)
    for rd in range(r_in + 1 + r_dist + r_out):
        if rd <= r_in:
            for i in range(32):
                key_bri[tmp[i]].add(state_M_l[rd][i])
        elif rd > r_in + r_dist:
            for i in range(32):
                key_bri[tmp[PosPerm[i]]].add(state_W_nl[rd - r_in - r_dist - 1][i])
        for i in range(32):
            tmp[i] = PK[tmp[i]]

    alpha = uLBC.addVars(32, vtype=GRB.BINARY, name="alpha")
    for i in range(32):
        uLBC.addGenConstrIndicator(alpha[i], 1, key_bri[i] >= 1)
        uLBC.addGenConstrIndicator(alpha[i], 0, key_bri[i] == 0)
        Key.add(alpha[i])


# Objective function
def Set_objective():
    uLBC.addConstr(Key <= 31)
    uLBC.addConstr(Obj >= Deg)
    uLBC.addConstr(Obj >= Key)
    uLBC.setObjective(Obj, GRB.MINIMIZE)


def Print_var(rd, var):
    for i in range(4):
        print(
            round(var[rd][i].Xn),
            round(var[rd][i + 4].Xn),
            round(var[rd][i + 8].Xn),
            round(var[rd][i + 12].Xn),
            round(var[rd][i + 16].Xn),
            round(var[rd][i + 20].Xn),
            round(var[rd][i + 24].Xn),
            round(var[rd][i + 28].Xn),
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
            print("-- (AddRoundKey, SubNib, PosPerm) ->")
        print("X_non_linear[", rd, "]")
        Print_var(rd, state_X_nl)
        if rd < r_dist - 1:
            print("-- (MixColumn) ->")


def Print_variable_Y(r_dist):
    print("---------- Var Y ----------")
    for rd in range(1, r_dist + 1):
        print("Y_linear[", rd, "]")
        Print_var(rd, state_Y_l)
        if rd < r_dist:
            print("-- (AddRoundKey, SubNib, PosPerm) ->")
            print("Y_non_linear[", rd, "]")
            Print_var(rd, state_Y_nl)
            print("-- (MixColumn) ->")


def Print_variable_M(r_in):
    print("---------- Var M ----------")
    for rd in range(r_in + 1):
        print("M_linear[", rd, "]")
        Print_var(rd, state_M_l)
        print("-- (AddRoundKey, SubNib, PosPerm) ->")
        print("M_non_linear[", rd, "]")
        Print_var(rd, state_M_nl)
        if rd < r_in:
            print("-- (MixColumn) ->")


def Print_variable_W(r_dist, r_out):
    print("---------- Var W ----------")
    for rd in range(r_out + 1):
        print("W_linear[", rd + r_dist + r_in, "]")
        Print_var(rd, state_W_l)
        if rd < r_out:
            print("-- (AddRoundKey, SubNib, PosPerm) ->")
            print("W_non_linear[", rd + r_dist + r_in, "]")
            Print_var(rd, state_W_nl)
            print("-- (MixColumn) ->")


def Start_solver(r_in, r_dist, r_out):
    # uLBC.setParam("OutputFlag", 0)
    uLBC.Params.PoolSearchMode = 2
    uLBC.Params.PoolSolutions = 1  # Number of sols
    uLBC.Params.PoolGap = 2.0
    uLBC.Params.Threads = 128
    # uLBC.Params.TimeLimit = 100
    # uLBC.setParam("IntFeasTol", 1e-9)
    uLBC.optimize()
    print("Model Status:", uLBC.Status)
    if uLBC.Status == 2 or uLBC.Status == 9:
        print("Min_Obj: %g" % uLBC.ObjVal)

        # All solutions
        for k in range(uLBC.SolCount):
            uLBC.Params.SolutionNumber = k
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
            for i in range(32):
                if round(state_Z[1][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]    B = [ "
            for i in range(32):
                if round(state_Z[r_dist - 1][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]"
            print(strr)

            Print_variable_Z(r_dist)
            Print_variable_X(r_dist)
            Print_variable_Y(r_dist)
            Print_variable_M(r_in)
            Print_variable_W(r_dist, r_out)
            print("---------- Key-Bridge ----------")
            strr = ""
            for i in range(32):
                strr += str(round(Evaluate_expr(key_bri[i]))) + " "
            print(strr)


if __name__ == "__main__":
    r_dist = 7
    r_in = 2
    r_out = 4
    Build_distinguisher(r_dist)
    Build_key_recovery(r_in, r_dist, r_out)
    Build_key_bridging(r_in, r_dist, r_out)
    Set_objective()
    Start_solver(r_in, r_dist, r_out)
