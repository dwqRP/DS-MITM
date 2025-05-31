from search import *

if __name__ == "__main__":
    for r_dist in range(8,13):
        for r_in in range(3,6):
            r_out = 23 - r_dist - r_in
            if Search_ds_mitm_attacks(r_dist, r_in, r_out, 54, 43, 0) == 2:
                print(r_dist, r_in, r_out)

            # r_out = 24 - r_dist - r_in
            # if Search_ds_mitm_attacks(r_dist, r_in, r_out, 58, 47, 0) == 2:
            #     print(r_dist, r_in, r_out)
