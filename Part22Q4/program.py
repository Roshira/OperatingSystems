import random
from collections import deque

# --- 1. Генерація трейсу з локальністю ---
def generate_locality_trace(max_page, length, hot_ratio=0.2, hot_prob=0.8):
    """
    Генерує трейс, де hot_prob (напр. 80%) звернень йдуть до 
    hot_ratio (напр. 20%) сторінок.
    """
    trace = []
    hot_boundary = int(max_page * hot_ratio)
    
    for _ in range(length):
        if random.random() < hot_prob:
            # Звернення до "гарячої" сторінки
            page = random.randint(0, hot_boundary)
        else:
            # Звернення до "холодної" сторінки
            page = random.randint(hot_boundary + 1, max_page)
        trace.append(page)
    return trace

# --- 2. Алгоритми заміщення ---

def solve_lru(trace, cache_size):
    cache = [] # Використовуємо список як стек: кінець - недавно використані
    hits = 0
    for page in trace:
        if page in cache:
            hits += 1
            cache.remove(page) # Переміщуємо в кінець (оновлюємо свіжість)
            cache.append(page)
        else:
            if len(cache) >= cache_size:
                cache.pop(0) # Видаляємо найстаріший (початок списку)
            cache.append(page)
    return (hits / len(trace)) * 100

def solve_rand(trace, cache_size):
    cache = []
    hits = 0
    for page in trace:
        if page in cache:
            hits += 1
        else:
            if len(cache) >= cache_size:
                evict_idx = random.randint(0, len(cache) - 1)
                cache.pop(evict_idx)
            cache.append(page)
    return (hits / len(trace)) * 100

def solve_clock(trace, cache_size, clock_bits=1):
    # cache зберігає [page_id, use_bits]
    cache = [] 
    hits = 0
    hand = 0 # Стрілка годинника
    
    for page in trace:
        # Перевірка на влучання (HIT)
        found = False
        for i in range(len(cache)):
            if cache[i][0] == page:
                hits += 1
                cache[i][1] = clock_bits # Скидаємо біти використання на максимум
                found = True
                break
        
        if not found:
            # MISS - треба вставити сторінку
            if len(cache) < cache_size:
                cache.append([page, clock_bits])
            else:
                # Алгоритм CLOCK: шукаємо жертву
                while True:
                    # Якщо стрілка вийшла за межі, повертаємо на початок
                    if hand >= len(cache):
                        hand = 0
                    
                    if cache[hand][1] > 0:
                        # Даємо другий (або n-й) шанс
                        cache[hand][1] -= 1
                        hand += 1
                    else:
                        # Знайшли жертву (bits == 0)
                        cache[hand] = [page, clock_bits]
                        hand += 1
                        break
    return (hits / len(trace)) * 100

# --- 3. Запуск експерименту ---

# Параметри
TRACE_LEN = 10000
MAX_PAGE = 100
CACHE_SIZE = 25  # Маленький кеш, щоб було багато витіснень

print(f"Генерація трейсу ({TRACE_LEN} звернень, {MAX_PAGE} сторінок, кеш={CACHE_SIZE})...")
print("Тип: 80% звернень до 20% адресного простору (локальність).")

trace = generate_locality_trace(MAX_PAGE, TRACE_LEN)

# Розрахунки
lru_hit = solve_lru(trace, cache_size=CACHE_SIZE)
rand_hit = solve_rand(trace, cache_size=CACHE_SIZE)
clock_1_hit = solve_clock(trace, cache_size=CACHE_SIZE, clock_bits=1)
clock_2_hit = solve_clock(trace, cache_size=CACHE_SIZE, clock_bits=2)
clock_3_hit = solve_clock(trace, cache_size=CACHE_SIZE, clock_bits=3)

# Вивід результатів
print("-" * 30)
print(f"LRU Hit Rate:        {lru_hit:.2f}%")
print(f"RAND Hit Rate:       {rand_hit:.2f}%")
print(f"CLOCK (1 bit) Hit:   {clock_1_hit:.2f}%")
print(f"CLOCK (2 bits) Hit:  {clock_2_hit:.2f}%")
print(f"CLOCK (3 bits) Hit:  {clock_3_hit:.2f}%")
print("-" * 30)

print("\nВисновки:")
diff = lru_hit - rand_hit
print(f"1. LRU краще за RAND на {diff:.2f}%.")
if clock_1_hit >= lru_hit - 1:
    print("2. CLOCK працює майже так само добре, як LRU.")
else:
    print("2. CLOCK трохи гірше LRU, але краще RAND.")
