from search import *

if __name__ == "__main__":
    # for r_dist in range(8, 13):
    for r_dist in range(11, 12):
        for r_in in range(2, 5):
            r_out = 23 - r_dist - r_in
            if Search_ds_mitm_attacks(r_dist, r_in, r_out, 0, 0, 0) == 2:
                print("r_dist, r_in, r_out: ", r_dist, r_in, r_out)

            # r_out = 24 - r_dist - r_in
            # if Search_ds_mitm_attacks(r_dist, r_in, r_out, 58, 47, 0) == 2:
            #     print(r_dist, r_in, r_out)
