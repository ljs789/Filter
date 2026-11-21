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