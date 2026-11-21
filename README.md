pattern = [
    [0, 1, 0],   # 0번 행
    [1, 1, 1],   # 1번 행
    [0, 1, 0],   # 2번 행
]
print(pattern[1][2])   # 1번 행, 2번 열 값 읽기 -> 1
pattern[0][0] = 5      # 0번 행, 0번 열에 5 저장하기
print(len(pattern))    # 행 개수 -> 3
print(len(pattern[0])) # 0번 행의 열 개수 -> 3
실행결과
1
[[5, 1, 0], [1, 1, 1], [0, 1, 0]]
3
3


def make_matrix(n, fill=0):
    return [[fill] * n for _ in range(n)]           #for _ in range(n)이 n번 돌면서 매번 새 행 [fill] * n을 만듬. _는 "반복 번호는 쓰지 않는다"는 뜻


n = 5
m = [[0] * n for _ in range(n)]   # 5x5, 전부 0 
m[2][2] = 1                       # 가운데 칸만 1
for row in m:
    print(row)
실행결과
[0, 0, 0, 0, 0]
[0, 0, 0, 0, 0]
[0, 0, 1, 0, 0]
[0, 0, 0, 0, 0]
[0, 0, 0, 0, 0]


bad = [[0] * 3] * 3
bad[0][0] = 1
print(bad)
실행결과
[[1, 0, 0], [1, 0, 0], [1, 0, 0]]   # 세 줄이 다 바뀜!

def make_matrix(n, fill=0):
    return [[fill] * n for _ in range(n)]

def print_matrix(matrix):
    for row in matrix:
        print("  " + " ".join(f"{v:g}" for v in row))

m = make_matrix(3)
m[1][1] = 1
print_matrix(m)
실행결과  
  0 0 0
  0 1 0
  0 0 0


  def mac(pattern, filt):
    n = len(pattern)
    total = 0.0
    for i in range(n):          # 행
        for j in range(n):      # 열
            total += pattern[i][j] * filt[i][j]
    return total