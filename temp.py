def deco1(func):
    def wrapper(*a, **kw):
        print("deco1")
        func(*a, **kw)
    return wrapper

def deco2(func):
    def wrapper(*a, **kw):
        print("deco2")
        func(*a, **kw)
    return wrapper

@deco1
@deco2
def foo():
    print("hui")

foo()