# iceprod_buildbot/worker-iceprod-centos7-build

FROM centos:7

LABEL description="IceCube - iceprod buildbot worker with devel packages running centos:7" \
      mounts="cvmfs, shared" \
      cpus="1" \
      memory="2000" \
      gpus="0" \
      organization="icecube-buildbot" \
      name="worker-iceprod-centos7-build" \
      version="0.1"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc gcc-c++ gcc-gfortran autoconf automake make m4 bison \
        libtool patch binutils unzip git subversion wget curl \
        libpng-devel openssl-devel libX11-devel bzip2-devel \
        ncurses-devel readline-devel libXext-devel libXi-devel \
        libXfixes-devel libXft-devel libXmu-devel libXpm-devel \
        libXrandr-devel libXt-devel freeglut-devel libffi-devel \
        file which python-devel && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    mkdir /cvmfs && \
    mkdir /shared && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot

USER buildbot

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["twistd", "-ny", "buildbot.tac"]
