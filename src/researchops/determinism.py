import os
import random

import numpy as np


def set_determinism(seed: int) -> None:
    os.environ.update(
        {
            "PYTHONHASHSEED": str(seed),
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
    )
    random.seed(seed)
    np.random.seed(seed)
