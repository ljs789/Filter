"""
Mini NPU Simulator
==================
패턴(그림)과 필터(기준 그림)를 같은 위치끼리 곱하고 모두 더해서(MAC)
그림이 십자가(Cross)인지 X인지 판정하는 프로그램입니다.

- 모드 1: 3x3 필터 A, B와 패턴을 직접 입력받아 판정
- 모드 2: data.json 의 필터/패턴을 읽어 일괄 판정 + PASS/FAIL + 성능 분석
- 모드 3: (보너스) 크기 N을 입력하면 Cross/X 패턴을 자동 생성

외부 라이브러리 없이 표준 라이브러리(json, os, sys, time)만 사용합니다.
실행: python main.py
      python main.py test_error_data.json   (모드 2에서 다른 JSON 파일로 시험할 때)
"""

import json
import os
import sys
import time


# ============================================================
# 0. 설정값 (상수)
#    여러 곳에서 쓰는 값은 맨 위에 한 번만 정의해 두면
#    나중에 바꿀 때 이 한 줄만 고치면 됩니다.
# ============================================================
EPSILON = 1e-9        # 두 점수 차이가 이보다 작으면 '동점'으로 본다
REPEAT = 10           # 성능 측정 반복 횟수 (과제 최소 기준: 10회)
PERF_SIZES = [3, 5, 13, 25]   # 성능 분석에 사용할 크기들

# data.json 은 main.py 와 같은 폴더에 있다고 가정합니다.
# __file__ 기준으로 경로를 만들면, 다른 폴더에서 실행해도 파일을 찾습니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data.json")

# 프로그램 내부에서 쓰는 "표준 라벨" (이 세 가지 외의 글자는 내부에서 쓰지 않는다)
CROSS = "Cross"
X = "X"
UNDECIDED = "UNDECIDED"

# 여러 표기법 -> 표준 라벨 변환표 (소문자로 바꾼 뒤 찾는다)
#   expected 값:  '+'      -> Cross,  'x' -> X
#   filter 키  :  'cross'  -> Cross,  'x' -> X
LABEL_ALIASES = {
    "+": CROSS,
    "cross": CROSS,
    "x": X,
}

LINE = "#" + "-" * 40


def print_section(title):
    """콘솔에 구분선과 섹션 제목을 출력한다."""
    print()
    print(LINE)
    print("# " + title)
    print(LINE)


# ============================================================
# 1. 데이터 구조: n x n 2차원 리스트
#    matrix[행][열] 로 특정 위치 값을 읽고(read) 쓸(write) 수 있다.
# ============================================================
def make_matrix(n, fill=0):
    """n x n 크기의 2차원 리스트를 만든다.

    주의: [[0] * n] * n 으로 만들면 모든 행이 '같은 리스트'를 가리켜서
    한 칸을 바꾸면 모든 행이 같이 바뀐다. 그래서 행마다 새 리스트를 만든다.
    """
    return [[fill] * n for _ in range(n)]


def print_matrix(matrix):
    """2차원 리스트를 보기 좋게 한 줄씩 출력한다."""
    for row in matrix:
        # :g 형식은 1.0 -> 1, 0.5 -> 0.5 처럼 불필요한 .0 을 빼고 보여준다.
        print("  " + " ".join(f"{v:g}" for v in row))


# ============================================================
# 2. MAC 연산 (Multiply-Accumulate)
#    같은 위치끼리 곱하고(Multiply) 그 값을 계속 더한다(Accumulate).
#    NumPy 없이 반복문으로 직접 구현한다.
# ============================================================
def mac(pattern, filt):
    """패턴과 필터의 MAC 점수를 계산해 float 로 반환한다.

    filter 는 파이썬 내장 함수 이름이라서 변수 이름은 filt 로 쓴다.
    """
    n = len(pattern)
    total = 0.0
    for i in range(n):          # 행
        for j in range(n):      # 열
            total += pattern[i][j] * filt[i][j]
    return total


# ============================================================
# 3. 점수 비교 (epsilon 기반 동점 처리)
# ============================================================
def compare_scores(score_a, score_b, eps=EPSILON):
    """두 점수를 비교해 'A', 'B', 'TIE' 중 하나를 반환한다.

    부동소수점은 0.1 + 0.2 가 0.30000000000000004 가 되는 것처럼
    아주 작은 오차가 생긴다. 그래서 == 로 비교하지 않고
    '차이가 eps 보다 작으면 같은 것'으로 본다.
    """
    if abs(score_a - score_b) < eps:
        return "TIE"
    if score_a > score_b:
        return "A"
    return "B"


