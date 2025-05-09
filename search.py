from gurobipy import *
import time
import sys


SR = [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]
PT = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]


def Evaluate_objective(model):
    expr = model.getObjective()
    val = 0
    for i in range(expr.size()):
        coeff = expr.getCoeff(i)
        var = expr.getVar(i)
        val += coeff * round(var.Xn)
    return val


def Search_ds_mitm_attacks(r_dist, r_in, r_out):
    SKINNY = Model("SKINNY")
    state_X_l = {}  # VAR X
    state_X_nl = {}
    state_Y_l = {}  # VAR Y
    state_Y_nl = {}
    state_Z = {}  # VAR Z
    con_1 = {}  # cipher-specific constraints
    con_2 = {}
    Deg = LinExpr()
    Con = LinExpr()
    Key = LinExpr()
    Obj = SKINNY.addVar(vtype=GRB.INTEGER, name="Obj")
    state_W_l = {}  # VAR W
    state_W_nl = {}
    state_M_l = {}  # VAR M
    state_M_nl = {}
    state_O_l = {}  # VAR O
    state_O_nl = {}
    Rou = {}

    # VAR X - forward differential
    state_X_l[0] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_X_l_0")
    for rd in range(r_dist):
        state_X_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_X_nl_" + str(rd)
        )
        state_X_l[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_X_l_" + str(rd + 1)
        )
        # SR
        SKINNY.addConstrs(state_X_nl[rd][i] == state_X_l[rd][SR[i]] for i in range(16))
        # MC - COL1
        SKINNY.addConstrs(state_X_l[rd + 1][i] >= state_X_nl[rd][i] for i in range(4))
        SKINNY.addConstrs(
            state_X_l[rd + 1][i] >= state_X_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i] >= state_X_nl[rd][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i]
            <= state_X_nl[rd][i] + state_X_nl[rd][i + 8] + state_X_nl[rd][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 4] == state_X_nl[rd][i] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 8] >= state_X_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 8] >= state_X_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 8] <= state_X_nl[rd][i + 4] + state_X_nl[rd][i + 8]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 12] >= state_X_nl[rd][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 12] >= state_X_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_X_l[rd + 1][i + 12] <= state_X_nl[rd][i] + state_X_nl[rd][i + 8]
            for i in range(4)
        )

    # VAR Y - backward determination
    state_Y_l[r_dist] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_Y_l_" + str(r_dist)
    )
    for rd in range(r_dist - 1, -1, -1):
        state_Y_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_Y_nl_" + str(rd)
        )
        state_Y_l[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_Y_l_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(state_Y_nl[rd][i] >= state_Y_l[rd + 1][i] for i in range(4))
        SKINNY.addConstrs(
            state_Y_nl[rd][i] >= state_Y_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_Y_nl[rd][i] >= state_Y_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_Y_nl[rd][i]
            <= state_Y_l[rd + 1][i]
            + state_Y_l[rd + 1][i + 4]
            + state_Y_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 4] == state_Y_l[rd + 1][i + 8] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 8] >= state_Y_l[rd + 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 8] >= state_Y_l[rd + 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 8] >= state_Y_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 8]
            <= state_Y_l[rd + 1][i]
            + state_Y_l[rd + 1][i + 8]
            + state_Y_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_Y_nl[rd][i + 12] == state_Y_l[rd + 1][i] for i in range(4)
        )
        # SR
        SKINNY.addConstrs(state_Y_l[rd][SR[i]] == state_Y_nl[rd][i] for i in range(16))

    # VAR Z
    for rd in range(r_dist + 1):
        state_Z[rd] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_Z_" + str(rd))
        SKINNY.addConstrs(state_Z[rd][i] <= state_X_l[rd][i] for i in range(16))
        SKINNY.addConstrs(state_Z[rd][i] <= state_Y_l[rd][i] for i in range(16))
        SKINNY.addConstrs(
            state_X_l[rd][i] + state_Y_l[rd][i] - state_Z[rd][i] <= 1 for i in range(16)
        )
        if rd < r_dist and rd > 0:
            for i in range(16):
                Deg.add(state_Z[rd][i])

    # Non trival
    SKINNY.addConstr(quicksum(state_X_l[0][i] for i in range(16)) >= 1)
    SKINNY.addConstr(quicksum(state_Y_l[r_dist][i] for i in range(16)) >= 1)

    # Specific condition
    for rd in range(r_dist):
        con_1[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_1_" + str(rd))
        con_2[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_2_" + str(rd))
        for i in range(4):
            SKINNY.addConstr(
                state_Z[rd + 1][i + 4]
                + state_Z[rd + 1][i + 12]
                + state_Z[rd][SR[i + 8]]
                >= 3 * con_1[rd][i]
            )
            SKINNY.addConstr(
                state_Z[rd + 1][i + 4]
                + state_Z[rd + 1][i + 12]
                + state_Z[rd][SR[i + 8]]
                <= 2 + con_1[rd][i]
            )
            SKINNY.addConstr(
                state_Z[rd + 1][i] + state_Z[rd + 1][i + 12] + state_Z[rd][SR[i + 12]]
                >= 3 * con_2[rd][i]
            )
            SKINNY.addConstr(
                state_Z[rd + 1][i] + state_Z[rd + 1][i + 12] + state_Z[rd][SR[i + 12]]
                <= 2 + con_2[rd][i]
            )
            Con.add(con_1[rd][i])
            Con.add(con_2[rd][i])

    # VAR W - forward determination
    state_W_l[0] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_W_l_0")
    SKINNY.addConstrs(state_W_l[0][i] == state_Z[r_dist][i] for i in range(16))
    for rd in range(r_out):
        state_W_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_W_nl_" + str(rd)
        )
        state_W_l[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_W_l_" + str(rd + 1)
        )
        # SR
        SKINNY.addConstrs(state_W_l[rd][SR[i]] == state_W_nl[rd][i] for i in range(16))
        # MC - COL1
        SKINNY.addConstrs(
            state_W_l[rd + 1][i] == state_W_nl[rd][i + 12] for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 4] >= state_W_nl[rd][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 4] >= state_W_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 4] >= state_W_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 4]
            <= state_W_nl[rd][i] + state_W_nl[rd][i + 4] + state_W_nl[rd][i + 8]
            for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 8] == state_W_nl[rd][i + 4] for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 12] >= state_W_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 12] >= state_W_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 12] >= state_W_nl[rd][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_W_l[rd + 1][i + 12]
            <= state_W_nl[rd][i + 4] + state_W_nl[rd][i + 8] + state_W_nl[rd][i + 12]
            for i in range(4)
        )

    # VAR M - backward differential
    state_M_l[r_in] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_W_l_" + str(r_in)
    )
    SKINNY.addConstrs(state_M_l[r_in][i] == state_Z[0][i] for i in range(16))
    for rd in range(r_in - 1, -1, -1):
        state_M_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_M_nl_" + str(rd)
        )
        state_M_l[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_M_l_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(
            state_M_nl[rd][i] == state_M_l[rd + 1][i + 4] for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_M_nl[rd][i + 4] >= state_M_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 4] >= state_M_l[rd + 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 4] >= state_M_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 4]
            <= state_M_l[rd + 1][i + 4]
            + state_M_l[rd + 1][i + 8]
            + state_M_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_M_nl[rd][i + 8] >= state_M_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 8] >= state_M_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 8]
            <= state_M_l[rd + 1][i + 4] + state_M_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_M_nl[rd][i + 12] >= state_M_l[rd + 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 12] >= state_M_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_M_nl[rd][i + 12] <= state_M_l[rd + 1][i] + state_M_l[rd + 1][i + 12]
            for i in range(4)
        )
        # SR
        SKINNY.addConstrs(state_M_l[rd][SR[i]] == state_M_nl[rd][i] for i in range(16))

    # VAR O - backward determination
    state_O_l[r_in - 1] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_O_l_" + str(r_in - 1)
    )
    SKINNY.addConstrs(
        state_O_l[r_in - 1][i] == state_M_l[r_in - 1][i] for i in range(16)
    )
    for rd in range(r_in - 2, -1, -1):
        state_O_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_O_nl_" + str(rd)
        )
        state_O_l[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_O_l_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(state_O_nl[rd][i] >= state_O_l[rd + 1][i] for i in range(4))
        SKINNY.addConstrs(
            state_O_nl[rd][i] >= state_O_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_O_nl[rd][i] >= state_O_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_O_nl[rd][i]
            <= state_O_l[rd + 1][i]
            + state_O_l[rd + 1][i + 4]
            + state_O_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_O_nl[rd][i + 4] == state_O_l[rd + 1][i + 8] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_O_nl[rd][i + 8] >= state_O_l[rd + 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_O_nl[rd][i + 8] >= state_O_l[rd + 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_O_nl[rd][i + 8] >= state_O_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_O_nl[rd][i + 8]
            <= state_O_l[rd + 1][i]
            + state_O_l[rd + 1][i + 8]
            + state_O_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_O_nl[rd][i + 12] == state_O_l[rd + 1][i] for i in range(4)
        )
        # SR & VAR M
        SKINNY.addConstrs(state_O_l[rd][i] >= state_M_l[rd][i] for i in range(16))
        SKINNY.addConstrs(state_O_l[rd][SR[i]] >= state_O_nl[rd][i] for i in range(16))
        SKINNY.addConstrs(
            state_O_l[rd][SR[i]] <= state_M_l[rd][SR[i]] + state_O_nl[rd][i]
            for i in range(16)
        )

    # Key-Bridging

    for i in range(16):
        Rou[i] = LinExpr()

    tmp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for rd in range(r_in + r_dist + r_out):
        if rd < r_in - 1:
            for i in range(8):
                Rou[tmp[SR[i]]].add(state_O_nl[rd][i])
        if rd > r_in + r_dist:
            for i in range(8):
                Rou[tmp[i]].add(state_W_l[rd - r_in - r_dist][i])
        for i in range(16):
            tmp[i] = PT[tmp[i]]

    # SKINNY.update()
    # for i in range(16):
    #     print(Rou[i])

    alpha = SKINNY.addVars(16, vtype=GRB.BINARY, name="alpha")
    beta = SKINNY.addVars(16, vtype=GRB.BINARY, name="beta")
    gamma = SKINNY.addVars(16, vtype=GRB.BINARY, name="gamma")
    for i in range(16):
        SKINNY.addGenConstrIndicator(alpha[i], 1, Rou[i] >= 3)
        SKINNY.addGenConstrIndicator(alpha[i], 0, Rou[i] <= 2)
        SKINNY.addGenConstrIndicator(beta[i], 1, Rou[i] >= 2)
        SKINNY.addGenConstrIndicator(beta[i], 0, Rou[i] <= 1)
        SKINNY.addGenConstrIndicator(gamma[i], 1, Rou[i] >= 1)
        SKINNY.addGenConstrIndicator(gamma[i], 0, Rou[i] == 0)
        Key.add(alpha[i])
        Key.add(beta[i])
        Key.add(gamma[i])

    SKINNY.addConstr(Obj >= Deg - Con)
    SKINNY.addConstr(Obj >= Key)

    # Reasonable
    SKINNY.addConstr(Obj <= 48)

    # Objective function
    # SKINNY.addConstr(state_Z[0][14] == 1)  # To be deleted!!!
    SKINNY.setObjective(Obj, GRB.MINIMIZE)

    # Start solver
    # SKINNY.setParam("OutputFlag", 0)
    SKINNY.Params.PoolSearchMode = 2
    SKINNY.Params.PoolSolutions = 3  # 84 sols
    SKINNY.Params.PoolGap = 3.0
    # SKINNY.setParam("IntFeasTol", 1e-9)
    SKINNY.optimize()
    print("Model Status:", SKINNY.Status)
    if SKINNY.Status == 2:
        print("Min_Obj: %g" % SKINNY.ObjVal)

        # All solutions
        for k in range(SKINNY.SolCount):
            SKINNY.Params.SolutionNumber = k
            print(
                "************ Sol no.{}    Deg = {} ************".format(
                    k + 1, Evaluate_objective(SKINNY)
                )
            )
            strr = "A = [ "
            for i in range(16):
                if round(state_Z[0][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]    B = [ "
            for i in range(16):
                if round(state_Z[r_dist][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]"
            print(strr)

            # print("---------- Var X ----------")
            # for rd in range(r_dist + 1):
            #     print("X_linear[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_X_l[rd][4 * i].Xn),
            #             round(state_X_l[rd][4 * i + 1].Xn),
            #             round(state_X_l[rd][4 * i + 2].Xn),
            #             round(state_X_l[rd][4 * i + 3].Xn),
            #         )
            #     if rd < r_dist:
            #         print("X_non_linear[", rd, "]")
            #         for i in range(4):
            #             print(
            #                 round(state_X_nl[rd][4 * i].Xn),
            #                 round(state_X_nl[rd][4 * i + 1].Xn),
            #                 round(state_X_nl[rd][4 * i + 2].Xn),
            #                 round(state_X_nl[rd][4 * i + 3].Xn),
            #             )

            # print("---------- Var Y ----------")
            # for rd in range(r_dist + 1):
            #     print("Y_linear[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_Y_l[rd][4 * i].Xn),
            #             round(state_Y_l[rd][4 * i + 1].Xn),
            #             round(state_Y_l[rd][4 * i + 2].Xn),
            #             round(state_Y_l[rd][4 * i + 3].Xn),
            #         )
            #     if rd < r_dist:
            #         print("Y_non_linear[", rd, "]")
            #         for i in range(4):
            #             print(
            #                 round(state_Y_nl[rd][4 * i].Xn),
            #                 round(state_Y_nl[rd][4 * i + 1].Xn),
            #                 round(state_Y_nl[rd][4 * i + 2].Xn),
            #                 round(state_Y_nl[rd][4 * i + 3].Xn),
            #             )

            # print("---------- Var Z ----------")
            # for rd in range(r_dist + 1):
            #     print("Z[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_Z[rd][4 * i].Xn),
            #             round(state_Z[rd][4 * i + 1].Xn),
            #             round(state_Z[rd][4 * i + 2].Xn),
            #             round(state_Z[rd][4 * i + 3].Xn),
            #         )

            # print("---------- Con ----------")
            # for rd in range(r_dist):
            #     print(
            #         "con_1[",
            #         rd,
            #         "] :",
            #         round(con_1[rd][0].Xn),
            #         round(con_1[rd][1].Xn),
            #         round(con_1[rd][2].Xn),
            #         round(con_1[rd][3].Xn),
            #     )
            #     print(
            #         "con_2[",
            #         rd,
            #         "] :",
            #         round(con_2[rd][0].Xn),
            #         round(con_2[rd][1].Xn),
            #         round(con_2[rd][2].Xn),
            #         round(con_2[rd][3].Xn),
            #     )

            # print("---------- Var O ----------")
            # for rd in range(r_in):
            #     print("O_linear[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_O_l[rd][4 * i].Xn),
            #             round(state_O_l[rd][4 * i + 1].Xn),
            #             round(state_O_l[rd][4 * i + 2].Xn),
            #             round(state_O_l[rd][4 * i + 3].Xn),
            #         )
            #     if rd < r_in - 1:
            #         print("O_non_linear[", rd, "]")
            #         for i in range(4):
            #             print(
            #                 round(state_O_nl[rd][4 * i].Xn),
            #                 round(state_O_nl[rd][4 * i + 1].Xn),
            #                 round(state_O_nl[rd][4 * i + 2].Xn),
            #                 round(state_O_nl[rd][4 * i + 3].Xn),
            #             )

            # print("---------- Var W ----------")
            # for rd in range(r_out + 1):
            #     print("W_linear[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_W_l[rd][4 * i].Xn),
            #             round(state_W_l[rd][4 * i + 1].Xn),
            #             round(state_W_l[rd][4 * i + 2].Xn),
            #             round(state_W_l[rd][4 * i + 3].Xn),
            #         )
            #     if rd < r_out:
            #         print("W_non_linear[", rd, "]")
            #         for i in range(4):
            #             print(
            #                 round(state_W_nl[rd][4 * i].Xn),
            #                 round(state_W_nl[rd][4 * i + 1].Xn),
            #                 round(state_W_nl[rd][4 * i + 2].Xn),
            #                 round(state_W_nl[rd][4 * i + 3].Xn),
            #             )

            # print("---------- Var M ----------")
            # for rd in range(r_in + 1):
            #     print("M_linear[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_M_l[rd][4 * i].Xn),
            #             round(state_M_l[rd][4 * i + 1].Xn),
            #             round(state_M_l[rd][4 * i + 2].Xn),
            #             round(state_M_l[rd][4 * i + 3].Xn),
            #         )
            #     if rd < r_in:
            #         print("M_non_linear[", rd, "]")
            #         for i in range(4):
            #             print(
            #                 round(state_M_nl[rd][4 * i].Xn),
            #                 round(state_M_nl[rd][4 * i + 1].Xn),
            #                 round(state_M_nl[rd][4 * i + 2].Xn),
            #                 round(state_M_nl[rd][4 * i + 3].Xn),
            #             )


if __name__ == "__main__":
    Search_ds_mitm_attacks(10, 3, 9)
