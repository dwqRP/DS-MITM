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


def Search_ds_mitm_attacks(r_dist, r_in, r_out, mx_deg, mx_key, mx_data):
    SKINNY = Model("SKINNY")
    # l -(SB,AK,SR)-> nl -(MC)-> l
    state_X_l = {}  # VAR X
    state_X_nl = {}
    state_Y_l = {}  # VAR Y
    state_Y_nl = {}
    state_Z = {}  # VAR Z
    state_V_sb = {}  # VAR V
    state_V = {}
    dummy_V = {}  # dummy for VAR V
    key_V = {}  # key for VAR V
    con_1 = {}  # cipher-specific constraints (non-full key addition)
    con_2 = {}
    con_3 = {}
    con_4 = {}
    Deg = LinExpr()
    Con = LinExpr()
    Key_sieve = LinExpr()
    Key = LinExpr()
    Data = LinExpr()
    Start = LinExpr()
    Val_Con = SKINNY.addVar(vtype=GRB.INTEGER, name="Val_Con")
    Obj = SKINNY.addVar(vtype=GRB.INTEGER, name="Obj")
    state_W_l = {}  # VAR W
    state_W_nl = {}
    state_M_l = {}  # VAR M
    state_M_nl = {}
    state_O_l = {}  # VAR O
    state_O_nl = {}
    key_bri = {}
    key_dep = {}

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

    for i in range(16):
        Start.add(state_Z[0][i])

    # Non trival
    SKINNY.addConstr(quicksum(state_X_l[0][i] for i in range(16)) >= 1)
    SKINNY.addConstr(quicksum(state_Y_l[r_dist][i] for i in range(16)) >= 1)

    # Specific condition (Non-full key addition)
    for rd in range(r_dist):
        con_1[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_1_" + str(rd))
        con_2[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_2_" + str(rd))
        con_3[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_3_" + str(rd))
        con_4[rd] = SKINNY.addVars(4, vtype=GRB.BINARY, name="con_4_" + str(rd))
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
            SKINNY.addConstr(
                state_Z[rd + 1][i]
                + state_Z[rd + 1][i + 4]
                + state_Z[rd][SR[i + 8]]
                + state_Z[rd][SR[i + 12]]
                >= 4 * con_3[rd][i]
            )
            SKINNY.addConstr(
                state_Z[rd + 1][i]
                + state_Z[rd + 1][i + 4]
                + state_Z[rd][SR[i + 8]]
                + state_Z[rd][SR[i + 12]]
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
            SKINNY.addConstr(state_V_sb[rd][i + 8] == state_Z[rd][SR[i + 8]])
            # Row 4 for V_sb
            SKINNY.addConstr(state_V_sb[rd][i + 12] == state_Z[rd][SR[i + 12]])
            # Row 1 for V
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i], [state_V_sb[rd][i + 12], state_V[rd + 1][i + 12]]
            )
            SKINNY.addGenConstrOr(
                state_V[rd + 1][i], [dummy_V[rd + 1][i], state_Z[rd + 1][i]]
            )
            # Row 2 for V
            SKINNY.addGenConstrAnd(
                dummy_V[rd + 1][i + 4], [state_V_sb[rd][i + 8], state_V[rd + 1][i + 12]]
            )
            SKINNY.addGenConstrOr(
                state_V[rd + 1][i + 4], [dummy_V[rd + 1][i + 4], state_Z[rd + 1][i + 4]]
            )
            # Row 3 for V
            SKINNY.addConstr(state_V[rd + 1][i + 8] == state_Z[rd + 1][i + 8])
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
                [dummy_V[rd + 1][i + 16], state_Z[rd + 1][i + 12]],
            )
        for i in range(8):
            SKINNY.addGenConstrAnd(
                key_V[rd][SR[i]], [state_V_sb[rd][i], state_Z[rd][SR[i]]]
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
                key_bri[tmp[i]].add(state_W_l[rd - r_in - r_dist][i])
        elif rd < r_in + r_dist - 1 and rd >= r_in:
            # print(tmp)
            for i in range(8):
                key_dep[tmp[i]].add(key_V[rd - r_in][i])
        for i in range(16):
            tmp[i] = PT[tmp[i]]

    # SKINNY.update()
    # for i in range(16):
    #     print(key_bri[i])

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

    big_M = 50
    dummy_K = SKINNY.addVars(16, vtype=GRB.INTEGER, name="dummy_K")
    dummy_B = SKINNY.addVars(16, vtype=GRB.BINARY, name="dummy_B")
    for i in range(16):
        SKINNY.addGenConstrIndicator(dummy_B[i], 1, key_dep[i] >= 4)
        SKINNY.addGenConstrIndicator(dummy_B[i], 0, key_dep[i] <= 3)
        SKINNY.addConstr(dummy_K[i] >= key_dep[i] - 3)
        SKINNY.addConstr(dummy_K[i] >= 0)
        SKINNY.addConstr(dummy_K[i] <= key_dep[i] - 3 + big_M * (1 - dummy_B[i]))
        SKINNY.addConstr(dummy_K[i] <= big_M * dummy_B[i])
        Key_sieve.add(dummy_K[i])

    # Value Constraints
    SKINNY.addConstr(Val_Con <= Data - 1)
    SKINNY.addConstr(Val_Con >= 0)
    # SKINNY.addConstr(Val_Con == 0)
    # SKINNY.addConstr(Key_sieve <= 2)
    SKINNY.addConstr(Obj >= Start + Deg - Con - Key_sieve - Val_Con)
    # SKINNY.addConstr(Obj >= Deg - Con)
    SKINNY.addConstr(Obj >= Start + Key + Val_Con - 1)

    # Reasonable
    if mx_key != 0:
        SKINNY.addConstr(Key <= mx_key)
    else:
        SKINNY.addConstr(Key <= 47)
    if mx_deg != 0:
        SKINNY.addConstr(Deg - Con - Key_sieve <= mx_deg)
    # else:
    #     SKINNY.addConstr(Deg - Con <= 47)
    if mx_data != 0:
        SKINNY.addConstr(Data <= mx_data)
    else:
        SKINNY.addConstr(Data <= 15)

    # Objective function
    # SKINNY.addConstr(state_Z[0][12] == 1)  # To be deleted!!!
    SKINNY.setObjective(Obj, GRB.MINIMIZE)

    # Start solver
    SKINNY.setParam("OutputFlag", 0)
    SKINNY.Params.PoolSearchMode = 2
    SKINNY.Params.PoolSolutions = 1  # Number of sols
    SKINNY.Params.PoolGap = 2.0
    SKINNY.Params.TimeLimit = 200
    # SKINNY.setParam("IntFeasTol", 1e-9)
    SKINNY.optimize()
    print("Model Status:", SKINNY.Status)
    if SKINNY.Status == 2 or SKINNY.Status == 9:
        print("Min_Obj: %g" % SKINNY.ObjVal)

        # All solutions
        for k in range(SKINNY.SolCount):
            SKINNY.Params.SolutionNumber = k
            print(
                "******** Sol no.{}    Obj = {}    Deg = {} - {} - {} = {}    Key = {}    Data = {}    Val_Con = {} ********".format(
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
                    round(Evaluate_expr(Key)),
                    round(Evaluate_expr(Data)),
                    round(Val_Con.Xn),
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

            # print("---------- Key V ----------")
            # for rd in range(r_dist):
            #     print("Key_V[", rd, "]")
            #     for i in range(2):
            #         print(
            #             round(key_V[rd][4 * i].Xn),
            #             round(key_V[rd][4 * i + 1].Xn),
            #             round(key_V[rd][4 * i + 2].Xn),
            #             round(key_V[rd][4 * i + 3].Xn),
            #         )

            # print("---------- Con ----------")
            # for rd in range(r_dist):
            #     print(
            #         "con[",
            #         rd,
            #         "] :",
            #         round(con_1[rd][0].Xn + con_2[rd][0].Xn + con_3[rd][0].Xn - con_4[rd][0].Xn),
            #         round(con_1[rd][1].Xn + con_2[rd][1].Xn + con_3[rd][1].Xn - con_4[rd][1].Xn),
            #         round(con_1[rd][2].Xn + con_2[rd][2].Xn + con_3[rd][2].Xn - con_4[rd][2].Xn),
            #         round(con_1[rd][3].Xn + con_2[rd][3].Xn + con_3[rd][3].Xn - con_4[rd][3].Xn),
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

            print("---------- Key Bridge ----------")
            strr = ""
            for i in range(16):
                strr += str(round(Evaluate_expr(key_bri[i]))) + " "
            print(strr)

    return SKINNY.Status


if __name__ == "__main__":
    # r_dist, r_in, r_out, mx_deg, mx_key, mx_data

    Search_ds_mitm_attacks(11, 3, 10, 0, 0, 0)

    # Exploiting Non-Full Key Additions: Full-Fledged Automatic Demirci-Selcuk Meet-in-the-Middle Cryptanalysis of SKINNY
    # Search_ds_mitm_attacks(9, 4, 10, 0, 0, 0)

    # Automatic DS Meet-in-the-Middle Attack on SKINNY with Key-Bridging
    # Search_ds_mitm_attacks(10, 3, 9, 0, 0, 0)