# ============================================================
# 4. 성능 측정
# ============================================================
def measure_mac_ms(pattern, filt, repeat=REPEAT):
    """mac() 를 repeat 번 실행해서 1회 평균 시간(ms)을 반환한다.

    - 입력/출력/파일 읽기 시간은 빼고 '연산 함수 호출 구간'만 잰다.
    - time.perf_counter() 는 짧은 시간을 재기에 가장 정밀한 시계다.
    """
    mac(pattern, filt)                 # 워밍업 1회 (첫 실행의 준비 시간 제외)
    start = time.perf_counter()
    for _ in range(repeat):
        mac(pattern, filt)
    end = time.perf_counter()
    return (end - start) * 1000 / repeat   # 초 -> ms, 그리고 1회 평균


def print_perf_table(rows):
    """rows: [(n, 평균ms), ...] 를 '크기 / 평균 시간 / 연산 횟수' 표로 출력한다.

    한글은 화면에서 영문 2글자 폭을 차지해서 f-string 정렬이 어긋난다.
    그래서 머리글은 공백을 직접 맞춘 문자열로 쓴다.
    """
    print("크기(NxN)      평균 시간(ms)  연산 횟수(N^2)")
    print("-" * 44)
    for n, avg_ms in rows:
        size_text = f"{n}x{n}"
        print(f"{size_text:<12}{avg_ms:>16.5f}{n * n:>16}")


# ============================================================
# 5. 패턴 생성기 (보너스 2) - 성능 분석과 모드 3 에서 재사용
# ============================================================
def generate_cross(n):
    """n x n 십자가 패턴: 가운데 행과 가운데 열이 1."""
    matrix = make_matrix(n)
    mid = n // 2
    for i in range(n):
        matrix[mid][i] = 1      # 가운데 행
        matrix[i][mid] = 1      # 가운데 열
    return matrix


def generate_x(n):
    """n x n X 패턴: 두 대각선이 1."""
    matrix = make_matrix(n)
    for i in range(n):
        matrix[i][i] = 1            # 왼쪽 위 -> 오른쪽 아래 대각선
        matrix[i][n - 1 - i] = 1    # 오른쪽 위 -> 왼쪽 아래 대각선
    return matrix


# ============================================================
# 6. 1차원 배열 최적화 (보너스 1)
# ============================================================
def flatten(matrix):
    """2차원 리스트를 길이 N^2 의 1차원 리스트로 펼친다."""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(flat_pattern, flat_filter):
    """1차원 리스트끼리 MAC. 반복문이 하나라서 인덱스 접근이 단순하다."""
    total = 0.0
    for k in range(len(flat_pattern)):
        total += flat_pattern[k] * flat_filter[k]
    return total


def measure_mac_flat_ms(flat_pattern, flat_filter, repeat=REPEAT):
    """mac_flat() 의 1회 평균 시간(ms). 펼치는 시간은 측정에서 뺀다."""
    mac_flat(flat_pattern, flat_filter)
    start = time.perf_counter()
    for _ in range(repeat):
        mac_flat(flat_pattern, flat_filter)
    end = time.perf_counter()
    return (end - start) * 1000 / repeat


def run_performance(sizes):
    """크기별로 MAC 평균 시간을 재서 표로 출력하고, 측정 결과를 반환한다."""
    rows = []
    for n in sizes:
        # 연산 시간은 '값'이 아니라 '크기'에 따라 달라지므로
        # 모든 크기에 같은 종류의 입력(생성된 십자가)을 써서 공정하게 비교한다.
        pattern = generate_cross(n)
        filt = generate_cross(n)
        rows.append((n, measure_mac_ms(pattern, filt)))
    print_perf_table(rows)
    return rows


def run_flat_comparison(sizes):
    """(보너스) 2차원 MAC 과 1차원 MAC 의 시간을 같은 입력, 같은 반복 횟수로 비교한다."""
    print("크기(NxN)        2차원(ms)     1차원(ms)")
    print("-" * 40)
    for n in sizes:
        pattern = generate_cross(n)
        filt = generate_cross(n)
        t2d = measure_mac_ms(pattern, filt)
        t1d = measure_mac_flat_ms(flatten(pattern), flatten(filt))
        size_text = f"{n}x{n}"
        print(f"{size_text:<12}{t2d:>14.5f}{t1d:>14.5f}")


