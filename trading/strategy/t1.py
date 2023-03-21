import time
bar2 = '5m'


t = int(bar2[:-1]) * 60 if "m" in bar2 else int(bar2[:-1]) * 60 * 60

print(t)

for i in range(t // 5):

    print(i)