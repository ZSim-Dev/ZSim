import os
from collections import defaultdict

import polars as pl

from zsim.define import DEBUG, DEBUG_LEVEL

buffered_data: dict[str, dict[int, dict[str, int]]] = defaultdict(
    lambda: defaultdict(lambda: defaultdict(int))
)


def report_buff_to_queue(
    character_name: str, time_tick, buff_name: str, buff_count, all_match: bool, level=4
):
    if DEBUG and DEBUG_LEVEL <= level:
        if all_match:
            # 由于Buff的log录入总是在下个tick的开头，所以这里的time_tick要-1
            buffered_data[character_name][time_tick - 1][buff_name] += buff_count


def dump_buff_csv(result_id: str):
    # Check if buffered_data has any content
    if not buffered_data:
        return
        
    for char_name, char_data in buffered_data.items():
        if not char_data:
            continue

        # 收集所有可能的buff名称
        all_buff_names = set()
        for buffs in char_data.values():
            all_buff_names.update(buffs.keys())

        # 构建行数据，确保所有行都有相同的列
        rows = []
        for tick, buffs in char_data.items():
            row = {"time_tick": tick}
            # 确保所有可能的 buff 列都存在于每行中
            for buff_name in all_buff_names:
                row[buff_name] = buffs.get(buff_name, 0)
            rows.append(row)

        if not rows:
            continue

        buff_report_file_path = f"{result_id}/buff_log/{char_name}.csv"
        
        # Ensure the directory exists
        try:
            os.makedirs(os.path.dirname(buff_report_file_path), exist_ok=True)
        except Exception:
            continue

        # Create DataFrame and sort columns
        try:
            df = pl.DataFrame(rows)
            if df.is_empty():
                continue
                
            # Sort columns: time_tick first, then buff names alphabetically for deterministic output.
            buff_columns = sorted([col for col in df.columns if col != "time_tick"])
            df = df.sort("time_tick").select(["time_tick"] + buff_columns)

            # Write CSV file
            df.write_csv(buff_report_file_path, include_bom=True)
        except Exception:
            pass
