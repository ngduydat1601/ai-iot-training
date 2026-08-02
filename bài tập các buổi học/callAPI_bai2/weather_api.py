import os
import time
import requests
from dotenv import load_dotenv
import pandas as pd

# ==========================
# Load API Key
# ==========================
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

CITY = "Hanoi"

URL = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# ==========================
# Cache
# ==========================

cache = {}

# ==========================
# Không cache
# ==========================

def get_weather():

    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    return response.json()

# ==========================
# Có cache
# ==========================

def get_weather_cache():

    if URL in cache:
        return cache[URL]

    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    data = response.json()

    cache[URL] = data

    return data

# ==========================
# Benchmark
# ==========================

def benchmark(func, total_requests):

    response_times = []

    success = 0
    errors = 0

    start_total = time.perf_counter()

    for i in range(total_requests):

        start = time.perf_counter()

        try:

            func()

            elapsed = (time.perf_counter() - start) * 1000

            success += 1

        except Exception:

            elapsed = None

            errors += 1

        response_times.append(elapsed)

    total_time = time.perf_counter() - start_total

    valid = [x for x in response_times if x is not None]

    avg = sum(valid) / len(valid) if valid else 0

    return {
        "response_times": response_times,
        "success": success,
        "errors": errors,
        "total_time": total_time,
        "avg_time": avg
    }

# ==========================
# Save Excel
# ==========================

def save_excel(no_cache, cache_result):

    EXCEL_OUTPUT = "benchmark_result_weather.xlsx"

    # ======================
    # Sheet 1: Chi tiết 100 requests
    # ======================
    ket_qua = []

    for i in range(100):
        ket_qua.append({
            "Request": i + 1,
            "Without Cache (ms)": no_cache["response_times"][i],
            "With Cache (ms)": cache_result["response_times"][i]
        })

    df_results = pd.DataFrame(ket_qua)

    # ======================
    # Sheet 2: Tổng quan
    # ======================
    tong_quan = pd.DataFrame({
        "Method": ["Without Cache", "With Cache"],
        "Success": [
            no_cache["success"],
            cache_result["success"]
        ],
        "Errors": [
            no_cache["errors"],
            cache_result["errors"]
        ],
        "Average Response Time (ms)": [
            round(no_cache["avg_time"], 2),
            round(cache_result["avg_time"], 2)
        ],
        "Total Time (s)": [
            round(no_cache["total_time"], 2),
            round(cache_result["total_time"], 2)
        ]
    })

    # ======================
    # Ghi ra Excel
    # ======================
    with pd.ExcelWriter(EXCEL_OUTPUT) as writer:

        df_results.to_excel(
            writer,
            sheet_name="Detail",
            index=False
        )

        tong_quan.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

    print("\n" + "=" * 50)
    print(f"Đã hoàn tất! File báo cáo lưu tại:\n{EXCEL_OUTPUT}")

    print("\n--- TỔNG QUAN HIỆU NĂNG ---")
    print(tong_quan.to_string(index=False))
# ==========================
# Main
# ==========================

if __name__ == "__main__":

    print("Benchmark WITHOUT cache...")

    result_no_cache = benchmark(get_weather,100)

    cache.clear()

    print("Benchmark WITH cache...")

    result_cache = benchmark(get_weather_cache,100)

    save_excel(result_no_cache,result_cache)

    print("\nDone!")

    print(f"Average without cache : {result_no_cache['avg_time']:.2f} ms")

    print(f"Average with cache    : {result_cache['avg_time']:.2f} ms")

    print("Excel saved: benchmark_result.xlsx")