# ============================================================
# 7. 모드 1: 사용자 입력 (3x3)
# ============================================================
def parse_row(line, n):
    """한 줄 문자열을 숫자 n개의 리스트로 바꾼다.

    성공하면 (리스트, None), 실패하면 (None, 오류 메시지)를 반환한다.
    """
    parts = line.split()        # 공백(스페이스/탭 여러 개 포함) 기준으로 자르기
    if len(parts) != n:
        return None, f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요. (입력된 개수: {len(parts)})"
    row = []
    for text in parts:
        try:
            row.append(float(text))     # '1', '0.5', '-2' 모두 숫자로 변환
        except ValueError:
            return None, f"입력 형식 오류: '{text}' 는 숫자가 아닙니다. 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요."
    return row, None


def read_matrix(title, n=3):
    """콘솔에서 n 줄을 입력받아 n x n 2차원 리스트를 만든다.

    잘못된 줄은 저장하지 않고 안내 문구를 출력한 뒤 그 줄을 다시 입력받는다.
    올바른 줄이 정확히 n 개 모일 때까지 반복하므로 행 수도 항상 n 이 된다.
    """
    print(f"{title} ({n}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < n:
        line = input()
        row, error = parse_row(line, n)
        if error:
            print(error)
            print(f"  -> {len(matrix) + 1}번째 줄을 다시 입력하세요.")
            continue
        matrix.append(row)
    return matrix


def run_mode_user():
    n = 3

    print_section("[1] 필터 입력")
    filter_a = read_matrix("필터 A", n)
    print()
    filter_b = read_matrix("필터 B", n)

    # 저장 확인: 입력한 값이 2차원 리스트에 제대로 들어갔는지 보여준다.
    print()
    print("[저장 완료] 필터 A")
    print_matrix(filter_a)
    print("[저장 완료] 필터 B")
    print_matrix(filter_b)

    print_section("[2] 패턴 입력")
    pattern = read_matrix("패턴", n)

    print_section("[3] MAC 결과")
    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    # 연산 시간: 필터 A 와 B 각각의 MAC 1회 평균을 재서 둘의 평균을 낸다.
    avg_ms = (measure_mac_ms(pattern, filter_a) + measure_mac_ms(pattern, filter_b)) / 2

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT}회): {avg_ms:.5f} ms")

    result = compare_scores(score_a, score_b)
    if result == "TIE":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {result}")

    print_section(f"[4] 성능 분석 (3x3, 평균/{REPEAT}회)")
    print_perf_table([(n, avg_ms)])


# ============================================================
# 8. 모드 2: data.json 분석
# ============================================================
def normalize_label(raw):
    """'+', 'x', 'cross', 'X', 'Cross' 같은 여러 표기를 표준 라벨(Cross/X)로 바꾼다.

    알 수 없는 값이면 None 을 반환한다.
    """
    if not isinstance(raw, str):
        return None
    return LABEL_ALIASES.get(raw.strip().lower())


def size_from_key(key):
    """'size_13' 이나 'size_13_2' 같은 키에서 크기 13 을 꺼낸다. 형식이 틀리면 None."""
    parts = key.split("_")              # 'size_13_2' -> ['size', '13', '2']
    if len(parts) < 2 or parts[0] != "size" or not parts[1].isdigit():
        return None
    return int(parts[1])


def validate_matrix(matrix, n):
    """matrix 가 n x n 숫자 2차원 리스트인지 검사한다.

    문제가 없으면 None, 문제가 있으면 원인을 설명하는 문자열을 반환한다.
    (오류를 '예외로 터뜨리지 않고' 메시지로 돌려주기 때문에 프로그램이 멈추지 않는다.)
    """
    if not isinstance(matrix, list):
        return "2차원 리스트가 아닙니다"
    if len(matrix) != n:
        return f"행 수 불일치 (필요: {n}, 실제: {len(matrix)})"
    for i, row in enumerate(matrix):
        if not isinstance(row, list):
            return f"{i + 1}번째 행이 리스트가 아닙니다"
        if len(row) != n:
            return f"{i + 1}번째 행의 열 수 불일치 (필요: {n}, 실제: {len(row)})"
        for value in row:
            if not isinstance(value, (int, float)):
                return f"{i + 1}번째 행에 숫자가 아닌 값이 있습니다: {value!r}"
    return None


