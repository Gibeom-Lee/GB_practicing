"""1-1 노트북의 CSV 처리 함수와 Windows/Jupyter용 프로세스 실행기."""

import glob
import os
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from time import perf_counter

import numpy as np
import pandas as pd


# 기존 파싱 동작 유지: 혼합 구분자, 불량 라인 건너뛰기, UTF-8 BOM.
READ_OPTS = dict(
    engine="python",
    sep=r"[,\t;]+",
    on_bad_lines="skip",
    encoding="utf-8-sig",
    header=None,
)

_non_numeric_re = re.compile(r"[A-Za-z가-힣\"']")


def fast_already_processed_check(path: str, sample_bytes: int = 4096) -> bool:
    """파일 앞부분에 헤더 같은 텍스트가 없으면 이미 처리된 것으로 추정."""
    try:
        with open(path, "rb") as f:
            head = f.read(sample_bytes)
        try:
            s = head.decode("utf-8-sig", errors="ignore")
        except Exception:
            s = head.decode(errors="ignore")
        return _non_numeric_re.search(s) is None
    except Exception:
        return False


def process_one_csv(file_path: str) -> tuple[str, str | None]:
    """기존 방식으로 파일을 처리하고 결과 및 파일명 변경 메시지를 반환."""
    rename_message = None
    try:
        # 파일명 공백 → 언더바.
        dir_name, file_name = os.path.split(file_path)
        new_file_name = file_name.replace(" ", "_")
        new_file_path = os.path.join(dir_name, new_file_name)
        if new_file_name != file_name:
            os.replace(file_path, new_file_path)
            file_path = new_file_path
            rename_message = f"[rename] {file_name} -> {new_file_name}"

        if fast_already_processed_check(file_path):
            return (
                f"[skip] Already processed (no header-like text): {file_path}",
                rename_message,
            )

        df = pd.read_csv(file_path, skiprows=21, **READ_OPTS)
        df = df.apply(pd.to_numeric, errors="coerce").dropna(how="all")
        if df.empty:
            return f"[empty] No valid data in {file_path}", rename_message

        # 첫 열만 기존과 같은 등간격 시간으로 교체.
        num_rows, num_cols = df.shape
        if num_rows > 1 and num_cols >= 1:
            start_time = df.iat[0, 0]
            end_time = df.iat[-1, 0]
            if pd.isna(start_time) or pd.isna(end_time):
                dt = 1.0
            else:
                dt = (end_time - start_time) / (num_rows - 1)
            df.iloc[:, 0] = np.arange(num_rows, dtype=float) * float(dt)

        df.to_csv(file_path, index=False, header=False, float_format="%.10f")
        return f"[ok] {file_path}", rename_message

    except Exception as e:
        return f"[err] {file_path}: {e}", rename_message


def _print_result(completed_count: int, total_files: int, result) -> None:
    # 자식 프로세스의 print 대신 부모에서 출력해야 노트북에서도 보인다.
    message, rename_message = result
    if rename_message:
        print(rename_message)
    print(f"[{completed_count}/{total_files}] {message}")


def process_csv_folder(folder_path: str, max_workers: int = 4) -> None:
    """CSV를 파일별로 병렬 처리. 소요 시간에는 프로세스 시작 시간도 포함."""
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1")

    started = perf_counter()
    csv_files = glob.glob(os.path.join(glob.escape(folder_path), "*.csv"))
    if not csv_files:
        print("[info] No CSV files found.")
        return

    total_files = len(csv_files)
    worker_count = min(max_workers, total_files, os.cpu_count() or 1)
    print(
        f"[info] Found {total_files} CSV files. "
        f"Processing with {worker_count} processes..."
    )

    completed_count = 0
    if worker_count == 1:
        # 파일이 하나이거나 병렬 처리를 끈 경우에는 프로세스 시작 비용 생략.
        for file_path in csv_files:
            completed_count += 1
            _print_result(completed_count, total_files, process_one_csv(file_path))
    else:
        # 작업 함수는 import 가능한 모듈에 두어 Windows/Jupyter spawn 지원.
        with ProcessPoolExecutor(
            max_workers=worker_count, mp_context=get_context("spawn")
        ) as executor:
            futures = [executor.submit(process_one_csv, path) for path in csv_files]
            for future in as_completed(futures):
                completed_count += 1
                _print_result(completed_count, total_files, future.result())

    elapsed = perf_counter() - started
    print("-" * 30)
    print(
        f"[info] All tasks finished. "
        f"({completed_count} files processed, {elapsed:.2f} seconds)"
    )
