FROM nvidia/cuda:10.2-devel-ubuntu18.04
WORKDIR /code
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y wget libopenexr-dev python3-pip libsm6 libxext6 libxrender-dev libz-dev fonts-dejavu python3 libboost-locale1.65.1 libc6 libfftw3-double3 libfontconfig1 libfreetype6 libgcc1 libgl1 libglew2.0 libglu1-mesa libglu1-mesa-dev  libgomp1 libilmbase12 libjack-dev libjemalloc1 libjpeg8 libopenal1 libopencolorio1v5 libopenexr22 libopenimageio1.7 libopenjp2-7 libopenvdb5.0 libpcre3 libpng16-16 libpython3.6 libsndfile1 libspnav0 libstdc++6 libswscale4 libtbb2 libtiff5 libx11-6 libxfixes3 libxi6 libxml2 libxxf86vm1 zlib1g
RUN wget https://download.blender.org/release/Blender2.82/blender-2.82a-linux64.tar.xz
RUN tar xvf blender-2.82a-linux64.tar.xz
RUN ./blender-2.82a-linux64/2.82/python/bin/python3.7m -m ensurepip
COPY ./assets ./assets
COPY ./modules ./modules
RUN apt-get install -y python3.7-dev
RUN ./blender-2.82a-linux64/2.82/python/bin/pip3 install --global-option=build_ext --global-option="-I/usr/include/python3.7/" openexr
RUN ./blender-2.82a-linux64/2.82/python/bin/pip3 install -r ./modules/bpycv/requirements.txt
COPY *.blend ./
COPY *.py ./
ENV OUT_DIR /out
CMD ./blender-2.82a-linux64/blender scene.blend --background --python render2.py