import json
import time

EPSILON = 1e-9      # 두 점수가 이 값보다 차이가 작으면 같은 점수로 간주
REPEAT = 10          # 성능 측정을 위해 반복할 횟수


def normalize_label(raw):
    """ 라벨 정규화 함수"""
    text = str(raw).strip().lower()
    if text in ("+", "cross"):
        return "Cross"
    if text == "x":
        return "X"
    return None

def mac(pattern, filt):
    """ 같은 위치끼리 곱해 모두 더한 점수를 반환"""
    total = 0
    n = len(pattern)
    for i in range(n):         # 행 (가로줄) 번호
        for j in range(n):     # 열 (세로줄) 번호
            total += pattern[i][j] * filt[i][j]
    return total


def judge(score_a, score_b, label_a="A", label_b="B"):
    """ 두 점수를 비교하여 승패를 판단하는 함수"""
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    
    elif score_a > score_b:
        return label_a
 
    return label_b

def measure_ms(pattern, filt):
    """ 성능 측정을 위한 함수"""
    start = time.perf_counter()
    for _ in range(REPEAT):
        mac(pattern, filt)
    end = time.perf_counter()
    return (end - start) * 1000 / REPEAT


def is_square(matrix, n):
    """ 주어진 행렬이 n x n 정사각형인지 확인하는 함수"""
    if not isinstance(matrix, list) or len(matrix) != n:
        return False
    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            return False
    return True


def read_matrix(title, n=3):
    """ 사용자로부터 n x n 행렬을 입력받는 함수"""
    print(f"{title} ({n}줄 입력, 공백 구분)")
    matrix = []
    while len(matrix) < n:
        line = input()
        parts = line.split()
        if len(parts) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 입력해야 합니다.")
            continue
        try:
            row = [float(p) for p in parts]
        except ValueError:
            print(f"입력 형식 오류: '{line}'는 숫자가 아닙니다. 다시 시도하세요.")
            continue
        matrix.append(row)
    return matrix


def make_cross(n):
    """ n x n 크기의 십자 모양 필터를 생성하는 함수"""
    mid = n // 2
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == mid or j == mid:
                row.append(1.0)
            else:
                row.append(0.0)
        matrix.append(row)
    return matrix


def make_x(n):
    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j or i + j == n - 1:
                row.append(1.0)
            else:
                row.append(0.0)
        matrix.append(row)
    return matrix


def print_title(text):
    """ 제목을 출력하는 함수"""
    print("#" + "-" * 40)
    print("#" + text)
    print("#" + "-" * 40)


def print_performance(sizes):
    """ 성능 측정 결과를 출력하는 함수"""
    print_title("성능 분석 (평균/10회)")
    print(f"{'크기':<6}{'평균 시간(ms)':<12}{'연산 횟수'}")
    print("-" * 40)
    for n in sizes:
        ms = measure_ms(make_cross(n), make_x(n))
        print(f"{str(n) + 'x' + str(n):<8}{ms:<16.3f}{n * n}")

    print()


def run_user_mode():
    """ 사용자 모드 실행 함수"""
    print_title("[1] 필터 입력")
    filter_a = read_matrix("필터 A")
    filter_b = read_matrix("필터 B")
    print("필터 A, B 저장 완료\n")

    print_title("[2] 패턴 입력")
    pattern = read_matrix("패턴")
    print("패턴 저장 완료\n")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)
    ms = measure_ms(pattern, filter_a) + measure_ms(pattern, filter_b)

    print_title("[3] MAC 결과")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT}회): {ms:.3f}ms")
    result = judge(score_a, score_b, "A", "B")

    if result == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")

    else:
        print(f"판정: {result}")

    print()

    print_performance([3])


def load_filters(data):
    filters = {}
    for key, value in data.get("filters", {}).items():
        try:
            n = int(key.split("_")[1])
        except (IndexError, ValueError):
            print(f"x {key}: 키 형식을 해석할 수 없음(건너뜀)")
            continue

        normalized = {}
        for raw_label, matrix in value.items():
            label = normalize_label(raw_label)
            if label is not None:
                normalized[label] = matrix
        filters[n] = normalized
        print(f"✓ {key} 필터 로드 완료 ({', '.join(normalized.keys())})")

    print()
    return filters


