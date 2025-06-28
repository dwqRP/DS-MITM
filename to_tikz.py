import sys
import re
import math

XX = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3]
YY = [3, 3, 3, 3, 2, 2, 2, 2, 1, 1, 1, 1, 0, 0, 0, 0]
SR = [0, 1, 2, 3, 7, 4, 5, 6, 10, 11, 8, 9, 13, 14, 15, 12]


def read_file():
    with open("output", "r") as f:
        content = f.read()
    lines = content.splitlines()
    # for idx, line in enumerate(lines):
    #     print(f"Line{idx}: {line}")
    return lines


def init(g, lines, typ, attr, bgn):
    st = ed = 0
    for idx, line in enumerate(lines):
        if "----------" in line and st != 0:
            ed = idx
            break
        if "Var " + attr in line or "Key " + attr in line:
            st = idx
    i = bgn
    j = 0
    for idx in range(st + 1, ed):
        line = lines[idx]
        if "[" in line:
            i += typ
            j = 0
            continue
        vals = line.split(" ")
        for k in range(4):
            g[i][j][attr] = int(vals[k])
            j += 1
    return g


def init_dist(g, lines):
    match = re.search(r"Deg = .*?= (\d+)", lines[2])
    if match:
        deg = int(match.group(1))

    st = ed = 0
    for idx, line in enumerate(lines):
        if "----------" in line and st != 0:
            ed = idx
            break
        if "Con" in line:
            st = idx
    i = -1
    cnt = 0
    for idx in range(st + 1, ed):
        line = lines[idx]
        i += 2
        vals = line.split(" ")
        vals = vals[-4:]
        # print(vals)
        for j in range(4):
            g[i][j]["Con"] = int(vals[j])
            cnt += g[i][j]["Con"]
    st = 0
    for idx, line in enumerate(lines):
        if "Key-Dependent-Seive" in line:
            st = idx + 1
            break
    strr = lines[st]
    strr = strr.split(" ")
    strr = strr[:-1]
    ans = 0
    for s in strr:
        # print("s:", s)
        ans += max(0, int(s) - 3)
    # print(cnt, ans)
    return g, deg, cnt, ans


def get_per(rd):
    tmp = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    per = [9, 15, 8, 13, 10, 14, 12, 11, 0, 1, 2, 3, 4, 5, 6, 7]
    for k in range(rd):
        for i in range(16):
            tmp[i] = per[tmp[i]]
    return tmp


