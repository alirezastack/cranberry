
from cranberry.main import CranberryAppTest

def test_cranberry(tmp):
    with CranberryAppTest() as app:
        res = app.run()
        print(res)
        raise Exception

def test_command1(tmp):
    argv = ['command1']
    with CranberryAppTest(argv=argv) as app:
        app.run()
