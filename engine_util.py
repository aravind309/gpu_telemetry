import os
import ctypes
import struct
import time

# Path to the PMU config files
ENGINES_PATH = "/sys/class/drm/card1/engine/"

# Struct for perf_event_attr (Linux syscall interface)
class PerfEventAttr(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint),
        ("size", ctypes.c_uint),
        ("config", ctypes.c_ulong),
        ("sample_period", ctypes.c_ulong),
        ("sample_type", ctypes.c_ulong),
        ("read_format", ctypes.c_ulong),
        ("disabled", ctypes.c_uint, 1),
        ("inherit", ctypes.c_uint, 1),
        ("pinned", ctypes.c_uint, 1),
        ("exclusive", ctypes.c_uint, 1),
        ("exclude_user", ctypes.c_uint, 1),
        ("exclude_kernel", ctypes.c_uint, 1),
        ("exclude_hv", ctypes.c_uint, 1),
        ("exclude_idle", ctypes.c_uint, 1),
        ("mmap", ctypes.c_uint, 1),
        ("comm", ctypes.c_uint, 1),
        ("freq", ctypes.c_uint, 1),
        ("inherit_stat", ctypes.c_uint, 1),
        ("enable_on_exec", ctypes.c_uint, 1),
        ("task", ctypes.c_uint, 1),
        ("watermark", ctypes.c_uint, 1),
        ("precise_ip", ctypes.c_uint, 2),
        ("mmap_data", ctypes.c_uint, 1),
        ("sample_id_all", ctypes.c_uint, 1),
        ("exclude_host", ctypes.c_uint, 1),
        ("exclude_guest", ctypes.c_uint, 1),
        ("exclude_callchain_kernel", ctypes.c_uint, 1),
        ("exclude_callchain_user", ctypes.c_uint, 1),
        ("mmap2", ctypes.c_uint, 1),
        ("comm_exec", ctypes.c_uint, 1),
        ("use_clockid", ctypes.c_uint, 1),
        ("context_switch", ctypes.c_uint, 1),
        ("write_backward", ctypes.c_uint, 1),
        ("namespaces", ctypes.c_uint, 1),
        ("__reserved_1", ctypes.c_uint, 31),
        ("wakeup_events", ctypes.c_uint),
        ("bp_type", ctypes.c_uint),
        ("__reserved_2", ctypes.c_uint64 * 2),
    ]

# Define the syscall function for perf_event_open
syscall = ctypes.CDLL(None).syscall
PERF_EVENT_OPEN = 298  # syscall number for perf_event_open on Linux

def open_perf_event(config):
    """Opens a perf event file descriptor for the given PMU config."""
    attr = PerfEventAttr()
    attr.size = ctypes.sizeof(PerfEventAttr)
    attr.type =34  # PERF_TYPE_HARDWARE
    attr.config = config
    attr.disabled = 1

    fd = syscall(PERF_EVENT_OPEN, ctypes.byref(attr), -1, 0, -1, 0)
    if fd == -1:
        raise OSError("Failed to open perf event")
    return fd

def read_perf_value(fd):
    """Reads the counter value from the perf event file descriptor."""
    data = os.read(fd, 34)
    return struct.unpack("Q", data)[0]

def get_engine_utilization():
    """Reads GPU engine utilization using perf_event_open()"""
    engines = [d for d in os.listdir(ENGINES_PATH) if os.path.isdir(os.path.join(ENGINES_PATH, d))]
    

    for engine in engines:
        config_path = os.path.join(ENGINES_PATH, engine, "class")
        
        if not os.path.exists(config_path):
            continue
        
        try:
            with open(config_path, "r") as f:
                config_value = int(f.read().strip())

            fd = open_perf_event(config_value)
            os.write(fd, b"1")  # Enable counting
            
            time.sleep(1)  # Sample for 1 second
            
            utilization = read_perf_value(fd)
            os.close(fd)

            print(f"Engine: {engine}, Utilization: {utilization}")
        except Exception as e:
            print(f"Error reading {engine}: {e}")

if __name__ == "__main__":
    get_engine_utilization()
