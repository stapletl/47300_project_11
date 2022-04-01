z = 'level p5-level-4'

print(z.strip().lower()[:5])
print(z.strip().lower()[6:])


boxes = [(1, 1), (5, 5), (7,7)]
targets = [(2, 2), (3, 4), (4,6)]

mdist = [[-1 for _ in boxes] for _ in boxes]

for i in range(len(boxes)):
    for j in range(len(targets)):
        xBox, yBox = boxes[i]
        xTarget, yTarget = targets[j]
        mdist[i][j] = abs(xBox - xTarget) + abs(yBox - yTarget)

sum = 0
for x in mdist:
    sum += min(x)
    i = x.index(min(x))
    for y in mdist:
        y.remove(y[i])


# sum = 0
# for dist in mdist:
#     # print('dist', dist)
#     # key = min(dist[1], key=dist[1].get)
#     sum = dist[1][min(dist[1])]

print('sum', sum)


# mdist = []

# for box in s.boxes():
#     boxDict = {}
#     for target in targets:
#         boxDict[target] = abs(box[0] - target[0]) + \
#                                 abs(box[1] - target[1])
#     mdist.append((box, boxDict))

# # print('mdist', mdist)

# sum = 0

# for dist in mdist:
#     # print('dist', dist)
#     # key = min(dist[1], key=dist[1].get)
#     sum = dist[1][min(dist[1])]

# print(sum)