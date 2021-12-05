from setuptools import setup, find_packages

VERSION          = '0.0.9' 
DESCRIPTION      = '3D and 2D Truss structural analysis'


setup(
        name="slientruss3d", 
        version=VERSION,
        license="MIT",
        author="Shih-Chi Cheng",
        author_email="ezioatiar@gmail.com",
        description=DESCRIPTION,
        url="https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis",
        download_url="https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/archive/refs/tags/v0.0.9.tar.gz",
        packages=['slientruss3d'],
        install_requires=['numpy', 'matplotlib'], 
        keywords=['python', 'truss', 'civil engineering', 'structural analysis'],
        classifiers= [
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Intended Audience :: Developers",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)