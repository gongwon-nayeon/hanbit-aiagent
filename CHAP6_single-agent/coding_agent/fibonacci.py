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
    
    # 나머지 항들을 계산
    for i in range(2, n):
        next_num = fib_sequence[i-1] + fib_sequence[i-2]
        fib_sequence.append(next_num)
    
    return fib_sequence

# 메인 실행 부분
if __name__ == "__main__":
    # 피보나치 수열 출력 테스트
    print("피보나치 수열 (첫 10개 항):")
    result = fibonacci(10)
    print(result)
    
    print("\n각 항을 개별적으로 출력:")
    for i, num in enumerate(result, 1):
        print(f"{i}번째 항: {num}")
    
    # 더 많은 항 테스트
    print("\n피보나치 수열 (첫 15개 항):")
    print(fibonacci(15))