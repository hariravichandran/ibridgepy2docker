# IBridgePy on Docker 

Dockerize IBridgePy Platform: (https://ibridgepy.com) to do Algorithmic Trading in Python with Interactive Brokers.

This repo uses the 3.7 Ubuntu files as needed for IBridgePy (e.g., IBridgePy_Ubuntu_Python37_64). Tested Deployment on MacOS Monterey on 2016 13" Macbook Pro. (Unfortunately, it doesn't look like IBridgePy supports Apple Silicon Macs at the Current Time). It *should* work on Linux, but has not been tested.

The Jupyter Image from https://github.com/jupyter/docker-stacks --> base-notebook is used as a template. The `b86753318aa1` tag is used since that tag uses `Python 3.7`, the version we need for IBridgePy to work.

## Installation

 Pull this repo and change to the directory in the terminal.
 
 ```cd <repo-directory>```

 Build container image (Only need to build for the first time/when altering container image):
 
 ```docker build -t ibridgepy .```

 Launch container from built image:
 
 ```docker run -p 10000:8888 -v "${PWD}":/home/jovyan/work ibridgepy```
 
-- This mounts your current directory with IBridgePy files to the home directory of the Jupyter notebook. Hence you can transfer files from your local to Jupyter and edit them there.

Go to the Jupyter URL at Localhost, Port 10000:

```http://127.0.0.1:10000/lab?token=<TOKEN>```

-- Change the token to the one that comes up in the terminal after Jupyter runs.

In the folder, `/IBridgePy_Ubuntu_Python37_64`, you can run the `RUN_ME.py` script:

`python RUN_ME.py`

That will get you started at least!

## TWS
You will have to install TWS on Mac OS X. (https://www.interactivebrokers.com/en/software/macDownload.php)

The ports and other settings need to be setup correctly. See this video: https://www.youtube.com/watch?v=M96ZPXQnngA&t=304s

Hopefully this is helpful. Let me know if it works well and/or if there are any issues.
