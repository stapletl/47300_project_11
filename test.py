boxes = [(1, 1), (5, 5)]
targets = [(2, 2), (3, 4)]

mdist = []

for box in boxes:
    boxDict = {}
    for target in targets:
        boxDict[target] = abs(box[0] - target[0]) + abs(box[1] - target[1])
    mdist.append((box, boxDict))

print('mdist', mdist)

sum = 0
for dist in mdist:
    print('dist', dist)
    sum += min(dist[1], key=dist[1].get)

