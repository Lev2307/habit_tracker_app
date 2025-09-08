g = [_ for _ in range(1, 101)]
blocks_7 = [[] for _ in range((101 // 7)+1)]
for i in range(len(g)):
    print(i//7, g[i])
    blocks_7[(i // 7)].append(g[i])
print(blocks_7)
print(len(blocks_7))