def load_json(path):
    """JSON 파일을 읽어 딕셔너리로 반환한다. 실패하면 이유를 출력하고 None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[오류] 파일을 찾을 수 없습니다: {path}")
    except json.JSONDecodeError as e:
        print(f"[오류] JSON 형식이 올바르지 않습니다: {e}")
    return None


def load_filters(data):
    """data['filters'] 를 읽어 {크기: {'Cross': 행렬, 'X': 행렬}} 형태로 정리한다."""
    filters = {}
    raw_filters = data.get("filters")
    if not isinstance(raw_filters, dict):
        print("[오류] data.json 에 'filters' 항목이 없거나 형식이 다릅니다.")
        return filters

    for size_key, group in raw_filters.items():     # 예: 'size_5', {'cross': [...], 'x': [...]}
        n = size_from_key(size_key)
        if n is None or not isinstance(group, dict):
            print(f"[오류] {size_key}: 'size_N' 형식의 키와 필터 묶음이 필요합니다.")
            continue

        normalized = {}
        for raw_label, matrix in group.items():
            label = normalize_label(raw_label)      # 'cross' -> 'Cross', 'x' -> 'X'
            if label is None:
                print(f"[경고] {size_key}: 알 수 없는 필터 키 '{raw_label}' 는 건너뜁니다.")
                continue
            error = validate_matrix(matrix, n)
            if error:
                print(f"[오류] {size_key} {label} 필터: {error}")
                continue
            normalized[label] = matrix

        if CROSS in normalized and X in normalized:
            filters[n] = normalized
            print(f"[완료] {size_key} 필터 로드 (Cross, X)")
        else:
            print(f"[오류] {size_key}: Cross 와 X 필터가 모두 있어야 합니다. 이 크기의 패턴은 FAIL 처리됩니다.")
    return filters


def analyze_case(case_id, case, filters):
    """패턴 한 개를 검증 -> MAC -> 판정 -> PASS/FAIL 하고 결과 딕셔너리를 반환한다.

    어떤 문제가 생겨도 예외로 멈추지 않고 '이 케이스만 FAIL' 로 처리한다.
    """
    print(f"--- {case_id} ---")

    def fail(reason):
        print(f"FAIL: {reason}")
        return {"id": case_id, "passed": False, "reason": reason}

    # (1) 키에서 크기 N 추출
    n = size_from_key(case_id)
    if n is None:
        return fail("키 형식 오류 ('size_N_번호' 형식이 아님)")
    if not isinstance(case, dict):
        return fail("케이스 형식 오류 (input/expected 를 가진 객체가 아님)")

    # (2) 해당 크기의 필터가 있는지
    if n not in filters:
        return fail(f"size_{n} 필터가 없거나 로드에 실패함")

    # (3) 패턴 크기/값 검증
    pattern = case.get("input")
    error = validate_matrix(pattern, n)
    if error:
        return fail(f"패턴 스키마 오류 - {error}")

    # (4) MAC 연산
    cross_score = mac(pattern, filters[n][CROSS])
    x_score = mac(pattern, filters[n][X])

    # (5) 판정 (A = Cross 필터, B = X 필터)
    result = compare_scores(cross_score, x_score)
    decision = {"A": CROSS, "B": X, "TIE": UNDECIDED}[result]

    # (6) expected 라벨 정규화 후 비교
    raw_expected = case.get("expected")
    expected = normalize_label(raw_expected)

    print(f"Cross 점수: {cross_score}")
    print(f"X 점수: {x_score}")
    shown_expected = expected if expected else repr(raw_expected)
    line = f"판정: {decision} | expected: {shown_expected}"

    if expected is None:
        print(line + " | FAIL")
        return {"id": case_id, "passed": False,
                "reason": f"expected 라벨을 해석할 수 없음 ({raw_expected!r})"}
    if decision == UNDECIDED:
        print(line + " | FAIL (동점 규칙)")
        return {"id": case_id, "passed": False,
                "reason": f"동점(UNDECIDED) 처리 규칙에 따라 FAIL (|Cross-X| < {EPSILON})"}
    if decision != expected:
        print(line + " | FAIL")
        return {"id": case_id, "passed": False,
                "reason": f"판정 {decision} 이(가) expected {expected} 와 다름"}

    print(line + " | PASS")
    return {"id": case_id, "passed": True, "reason": ""}


def print_summary(results):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    if failed:
        print()
        print("실패 케이스:")
        for r in results:
            if not r["passed"]:
                print(f"- {r['id']}: {r['reason']}")
    else:
        print("실패 케이스 없음 (라벨 정규화 + epsilon 비교 정책 적용)")


def get_data_path():
    """실행할 때 파일 경로를 적었으면 그 파일을, 아니면 main.py 옆의 data.json 을 쓴다.

    예) python main.py                      -> data.json
        python main.py test_error_data.json -> test_error_data.json
    sys.argv 는 실행 명령의 단어 목록이다. sys.argv[0] 은 'main.py' 자기 자신.
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    return DATA_PATH


