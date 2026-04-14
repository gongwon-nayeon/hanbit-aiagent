def fibonacci(n):
    """
    첫번째 항이 1인 피보나치 수열을 생성하는 함수
    n: 생성할 피보나치 수열의 항 개수
    """
    if n <= 0:
        return []
    elif n == 1:
        return [1]
    elif n == 2:
        return [1, 1]
    
    # 첫 두 항을 1, 1로 시작
    fib_sequence = [1, 1]
    
    # n개의 항을 생성
    for i in range(2, n):
        next_value = fib_sequence[i-1] + fib_sequence[i-2]
        fib_sequence.append(next_value)
    
    return fib_sequence


def main():
    # 피보나치 수열 테스트
    print("피보나치 수열 (첫 10개 항):")
    result = fibonacci(10)
    print(result)
    
    print("\n피보나치 수열 (첫 15개 항):")
    result = fibonacci(15)
    print(result)
    
    # 각 항별 출력
    print("\n각 항별 출력:")
    for i, value in enumerate(fibonacci(10), 1):
        print(f"F({i}) = {value}")


if __name__ == "__main__":
    main()