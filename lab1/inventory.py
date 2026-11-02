"""ЛР4, вариант 11. Технический паспорт компьютера в JSON."""
import json
import platform
import socket
from datetime import datetime
from pathlib import Path

import psutil


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).astimezone().isoformat(timespec="seconds"),
    }


def get_cpu_info():
    freq = psutil.cpu_freq()
    return {
        "model": platform.processor(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": round(freq.max) if freq else None,
        "load_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    return {"total_gb": round(mem.total / 1024**3, 2),
            "used_percent": mem.percent,
            "available_gb": round(mem.available / 1024**3, 2)}


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except OSError:
            # Включает PermissionError и недоступные съёмные носители.
            continue
        disks.append({"device": part.device, "mountpoint": part.mountpoint,
                      "fs": part.fstype, "total_gb": round(usage.total / 1024**3, 2),
                      "used_percent": usage.percent})
    return disks


def get_network_info():
    interfaces = []
    for name, addrs in psutil.net_if_addrs().items():
        mac = next((a.address for a in addrs if a.family == psutil.AF_LINK), None)
        for addr in addrs:
            if addr.family == socket.AF_INET:
                interfaces.append({"name": name, "ipv4": addr.address,
                                   "netmask": addr.netmask, "mac": mac})
    return interfaces


def analyze(passport):
    recommendations = []
    ram = passport["memory"]["total_gb"]
    cores = passport["cpu"]["physical_cores"]
    if ram < 8:
        recommendations.append("Недостаточно памяти для виртуальных машин и Docker")
    if ram >= 16 and cores is not None and cores >= 6:
        recommendations.append("Подходит для одновременной работы нескольких VM")
    for disk in passport["disks"]:
        if disk["used_percent"] > 85:
            recommendations.append(f"Освободить место на диске {disk['device']}")
    if cores is not None and cores < 4:
        recommendations.append("Процессор может стать узким местом (bottleneck)")
    # Собственное правило: дефицит доступной памяти при текущей нагрузке.
    if passport["memory"]["available_gb"] < 2:
        recommendations.append("Доступно менее 2 ГБ RAM: закройте лишние приложения")
    return recommendations


def main():
    passport = {"collected_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "system": get_system_info(), "cpu": get_cpu_info(),
                "memory": get_memory_info(), "disks": get_disk_info(),
                "network": get_network_info()}
    passport["recommendations"] = analyze(passport)
    filename = Path(__file__).resolve().parent / f"passport_{passport['system']['hostname']}.json"
    filename.write_text(json.dumps(passport, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(passport, indent=2, ensure_ascii=False))
    print(f"\nПаспорт сохранён: {filename.name}")


if __name__ == "__main__":
    main()
