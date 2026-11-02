"""ЛР4, вариант 11. Мониторинг ресурсов и времени работы системы."""
import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from statistics import mean

import psutil

INTERVAL = 2
SAMPLES = 15
THRESHOLDS = {"cpu": 70, "ram": 90, "disk": 85}
LOG_FILE = Path(__file__).resolve().parent / "monitor_log.csv"
DISK_PATH = Path(__file__).resolve().anchor  # На Windows C:\, а не случайный текущий диск.


def take_sample():
    return {
        "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage(DISK_PATH).percent,
        "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 4),
    }


def check_alerts(sample):
    return [f"{metric.upper()} = {sample[metric]}% (порог {limit}%)"
            for metric, limit in THRESHOLDS.items() if sample[metric] >= limit]


def summarize(samples):
    return {metric: {"mean": round(mean(s[metric] for s in samples), 3),
                     "max": max(s[metric] for s in samples),
                     "min": min(s[metric] for s in samples)}
            for metric in ("cpu", "ram", "disk", "uptime_hours")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=LOG_FILE)
    args = parser.parse_args()
    samples = []
    psutil.cpu_percent(interval=None)  # Прогрев счётчика перед первым интервалом.
    print(f"Вариант 11: {SAMPLES} замеров, интервал {INTERVAL} с; пороги {THRESHOLDS}")
    print(f"Раздел диска: {DISK_PATH}")
    with args.log.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["time", "cpu", "ram", "disk", "uptime_hours", "alert"])
        writer.writeheader()
        for _ in range(SAMPLES):
            time.sleep(INTERVAL)
            sample = take_sample()
            sample["alert"] = "; ".join(check_alerts(sample))
            writer.writerow(sample)
            stream.flush()
            samples.append(sample)
            mark = f" <-- ВНИМАНИЕ: {sample['alert']}" if sample["alert"] else ""
            print(f"{sample['time']} CPU {sample['cpu']:5.1f}% RAM {sample['ram']:5.1f}% "
                  f"DISK {sample['disk']:5.1f}% UPTIME {sample['uptime_hours']:.4f} ч{mark}", flush=True)
    stats = summarize(samples)
    print("\nМетрика       Среднее     Максимум     Минимум")
    for metric, values in stats.items():
        print(f"{metric:12} {values['mean']:9.3f} {values['max']:12.3f} {values['min']:11.3f}")
    args.log.with_suffix(".summary.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"Журнал сохранён: {args.log}")


if __name__ == "__main__":
    main()
