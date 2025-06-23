PT = [9,15,8,13,10,14,12,11,0,1,2,3,4,5,6,7]

res = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

for i in range(20):
    print(res[:8])
    tmp = []
    for j in range(16):
        tmp.append(res[j])
    for j in range(16):
        res[j]=tmp[PT[j]]