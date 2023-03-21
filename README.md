# IBridgePy Dockerized

This is a personal effort to Dockerize IBridgePy Platform: https://ibridgepy.com to Automate your Trading.

Please register and download the zip file for 3.7 Ubuntu from the following portal:
https://ibridgepy-portal.herokuapp.com

## Installation

 Pull this repo and add the IBridgePy zip file to the same Folder.

 Build your container Image:
 `docker build -t <your_image_name> .`

 Launch your container from the built image:
 `docker run -itd -p 8888:8888 <your_imange_name>`

## Usage

 Access the Jupyter Portal 'http://localhost:8888', and edit the IBridgePy Config Files to connect to your IB TWS API.

 Make sure to add the Docker Host IP to the whitelisted IPs of your TWS API.

 Load the .ipynb files and Enjoy Testing IBridgePy!