def fail(reason):
    """실패 사유를 출력하고 (False, 사유)를 돌려준다."""
    print(f"FAIL: {reason}")
    return False, reason


def analyze_pattern(key, item, filters):
    """패턴 하나를 판정한다. 결과: (통과여부, 실패 사유)"""
    print(f"---{key}---")

    # (1) 키에서 크기 N 꺼내기 : "size_13_2" → 13

    try:
        n = int(key.split("_")[1])
    except (IndexError, ValueError):
        return fail("키 형식 오류(size_N_idx 형태가 아님)")

     # (2) 필요한 데이터가 다 있는지

    if n not in filters:
        return fail(f"size_{n} 필터가 없음")
    if "Cross" not in filters[n] or "X" not in filters[n]:
        return fail(f"size_{n} 필터에 Cross/X 중 하나가 없음")
    if not isinstance(item, dict) or "input" not in item or "expected"  not in item:
        return fail("input 또는 expected 항목이 없음")

    pattern = item["input"]
    cross_f = filters[n]["Cross"]
    x_f = filters[n]["X"]


     # (3) 크기 검증
    if not is_square(pattern, n):
        return fail(f"패턴 크기가 {n}x{n}이 아님")
    if not is_square(cross_f, n) or not is_square(x_f, n):
        return fail(f"필터 크기가 {n}x{n}이 아님")


    # (4) expected 정규화
    expected = normalize_label(item["expected"])
    if expected is None:
        return fail(f"알 수 없는 expected 값: {item['expected']}")

    # (5) MAC 연산 + 판정
    try:
        cross_score = mac(pattern, cross_f)
        x_score = mac(pattern, x_f)
    except TypeError:
        return fail("배열 안에 숫자가 아닌 값이 있음")

    result = judge(cross_score, x_score, "Cross", "X")
    print(f"Cross 점수: {cross_score}")
    print(f"X 점수: {x_score}")

    passed = (result == expected)
    mark = "PASS" if passed else "FAIL"
    print(f"판정: {result} | expected: {expected} | {mark}")

    if passed:
        return True, ""
    if result == "UNDECIDED":
        return fail("동점(UNDECIDED) 처리 규칙에 따라 FAIL")
    return fail(f"판정({result})과 expected({expected})가 다름")