def write_dist(g, r_dist, r_in, deg, nonfull, keyseive):
    txt = "\\documentclass{standalone}\n\\usepackage{tikz}\n\\usetikzlibrary{patterns}\n\\begin{document}\n\\begin{tikzpicture}[scale=0.32]\n"
    rows = math.ceil((r_dist * 2 + 1) / 4)
    # print(rows)
    y_shift = 0
    rnd = r_in
    block_cnt = 0
    for r in range(rows):
        txt += "  \\begin{{scope}}[yshift={}cm]\n".format(y_shift)
        y_shift += -6
        x_shift = 0
        for o in range(4):
            if block_cnt == 2 * r_dist + 1:
                txt += "    \\path (18,-1) node {{\\tiny $OBJ_{{Dis}}: {}\\ \\ \\ \\ \\ Cut_{{Nonfull}}: {}\\ \\ \\ \\ \\ Cut_{{Keyseive}}: {}$}};".format(
                    deg, nonfull, keyseive
                )
                break
            if (o == 0 or o == 2) and block_cnt != 2 * r_dist:
                # print(block_cnt)
                if o == 0:
                    txt += "    \\begin{scope}[xshift=-1cm,yshift=-1.5cm]\n"
                else:
                    txt += "    \\begin{scope}[xshift=33cm,yshift=3.5cm]\n"
                for j in range(8):
                    if g[block_cnt][j]["V"] == 1:
                        txt += "        \\fill[color=cyan!40] ({},{}) rectangle +(1,1);\n".format(
                            XX[j], YY[j] - 2
                        )
                txt += "        \\draw (0,0) rectangle +(4,2);\n"
                txt += "        \\draw (0,1) -- +(4,0);\n"
                txt += "        \\draw (1,0) -- +(0,2);\n"
                txt += "        \\draw (2,0) -- +(0,2);\n"
                txt += "        \\draw (3,0) -- +(0,2);\n"
                if o == 0:
                    txt += "        \\draw[->] (4,1) -- ++(8,0) -- ++(0,1.5);\n"
                else:
                    txt += "        \\draw[->] (0,1) -- ++(-8,0) -- ++(0,-1.5);\n"
                tmp = get_per(rnd)
                for j in range(8):
                    txt += "        \\path ({},{}) node {{\\tiny \\texttt{{{}}}}};\n".format(
                        XX[j] + 0.5, YY[j] - 1.5, tmp[j]
                    )
                txt += "    \\end{scope}\n"

            x_shift += 6 + o % 2
            txt += "    \\begin{{scope}}[xshift={}cm]\n".format(x_shift)
            if o % 2 == 0:
                txt += "        \\path (2,4.5) node {{\\tiny Round {}}};\n".format(rnd)
                rnd += 1
            for j in range(16):
                if g[block_cnt][j]["GT"] == 1:
                    txt += "        \\fill[color=blue!40] ({},{}) rectangle +(1,1);\n".format(
                        XX[j], YY[j]
                    )
                if block_cnt % 2 == 0:
                    if g[block_cnt][j]["GZ"] == 1:
                        txt += "        \\fill[color=red!40] ({},{}) rectangle +(1,1);\n".format(
                            XX[j], YY[j]
                        )
                if g[block_cnt][j]["X"] == 1:
                    txt += "        \\fill[pattern=north east lines] ({},{}) rectangle +(1,1);\n".format(
                        XX[j], YY[j]
                    )
                if g[block_cnt][j]["Y"] == 1:
                    txt += "        \\fill[pattern=north west lines] ({},{}) rectangle +(1,1);\n".format(
                        XX[j], YY[j]
                    )
                if g[block_cnt][j]["T"] == 1:
                    txt += "        \\fill ({},{}) circle (0.25);\n".format(
                        XX[j] + 0.5, YY[j] + 0.5
                    )
            txt += "        \\draw (0,0) rectangle (4,4);\n"
            txt += "        \\draw (0,1) -- +(4,0);\n"
            txt += "        \\draw (0,2) -- +(4,0);\n"
            txt += "        \\draw (0,3) -- +(4,0);\n"
            txt += "        \\draw (1,0) -- +(0,4);\n"
            txt += "        \\draw (2,0) -- +(0,4);\n"
            txt += "        \\draw (3,0) -- +(0,4);\n"
            if block_cnt != 2 * r_dist:
                if o == 0:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny ART,SR};\n"
                elif o == 1:
                    txt += (
                        "        \\draw[->] (4,2) -- node[above] {\\tiny MC} +(2,0);\n"
                    )
                    txt += "        \\path (5,-0.5) node {{\\tiny \\texttt{{{} {} {} {}}}}};\n".format(
                        g[block_cnt][0]["Con"],
                        g[block_cnt][1]["Con"],
                        g[block_cnt][2]["Con"],
                        g[block_cnt][3]["Con"],
                    )
                elif o == 2:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC,ART};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny SR};\n"
                else:
                    txt += "        \\path (5,2.5) node {\\tiny MC};\n"
                    txt += "        \\draw[->] (4,2) -- ++(1.5,0) -- ++(0,-3) -- ++(-27,0) -- ++(0,-3) -- ++(1.5,0);\n"
                    txt += "        \\path (5,-0.5) node {{\\tiny \\texttt{{{} {} {} {}}}}};\n".format(
                        g[block_cnt][0]["Con"],
                        g[block_cnt][1]["Con"],
                        g[block_cnt][2]["Con"],
                        g[block_cnt][3]["Con"],
                    )
            txt += "    \\end{scope}\n"
            block_cnt += 1
        txt += "  \\end{scope}\n"

    txt += "\\end{tikzpicture}\n\\end{document}\n"
    # print(txt)
    file = open("dist_tikz", "w")
    file.write(txt)


