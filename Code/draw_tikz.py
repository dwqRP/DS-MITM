
a = [
    [[0, 1, 'n'], [0, 1, 'n'], [1, 1, 'n'], [1, 1, 'n']],
    [[0, 1, 'n'], [0, 1, 'n'], [0, 1, 'n'], [1, 1, 'n']],
    [[1, 1, 'n'], [0, 1, 'n'], [0, 1, 'n'], [0, 1, 'n']],
    [[0, 1, 'n'], [0, 1, 'n'], [0, 1, 'n'], [1, 1, 'n']]
]


for i in range(16):
    y = i % 4
    x = i // 4
    xa = y
    ya = 3 - x
    # if a[x][y][0] == 0 and a[x][y][1] == 1:
    #     str1 = "north west lines"
    # if a[x][y][0] == 1 and a[x][y][1] == 0:
    #     str1 = "north east lines"
    if a[x][y][0] == 1 and a[x][y][1] == 1:
        # str1 = "crosshatch"
        print("\\fill[color=blue!40] ({},{}) rectangle +(1,1);".format(xa,ya))
    # print("\\fill[pattern={}] ({},{}) rectangle +(1,1);".format(str1,xa,ya))