def run_json_mode(path="data.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"{path} 파일을 찾을 수 없습니다. main.py와 같은 폴더에 두세요.")
        return
    except json.JSONDecodeError as e:
        print(f"{path} 파일이 올바른 JSON 형식이 아닙니다: {e}")
        return

    print_title("[1] 필터 로드")
    filters = load_filters(data)

    print_title("[2] 패턴 분석 (라벨 정규화 적용)")
    total = 0
    passed_count = 0
    failures = []
    for key, item in data.get("patterns", {}).items():
        total += 1
        passed, reason = analyze_pattern(key, item, filters)
        if passed:
            passed_count += 1
        else:
            failures.append((key, reason))

    print()

    print_performance([3, 5, 13, 25])

    print_title("[4] 결과 요약")
    print(f"총 테스트: {total}개")
    print(f"통과: {passed_count}개")
    print(f"실패: {len(failures)}개")
    if failures:
        print("\n실패 케이스:")
        for key, reason in failures:
            print(f"- {key}: {reason}")



# ===============================================================
# 보너스 1. 패턴 생성기
# ===============================================================
def read_size():
    """패턴 크기 N을 입력받는다 (3 이상의 홀수만 허용)"""
    while True:
        text = input("패턴 크기 N 입력 (3 이상 홀수, 예: 5): ").strip()
        try:
            n = int(text)
        except ValueError:
            print("입력 형식 오류: 정수를 입력하세요.")
            continue
        if n < 3 or n % 2 == 0:
            print("입력 형식 오류: 3 이상의 홀수를 입력하세요. (짝수는 가운데 칸이 없어 십자가가 한쪽으로 치우칩니다)")
            continue
        return n


def print_matrix(matrix):
    """2차원 배열을 0/1 모양으로 출력한다"""
    for row in matrix:
        print(" ".join(str(int(v)) for v in row))


def run_generator_mode():
    """보너스 1: N을 입력받아 십자가/X 패턴을 만들고, 그 패턴으로 판정과 성능 분석을 한다"""
    print_title("[1] 패턴 생성")
    n = read_size()
    cross = make_cross(n)
    x = make_x(n)
    print(f"\n{n}x{n} 십자가(Cross) 패턴")
    print_matrix(cross)
    print(f"\n{n}x{n} X 패턴")
    print_matrix(x)
    print()

    print_title("[2] 생성 패턴 판정 (필터도 생성 패턴 사용)")
    for name, pattern in (("Cross", cross), ("X", x)):
        cross_score = mac(pattern, cross)
        x_score = mac(pattern, x)
        result = judge(cross_score, x_score, "Cross", "X")
        mark = "PASS" if result == name else "FAIL"
        print(f"{name} 패턴 → Cross 점수: {cross_score}, X 점수: {x_score}, 판정: {result} | {mark}")
    print()

    print_performance([n])


# ===============================================================
# 보너스 2. 1차원 배열 최적화
# ===============================================================
BONUS_REPEAT = 1000   # 시간이 너무 짧아 비교가 흔들리지 않도록 더 많이 반복 (두 방식 동일)


def flatten(matrix):
    """2차원 배열을 한 줄(길이 N*N)로 편다"""
    flat = []
    for row in matrix:
        for value in row:
            flat.append(value)
    return flat


def mac_flat(flat_a, flat_b):
    """1차원 배열끼리 MAC 연산 (반복문 하나)"""
    total = 0.0
    for k in range(len(flat_a)):
        total += flat_a[k] * flat_b[k]
    return total


def measure_ms_with(func, a, b, repeat):
    """func(a, b)를 repeat번 실행한 평균 시간(ms)"""
    start = time.perf_counter()
    for _ in range(repeat):
        func(a, b)
    end = time.perf_counter()
    return (end - start) * 1000 / repeat


def run_optimize_mode():
    """보너스 2: 같은 입력, 같은 반복 횟수로 2차원 방식과 1차원 방식을 비교한다"""
    print_title(f"최적화 전/후 비교 (평균/{BONUS_REPEAT}회)")
    print(f"{'크기':<6}{'2차원(ms)':<10}{'1차원(ms)':<10}{'속도 비율':<6}{'점수 일치'}")
    print("-" * 52)
    for n in [3, 5, 13, 25]:
        pattern = make_cross(n)
        filt = make_x(n)
        flat_p = flatten(pattern)    # 펴는 시간은 측정에서 제외 (미리 1번만)
        flat_f = flatten(filt)

        ms_2d = measure_ms_with(mac, pattern, filt, BONUS_REPEAT)
        ms_1d = measure_ms_with(mac_flat, flat_p, flat_f, BONUS_REPEAT)
        same = abs(mac(pattern, filt) - mac_flat(flat_p, flat_f)) < EPSILON
        ratio = ms_2d / ms_1d if ms_1d > 0 else 0
        print(f"{str(n) + 'x' + str(n):<8}{ms_2d:<12.4f}{ms_1d:<12.4f}{ratio:<10.2f}{'O' if same else 'X'}")
    print()
    print("속도 비율 = 2차원 시간 / 1차원 시간 (1보다 크면 1차원이 더 빠름)")


def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    print("3. [보너스] 패턴 생성기")
    print("4. [보너스] 1차원 최적화 비교")
    while True:
        choice = input("선택: ").strip()
        if choice in ("1", "2", "3", "4"):
            break
        print("1~4 중 하나를 입력하세요.")
    print()
    if choice == "1":
        run_user_mode()
    elif choice == "2":
        run_json_mode()
    elif choice == "3":
        run_generator_mode()
    else:
        run_optimize_mode()


if __name__ == "__main__":
    main()