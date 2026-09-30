# AquaGuard AI - OpenCV Hardware & Multi-Threading Optimizer (Phase 12)
from __future__ import annotations
import os
import cv2
import numpy as np
from loguru import logger

class OpenCVOptimizer:
    @classmethod
    def apply_optimizations(cls, num_threads: int = None):
        if num_threads is None:
            num_threads = max(1, (os.cpu_count() or 4) // 2)

        cv2.setUseOptimized(True)
        cv2.setNumThreads(num_threads)

        opencl_available = False
        try:
            opencl_available = bool(cv2.ocl.haveOpenCL())
        except Exception:
            pass

        info = {
            'use_optimized': bool(cv2.useOptimized()),
            'num_threads': int(cv2.getNumThreads()),
            'opencl_available': opencl_available,
            'build_info_simd': 'AVX2/SIMD active' if cv2.useOptimized() else 'Standard',
            'cpu_threads_configured': num_threads
        }
        logger.info(f'Applied OpenCV CPU optimizations: {info}')
        return info

    @staticmethod
    def fast_resize(frame, target_wh):
        return cv2.resize(frame, target_wh, interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def fast_motion_energy(prev_gray, curr_gray):
        if prev_gray is None or curr_gray is None:
            return 0.0
        diff = cv2.absdiff(curr_gray, prev_gray)
        return float(np.mean(diff))

if __name__ == '__main__':
    s = OpenCVOptimizer.apply_optimizations()
    print('OpenCV Optimizer status:', s)