def run_mode_json():
    print_section("[1] 필터 로드")
    path = get_data_path()
    print(f"파일: {os.path.basename(path)}")
    data = load_json(path)
    if not isinstance(data, dict):
        print("data.json 을 읽지 못해 분석을 종료합니다.")
        return
    filters = load_filters(data)

    print_section("[2] 패턴 분석 (라벨 정규화 적용)")
    patterns = data.get("patterns")
    results = []
    if not isinstance(patterns, dict):
        print("[오류] data.json 에 'patterns' 항목이 없거나 형식이 다릅니다.")
    else:
        for case_id, case in patterns.items():
            results.append(analyze_case(case_id, case, filters))

    print_section(f"[3] 성능 분석 (평균/{REPEAT}회)")
    run_performance(PERF_SIZES)
    print()
    print(f"[보너스] 2차원 vs 1차원 배열 MAC 비교 (평균/{REPEAT}회)")
    run_flat_comparison(PERF_SIZES)

    print_section("[4] 결과 요약")
    print_summary(results)


# ============================================================
# 9. 모드 3 (보너스): 패턴 생성기
# ============================================================
def read_odd_size():
    """3 이상의 홀수 N 을 입력받는다. (짝수는 '가운데' 줄이 없어서 십자가가 대칭이 안 됨)"""
    while True:
        text = input("크기 N (3 이상의 홀수): ").strip()
        if text.isdigit() and int(text) >= 3 and int(text) % 2 == 1:
            return int(text)
        print("입력 오류: 3 이상의 홀수를 입력하세요. (예: 3, 5, 13, 25)")


def run_mode_generator():
    print_section("[1] 크기 입력")
    n = read_odd_size()

    cross = generate_cross(n)
    x_pattern = generate_x(n)

    print_section(f"[2] 생성된 {n}x{n} 패턴")
    print("Cross:")
    print_matrix(cross)
    print("X:")
    print_matrix(x_pattern)

    # 생성된 패턴을 필터로도 재사용해서 MAC 판정을 확인한다.
    print_section("[3] 생성 패턴으로 MAC 판정")
    for name, pattern in (("Cross 패턴", cross), ("X 패턴", x_pattern)):
        cross_score = mac(pattern, cross)
        x_score = mac(pattern, x_pattern)
        decision = {"A": CROSS, "B": X, "TIE": UNDECIDED}[compare_scores(cross_score, x_score)]
        print(f"{name}: Cross 점수 {cross_score}, X 점수 {x_score} -> 판정 {decision}")

    print_section(f"[4] 성능 분석 ({n}x{n}, 평균/{REPEAT}회)")
    run_performance([n])


# ============================================================
# 10. 프로그램 시작점
# ============================================================
def choose_mode():
    """1, 2, 3 중 하나가 입력될 때까지 반복해서 묻는다."""
    while True:
        print()
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 패턴 생성기 (보너스)")
        choice = input("선택: ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("입력 오류: 1, 2, 3 중 하나를 입력하세요.")


def main():
    print("=== Mini NPU Simulator ===")
    mode = choose_mode()
    if mode == "1":
        run_mode_user()
    elif mode == "2":
        run_mode_json()
    else:
        run_mode_generator()


# 이 파일을 직접 실행했을 때만 main() 을 부른다.
# (다른 파일에서 import 할 때는 자동 실행되지 않는다.)
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C 를 누르거나 입력이 끝나도 에러 메시지 대신 깔끔하게 종료
        print("\n프로그램을 종료합니다.")
