from distutils.core import setup

setup(
    name            = "doflicky",
    version         = "5",
    author          = "Ikey Doherty",
    author_email    = "ikey@solus-project.com",
    description     = ("Solus Driver Manager"),
    license         = "GPL-2.0",
    url             = "https://github.com/solus-project/doflicky",
    packages        = ['doflicky'],
    scripts         = ['doflicky-ui'],
    classifiers     = [ "License :: OSI Approved :: GPL-2.0 License"],
    data_files      = [("/usr/share/applications", ["doflicky.desktop"]),
                       ("/usr/share/doflicky/modaliases", ["aliases/broadcom-sta.modaliases"])]
)
