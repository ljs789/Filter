pattern = [
    [0, 1, 0],
    [1, 1, 1],
    [0, 1, 0],
]

print(pattern[1][2])     # 1번 줄의 2번 칸 읽기
pattern[0][0] = 5        # 0번 줄의 0번 칸을 5로 바꾸기
print(pattern)           # 전체 확인
print(len(pattern))      # 줄 개수
print(len(pattern[0]))   # 0번 줄의 칸 개수
=1
[[5, 1, 0], [1, 1, 1], [0, 1, 0]]
3
3


n = 5
m = [[0] * n for _ in range(n)]   # 5x5, 전부 0 
m[2][2] = 1                       # 가운데 칸만 1
for row in m:
    print(row)
=[0, 0, 0, 0, 0]
[0, 0, 0, 0, 0]
[0, 0, 1, 0, 0]
[0, 0, 0, 0, 0]
[0, 0, 0, 0, 0]


bad = [[0] * 3] * 3
bad[0][0] = 1
print(bad)
=[[1, 0, 0], [1, 0, 0], [1, 0, 0]]

def make_matrix(n, fill=0):
    return [[fill] * n for _ in range(n)]

def print_matrix(matrix):
    for row in matrix:
        print("  " + " ".join(f"{v:g}" for v in row))

m = make_matrix(3)
m[1][1] = 1
print_matrix(m)
= 0 0 0
  0 1 0
  0 0 0

실행결과
PS C:\Users\lghyh\Desktop\코딩\Filter> python practice.py
  0 0 0
  0 1 0
  0 0 0