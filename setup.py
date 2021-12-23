from setuptools import setup, find_packages

VERSION          = '1.1.0' 
DESCRIPTION      = '3D and 2D Truss structural analysis'


setup(
        name="slientruss3d", 
        version=VERSION,
        license="MIT",
        author="Shih-Chi Cheng",
        author_email="ezioatiar@gmail.com",
        description=DESCRIPTION,
        url="https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis",
        download_url="https://github.com/leo27945875/Python_Stable_3D_Truss_Analysis/archive/refs/tags/v1.1.0.tar.gz",
        packages=['slientruss3d'],
        install_requires=['numpy', 'matplotlib'], 
        keywords=['python', 'truss', 'civil engineering', 'structural analysis'],
        classifiers= [
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Education",
            "Intended Audience :: Developers",
            "Intended Audience :: Manufacturing",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3.9",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)