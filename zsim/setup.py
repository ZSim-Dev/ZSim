from setuptools import Extension, setup

module_LinkedList = Extension(
    "sim_progress.data_struct.LinkedList",
    sources=[r"./sim_progress/data_struct/LinkedList.c"],
)

module_ActionStack = Extension(
    "sim_progress.data_struct.ActionStack",
    sources=[r"./sim_progress/data_struct/ActionStack.cpp"],
)

setup(
    name="LinkedList",
    version="1.0",
    description="A simple linked list extension module",
    ext_modules=[module_LinkedList],
)

setup(
    name="ActionStack",
    version="1.0",
    description="A simple action stack extension module",
    ext_modules=[module_ActionStack],
)