def init_keyr(g, lines):
    match = re.search(r"Key = (\d+)", lines[2])
    key = int(match.group(1))

    st = ed = 0
    for idx, line in enumerate(lines):
        if "----------" in line and st != 0:
            ed = idx
            break
        if "Var O" in line:
            st = idx
    i = -2
    for idx in range(st + 6, ed, 10):
        # print(lines[idx])
        i += 2
        line1 = lines[idx + 1]
        line2 = lines[idx + 2]
        vals = line1.split(" ") + line2.split(" ")
        # print(vals)
        for j in range(8):
            g[i][SR[j]]["O"] = int(vals[j])
    i += 2
    for j in range(8):
        g[i][j]["O"] = 0
    st = 0
    for idx, line in enumerate(lines):
        if "Key-Bridge" in line:
            st = idx + 1
            break
    strr = lines[st]
    strr = strr.split(" ")
    strr = strr[:-1]
    ans = 0
    for s in strr:
        ans += max(0, int(s) - 3)
    # print(key, ans)
    return g, key, ans


def write_keyr(g, r_dist, r_in, r_out, key, keybridge):
    txt = "\\documentclass{standalone}\n\\usepackage{tikz}\n\\usetikzlibrary{patterns}\n\\begin{document}\n\\begin{tikzpicture}[scale=0.32]\n"
    # print(rows)
    y_shift = 0
    rnd = 0
    block_cnt = 0
    rows = math.ceil((r_in * 2 + 1) / 4)
    for r in range(rows):
        txt += "  \\begin{{scope}}[yshift={}cm]\n".format(y_shift)
        y_shift += -6
        x_shift = 0
        for o in range(4):
            if block_cnt == 2 * r_in + 1:
                break
            if (o == 0 or o == 2) and block_cnt != 2 * r_in:
                if o == 0:
                    txt += "    \\begin{scope}[xshift=-1cm,yshift=-1.5cm]\n"
                else:
                    txt += "    \\begin{scope}[xshift=33cm,yshift=3.5cm]\n"
                for j in range(8):
                    if g[block_cnt][j]["O"] == 1:
                        txt += "        \\fill[color=orange!40] ({},{}) rectangle +(1,1);\n".format(
                            XX[j], YY[j] - 2
                        )
                txt += "        \\draw (0,0) rectangle +(4,2);\n"
                txt += "        \\draw (0,1) -- +(4,0);\n"
                txt += "        \\draw (1,0) -- +(0,2);\n"
                txt += "        \\draw (2,0) -- +(0,2);\n"
                txt += "        \\draw (3,0) -- +(0,2);\n"
                if o == 0:
                    txt += "        \\draw[->] (4,1) -- ++(8,0) -- ++(0,1.5);\n"
                else:
                    txt += "        \\draw[->] (0,1) -- ++(-8,0) -- ++(0,-1.5);\n"
                tmp = get_per(rnd)
                for j in range(8):
                    txt += "        \\path ({},{}) node {{\\tiny \\texttt{{{}}}}};\n".format(
                        XX[j] + 0.5, YY[j] - 1.5, tmp[j]
                    )
                txt += "    \\end{scope}\n"

            x_shift += 6 + o % 2
            txt += "    \\begin{{scope}}[xshift={}cm]\n".format(x_shift)
            if o % 2 == 0:
                txt += "        \\path (2,4.5) node {{\\tiny Round {}}};\n".format(rnd)
                rnd += 1
            for j in range(16):
                if g[block_cnt][j]["M"] == 1:
                    txt += "        \\fill[pattern=crosshatch ,pattern color=gray] ({},{}) rectangle +(1,1);\n".format(
                        XX[j], YY[j]
                    )
            txt += "        \\draw (0,0) rectangle (4,4);\n"
            txt += "        \\draw (0,1) -- +(4,0);\n"
            txt += "        \\draw (0,2) -- +(4,0);\n"
            txt += "        \\draw (0,3) -- +(4,0);\n"
            txt += "        \\draw (1,0) -- +(0,4);\n"
            txt += "        \\draw (2,0) -- +(0,4);\n"
            txt += "        \\draw (3,0) -- +(0,4);\n"
            if block_cnt != 2 * r_in:
                if o == 0:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny ART,SR};\n"
                elif o == 1:
                    txt += (
                        "        \\draw[->] (4,2) -- node[above] {\\tiny MC} +(2,0);\n"
                    )
                elif o == 2:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC,ART};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny SR};\n"
                else:
                    txt += "        \\path (5,2.5) node {\\tiny MC};\n"
                    txt += "        \\draw[->] (4,2) -- ++(1.5,0) -- ++(0,-3) -- ++(-27,0) -- ++(0,-3) -- ++(1.5,0);\n"
            else:
                txt += "        \\draw[-] (4,2) -- +(1,0);\n"
                txt += "        \\node at (8,2) {{\\tiny {}r Distinguisher}};\n".format(
                    r_dist
                )
                if o == 0:
                    txt += (
                        "        \\draw[->] (4,2) -- node[above] {\\tiny MC} +(2,0);\n"
                    )
                if o == 2:
                    txt += "        \\node at (12,2.5) {\\tiny MC};\n"
                    txt += "        \\draw[->] (11,2) -- ++(1.5,0) -- ++(0,-3) -- ++(-27,0) -- ++(0,-3) -- ++(1.5,0);\n"
            txt += "    \\end{scope}\n"
            block_cnt += 1
        txt += "  \\end{scope}\n"

    rnd += r_dist - 1
    rows = math.ceil((r_out * 2 + 1) / 4)
    # print(block_cnt)
    # print(g[7])
    for r in range(rows):
        txt += "  \\begin{{scope}}[yshift={}cm]\n".format(y_shift)
        y_shift += -6
        x_shift = 0
        for o in range(4):
            if block_cnt == 2 * (r_in + r_out + 1):
                txt += "    \\path (18,-1) node {{\\tiny $OBJ_{{K}}: {}\\ \\ \\ \\ \\ Cut_{{Keybridge}}: {}$}};".format(
                    key, keybridge
                )
                break
            if (o == 0 or o == 2) and block_cnt != 2 * (r_in + r_out) + 1:
                if o == 0:
                    txt += "    \\begin{scope}[xshift=-1cm,yshift=-1.5cm]\n"
                else:
                    txt += "    \\begin{scope}[xshift=33cm,yshift=3.5cm]\n"
                for j in range(8):
                    if g[block_cnt][j]["W"] == 1:
                        txt += "        \\fill[color=orange!40] ({},{}) rectangle +(1,1);\n".format(
                            XX[j], YY[j] - 2
                        )
                txt += "        \\draw (0,0) rectangle +(4,2);\n"
                txt += "        \\draw (0,1) -- +(4,0);\n"
                txt += "        \\draw (1,0) -- +(0,2);\n"
                txt += "        \\draw (2,0) -- +(0,2);\n"
                txt += "        \\draw (3,0) -- +(0,2);\n"
                if o == 0:
                    txt += "        \\draw[->] (4,1) -- ++(8,0) -- ++(0,1.5);\n"
                else:
                    txt += "        \\draw[->] (0,1) -- ++(-8,0) -- ++(0,-1.5);\n"
                tmp = get_per(rnd)
                for j in range(8):
                    txt += "        \\path ({},{}) node {{\\tiny \\texttt{{{}}}}};\n".format(
                        XX[j] + 0.5, YY[j] - 1.5, tmp[j]
                    )
                txt += "    \\end{scope}\n"

            x_shift += 6 + o % 2
            txt += "    \\begin{{scope}}[xshift={}cm]\n".format(x_shift)
            if o % 2 == 0:
                txt += "        \\path (2,4.5) node {{\\tiny Round {}}};\n".format(rnd)
                rnd += 1
            for j in range(16):
                if g[block_cnt][j]["W"] == 1:
                    txt += "        \\fill[color=blue!40] ({},{}) rectangle +(1,1);\n".format(
                        XX[j], YY[j]
                    )
            txt += "        \\draw (0,0) rectangle (4,4);\n"
            txt += "        \\draw (0,1) -- +(4,0);\n"
            txt += "        \\draw (0,2) -- +(4,0);\n"
            txt += "        \\draw (0,3) -- +(4,0);\n"
            txt += "        \\draw (1,0) -- +(0,4);\n"
            txt += "        \\draw (2,0) -- +(0,4);\n"
            txt += "        \\draw (3,0) -- +(0,4);\n"
            if block_cnt != 2 * (r_in + r_out) + 1:
                if o == 0:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny ART,SR};\n"
                elif o == 1:
                    txt += (
                        "        \\draw[->] (4,2) -- node[above] {\\tiny MC} +(2,0);\n"
                    )
                elif o == 2:
                    txt += "        \\draw[->] (4,2) --  +(3,0);\n"
                    txt += "        \\path (5.5,2.5) node {\\tiny SC,ART};\n"
                    txt += "        \\path (5.5,1.5) node {\\tiny SR};\n"
                else:
                    txt += "        \\path (5,2.5) node {\\tiny MC};\n"
                    txt += "        \\draw[->] (4,2) -- ++(1.5,0) -- ++(0,-3) -- ++(-27,0) -- ++(0,-3) -- ++(1.5,0);\n"
            txt += "    \\end{scope}\n"
            block_cnt += 1
        txt += "  \\end{scope}\n"

    txt += "\\end{tikzpicture}\n\\end{document}\n"
    # print(block_cnt)
    file = open("keyr_tikz", "w")
    file.write(txt)


