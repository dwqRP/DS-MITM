# Key-bridging technique of AES

### Improved Single-Key Attacks on 8-Round AES-192 and AES-256

ASIACRYPT 2010

Orr Dunkelman, Nathan Keller , and Adi Shamir

<img src="C:\Users\17558\AppData\Roaming\Typora\typora-user-images\image-20250915172315879.png" alt="image-20250915172315879" style="zoom:53%;" />

They first propose the key-bridging technique.

### Automatic Search for Key-Bridging Technique: Applications to LBlock and TWINE

FSE 2016

Li Lin, Wenling Wu, and Yafei Zheng

They provide an algorithm for searching key-bridging technique on word-oriented and bit-oriented block ciphers.

Two phase:

- Knowledge-Propagation
- Relation-Derivation

They apply their tool to the impossible differential and multidimensional zero correlation linear attacks on 23-round LBlock, 23-round TWINE-80 and 25-round TWINE-128. 

"In INDOCRYPT 2012, Wu et al. presented an automatic search tool to search for the best impossible differential distinguishers. In this paper, we automatize the search of the best impossible differential attacks by combining Wu’s tool with our tool. Using Wu’s tool, we can get all distinguishers with certain rounds. Using our key-bridging tool, we can get all the key-bridges to reduce the complexity in key-sieving phase."

<img src="C:\Users\17558\AppData\Roaming\Typora\typora-user-images\image-20250915173714746.png" alt="image-20250915173714746" style="zoom:65%;" />

In their work, they apply their automatic search tool as an independent part and AES is not one of their target.

### Automatic Demirci-Selçuk Meet-in-the-Middle Attack on SKINNY with Key-Bridging

ICICS 2020

Qiu Chen, Danping Shi, Siwei Sun, and Lei Hu

They propose the CP/MILP model of key-bridging technique of SKINNY.

### Autoguess: A Tool for Finding Guess-and-Determine Attacks and Key Bridges

ACNS 2022

Hosein Hadipour and Maria Eichlseder

<img src="C:\Users\17558\AppData\Roaming\Typora\typora-user-images\image-20250916104804995.png" alt="image-20250916104804995" style="zoom:65%;" />