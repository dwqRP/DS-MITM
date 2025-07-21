from gurobipy import *
import time
import sys


SR = [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]
PT = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]


def Evaluate_expr(le):
    val = 0
    for i in range(le.size()):
        coeff = le.getCoeff(i)
        var = le.getVar(i)
        val += coeff * round(var.Xn)
    return val


def Search_ds_distinguishers_td(r_dist, r_mid, r_in, r_out):
    SKINNY = Model("SKINNY")
    # l -(SB,AK,SR)-> nl -(MC)-> l
    state_X_l = {}  # VAR X: parameters
    state_X_nl = {}
    state_Y_l = {}  # VAR Y: parameters
    state_Y_nl = {}
    state_Z = {}  # VAR Z: parameters

    state_T_l = {}  # VAR for truncated differential
    state_T_nl = {}
    state_GT_l = {}  # VAR for differential enumeration
    state_GT_nl = {}
    dummy_GT = {}  # dummy for VAR GT
    state_GZ = {}
    state_GU = {}  # union of Z and GT

    con_1 = {}  # cipher-specific constraints (non-full key addition)
    con_2 = {}
    con_3 = {}
    con_4 = {}

    state_V_sb = {}  # VAR V: key-dependent-seive
    state_V = {}
    dummy_V = {}  # dummy for VAR V
    key_V = {}  # key for VAR V
    key_dep = {}

    state_M_l = {}  # VAR M: Kin - differential
    state_M_nl = {}
    state_O_l = {}  # VAR O: Kin - determination
    state_O_nl = {}
    state_W_l = {}  # VAR W: Kout of MITM
    state_W_nl = {}
    state_E_l = {}  # VAR E: Kout of TD - differential
    state_E_nl = {}
    state_F_l = {}  # VAR F: Kout of TD - determination
    state_F_nl = {}
    key_out = {}  # Kout: W and F together
    key_bri = {}

    Deg = LinExpr()  # number of active VAR Z
    Con = LinExpr()  # number can be saved by non-full key addition
    Key_sieve = LinExpr()  # number can be saved by key-dependent-seive
    Start = LinExpr()  # number of active Z[r=0]
    Key = LinExpr()
    Data = LinExpr()
    Obj = SKINNY.addVar(vtype=GRB.INTEGER, name="Obj")

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

    for i in range(16):
        Start.add(state_Z[0][i])

    # Non trival
    SKINNY.addConstr(quicksum(state_X_l[0][i] for i in range(16)) >= 1)
    SKINNY.addConstr(quicksum(state_Y_l[r_dist][i] for i in range(16)) >= 1)

    # VAR T - truncated differential
    state_T_l[0] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_T_l_0")
    SKINNY.addConstrs(state_T_l[0][i] == state_Z[0][i] for i in range(16))
    for rd in range(r_mid):
        state_T_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_T_nl_" + str(rd)
        )
        state_T_l[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_T_l_" + str(rd + 1)
        )
        # SR
        SKINNY.addConstrs(state_T_nl[rd][i] == state_T_l[rd][SR[i]] for i in range(16))
        # MC - COL1
        SKINNY.addConstrs(state_T_l[rd + 1][i] >= state_T_nl[rd][i] for i in range(4))
        SKINNY.addConstrs(
            state_T_l[rd + 1][i] >= state_T_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i] >= state_T_nl[rd][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i]
            <= state_T_nl[rd][i] + state_T_nl[rd][i + 8] + state_T_nl[rd][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 4] == state_T_nl[rd][i] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 8] >= state_T_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 8] >= state_T_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 8] <= state_T_nl[rd][i + 4] + state_T_nl[rd][i + 8]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 12] >= state_T_nl[rd][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 12] >= state_T_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_l[rd + 1][i + 12] <= state_T_nl[rd][i] + state_T_nl[rd][i + 8]
            for i in range(4)
        )

    state_T_l[r_dist] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_T_l_" + str(r_dist)
    )
    for rd in range(r_dist - 1, r_mid - 1, -1):
        state_T_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_T_nl_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(
            state_T_nl[rd][i] == state_T_l[rd + 1][i + 4] for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_T_nl[rd][i + 4] >= state_T_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 4] >= state_T_l[rd + 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 4] >= state_T_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 4]
            <= state_T_l[rd + 1][i + 4]
            + state_T_l[rd + 1][i + 8]
            + state_T_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_T_nl[rd][i + 8] >= state_T_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 8] >= state_T_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 8]
            <= state_T_l[rd + 1][i + 4] + state_T_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_T_nl[rd][i + 12] >= state_T_l[rd + 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 12] >= state_T_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_T_nl[rd][i + 12] <= state_T_l[rd + 1][i] + state_T_l[rd + 1][i + 12]
            for i in range(4)
        )
        # SR
        if rd > r_mid:
            state_T_l[rd] = SKINNY.addVars(
                16, vtype=GRB.BINARY, name="state_T_l_" + str(rd)
            )
        SKINNY.addConstrs(state_T_l[rd][SR[i]] == state_T_nl[rd][i] for i in range(16))

    # Reasonable: T[0] (T[r_dist]) has at least one non-zero difference
    SKINNY.addConstr(quicksum(state_T_l[0][i] for i in range(16)) >= 1)
    SKINNY.addConstr(quicksum(state_T_l[r_dist][i] for i in range(16)) >= 1)

    # VAR GT - determination + VAR T
    state_GT_l[r_mid] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_GT_l_" + str(r_mid)
    )
    state_GT_nl[r_mid] = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="state_GT_nl_" + str(r_mid)
    )
    for i in range(16):
        SKINNY.addGenConstrAnd(
            state_GT_l[r_mid][i], [state_T_l[r_mid][i], state_Z[r_mid][i]]
        )
        SKINNY.addConstr(state_GT_l[r_mid][SR[i]] == state_GT_nl[r_mid][i])
    # backward determination between dummy_GT[rd] and state_GT_l[rd + 1]
    for rd in range(r_mid - 1, -1, -1):
        dummy_GT[rd] = SKINNY.addVars(16, vtype=GRB.BINARY, name="dummy_GT_" + str(rd))
        state_GT_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_GT_nl_" + str(rd)
        )
        state_GT_l[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_GT_l_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(dummy_GT[rd][i] >= state_GT_l[rd + 1][i] for i in range(4))
        SKINNY.addConstrs(
            dummy_GT[rd][i] >= state_GT_l[rd + 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd][i] >= state_GT_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd][i]
            <= state_GT_l[rd + 1][i]
            + state_GT_l[rd + 1][i + 4]
            + state_GT_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            dummy_GT[rd][i + 4] == state_GT_l[rd + 1][i + 8] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            dummy_GT[rd][i + 8] >= state_GT_l[rd + 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd][i + 8] >= state_GT_l[rd + 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd][i + 8] >= state_GT_l[rd + 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd][i + 8]
            <= state_GT_l[rd + 1][i]
            + state_GT_l[rd + 1][i + 8]
            + state_GT_l[rd + 1][i + 12]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            dummy_GT[rd][i + 12] == state_GT_l[rd + 1][i] for i in range(4)
        )
        # SR
        SKINNY.addConstrs(
            state_GT_l[rd][SR[i]] == state_GT_nl[rd][i] for i in range(16)
        )
        # state_GT_nl[rd] = dummy_GT[rd] & state_T_nl[rd]
        for i in range(16):
            SKINNY.addGenConstrAnd(
                state_GT_nl[rd][i], [dummy_GT[rd][i], state_T_nl[rd][i]]
            )
            Deg.add(state_GT_l[rd][i])
    # forward determination between dummy_GT[rd + 1] and state_GT_nl[rd]
    for rd in range(r_mid, r_dist):
        dummy_GT[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="dummy_GT_" + str(rd + 1)
        )
        state_GT_l[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_GT_l_" + str(rd + 1)
        )
        # MC - COL1
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i] == state_GT_nl[rd][i + 12] for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 4] >= state_GT_nl[rd][i] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 4] >= state_GT_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 4] >= state_GT_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 4]
            <= state_GT_nl[rd][i] + state_GT_nl[rd][i + 4] + state_GT_nl[rd][i + 8]
            for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 8] == state_GT_nl[rd][i + 4] for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 12] >= state_GT_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 12] >= state_GT_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 12] >= state_GT_nl[rd][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            dummy_GT[rd + 1][i + 12]
            <= state_GT_nl[rd][i + 4] + state_GT_nl[rd][i + 8] + state_GT_nl[rd][i + 12]
            for i in range(4)
        )
        # SR
        if rd < r_dist - 1:
            state_GT_nl[rd + 1] = SKINNY.addVars(
                16, vtype=GRB.BINARY, name="state_GT_nl_" + str(rd + 1)
            )
            SKINNY.addConstrs(
                state_GT_l[rd + 1][SR[i]] == state_GT_nl[rd + 1][i] for i in range(16)
            )
        # state_GT_l[rd + 1] = dummy_GT[rd + 1] & state_T_l[rd + 1]
        for i in range(16):
            SKINNY.addGenConstrAnd(
                state_GT_l[rd + 1][i], [dummy_GT[rd + 1][i], state_T_l[rd + 1][i]]
            )
            Deg.add(state_GT_l[rd + 1][i])

    # VAR GZ: Z=1 and GT=0
    for rd in range(r_dist + 1):
        state_GZ[rd] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_GZ_" + str(rd))
        SKINNY.addConstrs(state_GZ[rd][i] <= state_Z[rd][i] for i in range(16))
        SKINNY.addConstrs(state_GZ[rd][i] <= 1 - state_GT_l[rd][i] for i in range(16))
        SKINNY.addConstrs(
            state_GZ[rd][i] >= state_Z[rd][i] - state_GT_l[rd][i] for i in range(16)
        )
        if rd < r_dist:
            for i in range(16):
                Deg.add(state_GZ[rd][i])

    # for i in range(16):
    #     Deg.add(state_GT_l[0][i])

    # VAR GU: Z=1 or GT=1
    for rd in range(r_dist + 1):
        state_GU[rd] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_GU_" + str(rd))
        for i in range(16):
            SKINNY.addGenConstrOr(state_GU[rd][i], [state_Z[rd][i], state_GT_l[rd][i]])

    # Specific condition (Non-full key addition)
    for rd in range(r_dist):
        con_1[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_1_" + str(rd))
        con_2[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_2_" + str(rd))
        con_3[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_3_" + str(rd))
        con_4[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_4_" + str(rd))
        for i in range(4):
            SKINNY.addConstr(
                state_GU[rd + 1][i + 4]
                + state_GU[rd + 1][i + 12]
                + state_GU[rd][SR[i + 8]]
                >= 3 * con_1[rd][i]
            )
            SKINNY.addConstr(
                state_GU[rd + 1][i + 4]
                + state_GU[rd + 1][i + 12]
                + state_GU[rd][SR[i + 8]]
                <= 2 + con_1[rd][i]
            )
            SKINNY.addConstr(
                state_GU[rd + 1][i]
                + state_GU[rd + 1][i + 12]
                + state_GU[rd][SR[i + 12]]
                >= 3 * con_2[rd][i]
            )
            SKINNY.addConstr(
                state_GU[rd + 1][i]
                + state_GU[rd + 1][i + 12]
                + state_GU[rd][SR[i + 12]]
                <= 2 + con_2[rd][i]
            )
            SKINNY.addConstr(
                state_GU[rd + 1][i]
                + state_GU[rd + 1][i + 4]
                + state_GU[rd][SR[i + 8]]
                + state_GU[rd][SR[i + 12]]
                >= 4 * con_3[rd][i]
            )
            SKINNY.addConstr(
                state_GU[rd + 1][i]
                + state_GU[rd + 1][i + 4]
                + state_GU[rd][SR[i + 8]]
                + state_GU[rd][SR[i + 12]]
                <= 3 + con_3[rd][i]
            )
            SKINNY.addGenConstrIndicator(
                con_4[rd][i], 1, con_1[rd][i] + con_2[rd][i] + con_3[rd][i] >= 3
            )
            SKINNY.addGenConstrIndicator(
                con_4[rd][i], 0, con_1[rd][i] + con_2[rd][i] + con_3[rd][i] <= 1
            )
            Con.add(con_1[rd][i])
            Con.add(con_2[rd][i])
            Con.add(con_3[rd][i])
            Con.add(-con_4[rd][i])

    # VAR V
    for rd in range(r_dist):
        state_V_sb[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_V_sb_" + str(rd)
        )
        state_V[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_V_" + str(rd + 1)
        )
        dummy_V[rd + 1] = SKINNY.addVars(
            28, vtype=GRB.BINARY, name="dummy_V_" + str(rd + 1)
        )
        key_V[rd] = SKINNY.addVars(8, vtype=GRB.BINARY, name="key_V_" + str(rd))
        for i in range(4):
            # Row 1 for V_sb
            SKINNY.addConstr(state_V_sb[rd][i] == state_V[rd + 1][i + 4])
            # Row 2 for V_sb
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i + 20],
                [state_V[rd + 1][i + 4], state_V[rd + 1][i + 12]],
            )
            SKINNY.addGenConstrOr(
                dummy_V[rd + 1][i + 24],
                [state_V_sb[rd][i + 8], dummy_V[rd + 1][i + 20]],
            )
            SKINNY.addGenConstrAnd(
                state_V_sb[rd][i + 4],
                [state_V[rd + 1][i + 8], dummy_V[rd + 1][i + 24]],
            )
            # Row 3 for V_sb
            SKINNY.addConstr(state_V_sb[rd][i + 8] == state_GU[rd][SR[i + 8]])
            # Row 4 for V_sb
            SKINNY.addConstr(state_V_sb[rd][i + 12] == state_GU[rd][SR[i + 12]])
            # Row 1 for V
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i], [state_V_sb[rd][i + 12], state_V[rd + 1][i + 12]]
            )
            SKINNY.addGenConstrOr(
                state_V[rd + 1][i], [dummy_V[rd + 1][i], state_GU[rd + 1][i]]
            )
            # Row 2 for V
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i + 4], [state_V_sb[rd][i + 8], state_V[rd + 1][i + 12]]
            )
            SKINNY.addGenConstrOr(
                state_V[rd + 1][i + 4],
                [dummy_V[rd + 1][i + 4], state_GU[rd + 1][i + 4]],
            )
            # Row 3 for V
            SKINNY.addConstr(state_V[rd + 1][i + 8] == state_GU[rd + 1][i + 8])
            # Row 4 for V
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i + 8], [state_V_sb[rd][i + 12], state_V[rd + 1][i]]
            )
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i + 12], [state_V_sb[rd][i + 8], state_V[rd + 1][i + 4]]
            )
            SKINNY.addGenConstrOr(
                dummy_V[rd + 1][i + 16],
                [dummy_V[rd + 1][i + 8], dummy_V[rd + 1][i + 12]],
            )
            SKINNY.addGenConstrOr(
                state_V[rd + 1][i + 12],
                [dummy_V[rd + 1][i + 16], state_GU[rd + 1][i + 12]],
            )
        for i in range(8):
            SKINNY.addGenConstrAnd(
                key_V[rd][SR[i]], [state_V_sb[rd][i], state_GU[rd][SR[i]]]
            )

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
    for i in range(16):
        Data.add(state_M_l[0][i])

    # VAR O - backward determination
    if r_in > 0:
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

    # VAR E - forward differential
    state_E_l[0] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_E_l_0")
    SKINNY.addConstrs(state_E_l[0][i] == state_T_l[r_dist][i] for i in range(16))
    for rd in range(r_out):
        state_E_nl[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_E_nl_" + str(rd)
        )
        state_E_l[rd + 1] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_E_l_" + str(rd + 1)
        )
        # SR
        SKINNY.addConstrs(state_E_nl[rd][i] == state_E_l[rd][SR[i]] for i in range(16))
        # MC - COL1
        SKINNY.addConstrs(state_E_l[rd + 1][i] >= state_E_nl[rd][i] for i in range(4))
        SKINNY.addConstrs(
            state_E_l[rd + 1][i] >= state_E_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i] >= state_E_nl[rd][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i]
            <= state_E_nl[rd][i] + state_E_nl[rd][i + 8] + state_E_nl[rd][i + 12]
            for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 4] == state_E_nl[rd][i] for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 8] >= state_E_nl[rd][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 8] >= state_E_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 8] <= state_E_nl[rd][i + 4] + state_E_nl[rd][i + 8]
            for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 12] >= state_E_nl[rd][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 12] >= state_E_nl[rd][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_E_l[rd + 1][i + 12] <= state_E_nl[rd][i] + state_E_nl[rd][i + 8]
            for i in range(4)
        )

    # VAR F - forward determination
    state_F_l[1] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_F_l_1")
    state_F_nl[1] = SKINNY.addVars(16, vtype=GRB.BINARY, name="state_F_nl_1")
    SKINNY.addConstrs(state_F_l[1][i] == state_E_l[1][i] for i in range(16))
    SKINNY.addConstrs(state_F_nl[1][i] == state_E_nl[1][i] for i in range(16))
    for rd in range(2, r_out + 1):
        state_F_l[rd] = SKINNY.addVars(
            16, vtype=GRB.BINARY, name="state_F_l_" + str(rd)
        )
        # MC - COL1
        SKINNY.addConstrs(
            state_F_l[rd][i] == state_F_nl[rd - 1][i + 12] for i in range(4)
        )
        # MC - COL2
        SKINNY.addConstrs(
            state_F_l[rd][i + 4] >= state_F_nl[rd - 1][i] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 4] >= state_F_nl[rd - 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 4] >= state_F_nl[rd - 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 4]
            <= state_F_nl[rd - 1][i]
            + state_F_nl[rd - 1][i + 4]
            + state_F_nl[rd - 1][i + 8]
            for i in range(4)
        )
        # MC - COL3
        SKINNY.addConstrs(
            state_F_l[rd][i + 8] == state_F_nl[rd - 1][i + 4] for i in range(4)
        )
        # MC - COL4
        SKINNY.addConstrs(
            state_F_l[rd][i + 12] >= state_F_nl[rd - 1][i + 4] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 12] >= state_F_nl[rd - 1][i + 8] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 12] >= state_F_nl[rd - 1][i + 12] for i in range(4)
        )
        SKINNY.addConstrs(
            state_F_l[rd][i + 12]
            <= state_F_nl[rd - 1][i + 4]
            + state_F_nl[rd - 1][i + 8]
            + state_F_nl[rd - 1][i + 12]
            for i in range(4)
        )
        if rd < r_out:
            state_F_nl[rd] = SKINNY.addVars(
                16, vtype=GRB.BINARY, name="state_F_nl_" + str(rd)
            )
            # SR
            SKINNY.addConstrs(
                state_F_nl[rd][i] >= state_F_l[rd][SR[i]] for i in range(16)
            )
            SKINNY.addConstrs(state_F_nl[rd][i] >= state_E_nl[rd][i] for i in range(16))
            SKINNY.addConstrs(
                state_F_nl[rd][i] <= state_F_l[rd][SR[i]] + state_E_nl[rd][i]
                for i in range(16)
            )

    for rd in range(1, r_out):
        key_out[rd] = SKINNY.addVars(8, vtype=GRB.BINARY, name="key_out_" + str(rd))
        SKINNY.addConstrs(key_out[rd][i] >= state_W_l[rd][i] for i in range(8))
        SKINNY.addConstrs(key_out[rd][SR[i]] >= state_F_nl[rd][i] for i in range(8))
        SKINNY.addConstrs(
            key_out[rd][SR[i]] <= state_W_l[rd][SR[i]] + state_F_nl[rd][i]
            for i in range(8)
        )

    # Key-Bridging & Key-dependent-sieve
    for i in range(16):
        key_dep[i] = LinExpr()
        key_bri[i] = LinExpr()

    tmp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    for rd in range(r_in + r_dist + r_out):
        if rd < r_in - 1:
            for i in range(8):
                key_bri[tmp[SR[i]]].add(state_O_nl[rd][i])
        elif rd > r_in + r_dist:
            for i in range(8):
                key_bri[tmp[i]].add(key_out[rd - r_in - r_dist][i])
        elif rd < r_in + r_dist - 1 and rd >= r_in:
            # print(tmp)
            for i in range(8):
                key_dep[tmp[i]].add(key_V[rd - r_in][i])
        for i in range(16):
            tmp[i] = PT[tmp[i]]

    big_M = 50
    dummy_K = SKINNY.addVars(
        16, vtype=GRB.INTEGER, name="dummy_K"
    )  # number add to key_seive
    dummy_B = SKINNY.addVars(
        16, vtype=GRB.BINARY, name="dummy_B"
    )  # 0/1 for key_dep[i]>=4 or not
    for i in range(16):
        SKINNY.addGenConstrIndicator(dummy_B[i], 1, key_dep[i] >= 4)
        SKINNY.addGenConstrIndicator(dummy_B[i], 0, key_dep[i] <= 3)
        SKINNY.addConstr(dummy_K[i] >= key_dep[i] - 3)
        SKINNY.addConstr(dummy_K[i] >= 0)
        SKINNY.addConstr(dummy_K[i] <= key_dep[i] - 3 + big_M * (1 - dummy_B[i]))
        SKINNY.addConstr(dummy_K[i] <= big_M * dummy_B[i])
        Key_sieve.add(dummy_K[i])

    alpha = SKINNY.addVars(16, vtype=GRB.BINARY, name="alpha")
    beta = SKINNY.addVars(16, vtype=GRB.BINARY, name="beta")
    gamma = SKINNY.addVars(16, vtype=GRB.BINARY, name="gamma")
    for i in range(16):
        SKINNY.addGenConstrIndicator(alpha[i], 1, key_bri[i] >= 3)
        SKINNY.addGenConstrIndicator(alpha[i], 0, key_bri[i] <= 2)
        SKINNY.addGenConstrIndicator(beta[i], 1, key_bri[i] >= 2)
        SKINNY.addGenConstrIndicator(beta[i], 0, key_bri[i] <= 1)
        SKINNY.addGenConstrIndicator(gamma[i], 1, key_bri[i] >= 1)
        SKINNY.addGenConstrIndicator(gamma[i], 0, key_bri[i] == 0)
        Key.add(alpha[i])
        Key.add(beta[i])
        Key.add(gamma[i])

    SKINNY.addConstr(Key <= 46)

    # Objective function
    SKINNY.addConstr(Obj >= Start + Deg - Con - Key_sieve)
    SKINNY.addConstr(Obj >= Start + Key)
    # SKINNY.addConstr(quicksum(state_Z[r_dist][i] for i in range(16)) == 1)
    # SKINNY.addConstr(quicksum(state_T_l[r_dist][i] for i in range(16)) <= 2)
    # SKINNY.addConstr(state_Z[0][13] == 1)  # To be deleted!!!
    SKINNY.setObjective(Obj, GRB.MINIMIZE)

    # Start solver
    # SKINNY.setParam("OutputFlag", 0)
    SKINNY.Params.PoolSearchMode = 2
    SKINNY.Params.PoolSolutions = 1  # Number of sols
    SKINNY.Params.PoolGap = 2.0
    SKINNY.Params.TimeLimit = 200
    # SKINNY.setParam("IntFeasTol", 1e-9)
    SKINNY.optimize()
    file = open("output", "w")
    sys.stdout = file
    print("Model Status:", SKINNY.Status)
    if SKINNY.Status == 2 or SKINNY.Status == 9:
        print("Min_Obj: %g" % SKINNY.ObjVal)

        # All solutions
        for k in range(SKINNY.SolCount):
            SKINNY.Params.SolutionNumber = k
            print(
                "******** Sol no.{}    Obj = {}    Deg = {} - {} - {} = {}    R_mid = {}    Key = {}    Data = {} ********".format(
                    k + 1,
                    round(Obj.Xn),
                    round(Evaluate_expr(Deg)),
                    round(Evaluate_expr(Con)),
                    round(Evaluate_expr(Key_sieve)),
                    round(
                        Evaluate_expr(Deg)
                        - Evaluate_expr(Con)
                        - Evaluate_expr(Key_sieve)
                    ),
                    r_mid,
                    round(Evaluate_expr(Key)),
                    round(Evaluate_expr(Data)),
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
            strr += "]    TA = [ "
            for i in range(16):
                if round(state_T_l[0][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]    TB = [ "
            for i in range(16):
                if round(state_T_l[r_dist][i].Xn) == 1:
                    strr += str(i) + " "
            strr += "]"
            print(strr)

            print("---------- Var X ----------")
            for rd in range(r_dist + 1):
                print("X_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_X_l[rd][4 * i].Xn),
                        round(state_X_l[rd][4 * i + 1].Xn),
                        round(state_X_l[rd][4 * i + 2].Xn),
                        round(state_X_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_dist:
                    print("X_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_X_nl[rd][4 * i].Xn),
                            round(state_X_nl[rd][4 * i + 1].Xn),
                            round(state_X_nl[rd][4 * i + 2].Xn),
                            round(state_X_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var Y ----------")
            for rd in range(r_dist + 1):
                print("Y_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_Y_l[rd][4 * i].Xn),
                        round(state_Y_l[rd][4 * i + 1].Xn),
                        round(state_Y_l[rd][4 * i + 2].Xn),
                        round(state_Y_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_dist:
                    print("Y_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_Y_nl[rd][4 * i].Xn),
                            round(state_Y_nl[rd][4 * i + 1].Xn),
                            round(state_Y_nl[rd][4 * i + 2].Xn),
                            round(state_Y_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var Z ----------")
            for rd in range(r_dist + 1):
                print("Z[", rd, "]")
                for i in range(4):
                    print(
                        round(state_Z[rd][4 * i].Xn),
                        round(state_Z[rd][4 * i + 1].Xn),
                        round(state_Z[rd][4 * i + 2].Xn),
                        round(state_Z[rd][4 * i + 3].Xn),
                    )

            print("---------- Var GZ ----------")
            for rd in range(r_dist + 1):
                print("GZ[", rd, "]")
                for i in range(4):
                    print(
                        round(state_GZ[rd][4 * i].Xn),
                        round(state_GZ[rd][4 * i + 1].Xn),
                        round(state_GZ[rd][4 * i + 2].Xn),
                        round(state_GZ[rd][4 * i + 3].Xn),
                    )

            print("---------- Var GT ----------")
            for rd in range(r_dist + 1):
                print("GT_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_GT_l[rd][4 * i].Xn),
                        round(state_GT_l[rd][4 * i + 1].Xn),
                        round(state_GT_l[rd][4 * i + 2].Xn),
                        round(state_GT_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_dist:
                    print("GT_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_GT_nl[rd][4 * i].Xn),
                            round(state_GT_nl[rd][4 * i + 1].Xn),
                            round(state_GT_nl[rd][4 * i + 2].Xn),
                            round(state_GT_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var T ----------")
            for rd in range(r_dist + 1):
                print("T_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_T_l[rd][4 * i].Xn),
                        round(state_T_l[rd][4 * i + 1].Xn),
                        round(state_T_l[rd][4 * i + 2].Xn),
                        round(state_T_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_dist:
                    print("T_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_T_nl[rd][4 * i].Xn),
                            round(state_T_nl[rd][4 * i + 1].Xn),
                            round(state_T_nl[rd][4 * i + 2].Xn),
                            round(state_T_nl[rd][4 * i + 3].Xn),
                        )

            # print("---------- Var V ----------")
            # for rd in range(r_dist):
            #     print("V_sb[", rd, "]")
            #     for i in range(4):
            #         print(
            #             round(state_V_sb[rd][4 * i].Xn),
            #             round(state_V_sb[rd][4 * i + 1].Xn),
            #             round(state_V_sb[rd][4 * i + 2].Xn),
            #             round(state_V_sb[rd][4 * i + 3].Xn),
            #         )
            #     print("V[", rd + 1, "]")
            #     for i in range(4):
            #         print(
            #             round(state_V[rd + 1][4 * i].Xn),
            #             round(state_V[rd + 1][4 * i + 1].Xn),
            #             round(state_V[rd + 1][4 * i + 2].Xn),
            #             round(state_V[rd + 1][4 * i + 3].Xn),
            #         )

            print("---------- Key V ----------")
            for rd in range(r_dist):
                print("Key_V[", rd, "]")
                for i in range(2):
                    print(
                        round(key_V[rd][4 * i].Xn),
                        round(key_V[rd][4 * i + 1].Xn),
                        round(key_V[rd][4 * i + 2].Xn),
                        round(key_V[rd][4 * i + 3].Xn),
                    )

            print("---------- Var M ----------")
            for rd in range(r_in + 1):
                print("M_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_M_l[rd][4 * i].Xn),
                        round(state_M_l[rd][4 * i + 1].Xn),
                        round(state_M_l[rd][4 * i + 2].Xn),
                        round(state_M_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_in:
                    print("M_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_M_nl[rd][4 * i].Xn),
                            round(state_M_nl[rd][4 * i + 1].Xn),
                            round(state_M_nl[rd][4 * i + 2].Xn),
                            round(state_M_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var O ----------")
            for rd in range(r_in):
                print("O_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_O_l[rd][4 * i].Xn),
                        round(state_O_l[rd][4 * i + 1].Xn),
                        round(state_O_l[rd][4 * i + 2].Xn),
                        round(state_O_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_in - 1:
                    print("O_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_O_nl[rd][4 * i].Xn),
                            round(state_O_nl[rd][4 * i + 1].Xn),
                            round(state_O_nl[rd][4 * i + 2].Xn),
                            round(state_O_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var W ----------")
            for rd in range(r_out + 1):
                print("W_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_W_l[rd][4 * i].Xn),
                        round(state_W_l[rd][4 * i + 1].Xn),
                        round(state_W_l[rd][4 * i + 2].Xn),
                        round(state_W_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_out:
                    print("W_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_W_nl[rd][4 * i].Xn),
                            round(state_W_nl[rd][4 * i + 1].Xn),
                            round(state_W_nl[rd][4 * i + 2].Xn),
                            round(state_W_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var E ----------")
            for rd in range(r_out + 1):
                print("E_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_E_l[rd][4 * i].Xn),
                        round(state_E_l[rd][4 * i + 1].Xn),
                        round(state_E_l[rd][4 * i + 2].Xn),
                        round(state_E_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_out:
                    print("E_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_E_nl[rd][4 * i].Xn),
                            round(state_E_nl[rd][4 * i + 1].Xn),
                            round(state_E_nl[rd][4 * i + 2].Xn),
                            round(state_E_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Var F ----------")
            for rd in range(1, r_out + 1):
                print("F_linear[", rd, "]")
                for i in range(4):
                    print(
                        round(state_F_l[rd][4 * i].Xn),
                        round(state_F_l[rd][4 * i + 1].Xn),
                        round(state_F_l[rd][4 * i + 2].Xn),
                        round(state_F_l[rd][4 * i + 3].Xn),
                    )
                if rd < r_out:
                    print("F_non_linear[", rd, "]")
                    for i in range(4):
                        print(
                            round(state_F_nl[rd][4 * i].Xn),
                            round(state_F_nl[rd][4 * i + 1].Xn),
                            round(state_F_nl[rd][4 * i + 2].Xn),
                            round(state_F_nl[rd][4 * i + 3].Xn),
                        )

            print("---------- Con ----------")
            for rd in range(r_dist):
                print(
                    "con[",
                    rd,
                    "] :",
                    round(
                        con_1[rd][0].Xn
                        + con_2[rd][0].Xn
                        + con_3[rd][0].Xn
                        - con_4[rd][0].Xn
                    ),
                    round(
                        con_1[rd][1].Xn
                        + con_2[rd][1].Xn
                        + con_3[rd][1].Xn
                        - con_4[rd][1].Xn
                    ),
                    round(
                        con_1[rd][2].Xn
                        + con_2[rd][2].Xn
                        + con_3[rd][2].Xn
                        - con_4[rd][2].Xn
                    ),
                    round(
                        con_1[rd][3].Xn
                        + con_2[rd][3].Xn
                        + con_3[rd][3].Xn
                        - con_4[rd][3].Xn
                    ),
                )

        print("---------- Key-Bridge ----------")
        strr = ""
        for i in range(16):
            strr += str(round(Evaluate_expr(key_bri[i]))) + " "
        print(strr)

        print("---------- Key-Dependent-Seive ----------")
        strr = ""
        for i in range(16):
            strr += str(round(Evaluate_expr(key_dep[i]))) + " "
        print(strr)
    file.close()

    return SKINNY.Status


if __name__ == "__main__":

    # round_dist = 12

    # # Enumerate r_mid
    # for i in range(1, round_dist):
    #     # r_dist, r_mid
    #     Search_ds_distinguishers_td(round_dist, i)
    Search_ds_distinguishers_td(12, 6, 3, 8)
