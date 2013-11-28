from setuptools import setup

setup(
    name='customnoseplugins',
    version="2.3",
    description = 'test plan plugins for the nose testing framework',
    author = 'bao hongbin',
    author_email = 'hongbin.bao@gmail.com',
    license = 'MIT',
    long_description = """\
Extra plugins for the nose testing framework to load test case from a plan file.\n
usage:\n
>>> nosetests --with-plan-loader --plan-file path_of_planfile --loop 10\n

plan file content:\n
[tests]\n
packagename.modulename.classname.testcasename = 3\n
packagename.modulename.classname.testcasename = 5\n

FUTURE support plan file content:\n
[tests]\n
packagename.modulename:classname.testcasename = 3\n
packagename.modulename:classname.testcasename = 5\n

1: allow to custom a test plan file. the plan file can define the test cases name list  and the executed  loop count in one loop.\n All tests will be executed from top to end follow it's own loop count.\n
2: allow to define the test cycle number. the test will be executed cyclically until exceed the cycle number. default only\n executed 1 cycle.\n

tests from python env:\n
>>> from customnoseplugins.planloader import PlanLoaderPlugin\n
>>> nose.run(argv=['--with-plan-loader', --plan-file', 'plan', '--loop', '100'], \naddplugins=[PlanLoaderPlugin()])\n
""",
    packages = ['customnoseplugins'],
    entry_points = {
        'nose.plugins': [
            'plan-loader = customnoseplugins.planloader:PlanLoaderPlugin',
            'dut-configer = customnoseplugins.dutconfiger:DUTConfigerPlugin',
            'screen-monitor = customnoseplugins.screenmonitor:ScreenMonitorPlugin',
            ],
         },
)
