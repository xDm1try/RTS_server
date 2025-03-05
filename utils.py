import gc


def garbage_collect(func):
    def decorator():
        func()
        gc.collect()
    return decorator
