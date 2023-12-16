import pathlib


def package_root():

    return pathlib.Path(__file__).parents[1]


if __name__ == "__main__":
    print(package_root())
