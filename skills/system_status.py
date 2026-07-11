"""
Skill: system_status
Reports system health and resource usage.
"""
import subprocess
import os
import logging

logger = logging.getLogger("infinimation")

def run(*args, raw_text: str = "") -> str:
    try:
        batt = subprocess.run(
            ["termux-battery-status"],
            capture_output=True, text=True, timeout=5
        )
        batt_info = batt.stdout.strip() if batt.returncode == 0 else "N/A"
        
        stat = os.statvfs('/data')
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemTotal' in line or 'MemAvailable' in line:
                    key, val = line.split(':')
                    mem_info[key.strip()] = int(val.strip().split()[0]) / 1024
        
        return (
            f"📊 System Status\n"
            f"────────────────\n"
            f"🔋 Battery: {batt_info}\n"
            f"💾 Storage: {free_gb:.1f}GB free / {total_gb:.1f}GB total\n"
            f"🧠 RAM: {mem_info.get('MemAvailable', 0):.0f}MB available / {mem_info.get('MemTotal', 0):.0f}MB total"
        )
    except Exception as e:
        logger.error(f"STATUS_ERROR: {e}")
        return f"Status check failed: {str(e)}"