if __name__ == "__main__":
    r_in = 3
    r_dist = 12
    r_out = 9
    lines = read_file()
    state_dist = []
    for i in range(2 * r_dist + 1):
        state_dist.append([])
        for j in range(16):
            state_dist[i].append({})
    state_dist = init(state_dist, lines, 1, "X", -1)
    state_dist = init(state_dist, lines, 1, "Y", -1)
    state_dist = init(state_dist, lines, 2, "Z", -2)
    state_dist = init(state_dist, lines, 2, "GZ", -2)
    state_dist = init(state_dist, lines, 1, "GT", -1)
    state_dist = init(state_dist, lines, 1, "T", -1)
    state_dist = init(state_dist, lines, 2, "V", -2)
    state_dist, deg, nonfull, keyseive = init_dist(state_dist, lines)
    # for i in range(2 * r_dist + 1):
    #     print("--------")
    #     for j in range(16):
    #         print(state_dist[i][j])
    write_dist(state_dist, r_dist, r_in, deg, nonfull, keyseive)

    state_keyr = []
    for i in range(2 * (r_in + r_out + 1)):
        state_keyr.append([])
        for j in range(16):
            state_keyr[i].append({})
    state_keyr = init(state_keyr, lines, 1, "M", -1)
    state_keyr = init(state_keyr, lines, 1, "W", 6)
    state_keyr, key, keybridge = init_keyr(state_keyr, lines)
    # for i in range(2 * (r_in + r_out + 1)):
    #     print("--------")
    #     for j in range(16):
    #         print(state_keyr[i][j])
    write_keyr(state_keyr, r_dist, r_in, r_out, key, keybridge)
