# iceprod_buildbot/worker-iceprod-condor-centos7

FROM nvidia/cuda:9.0-runtime-centos7

LABEL description="IceCube - iceprod buildbot worker with condor running centos:7" \
      mounts="shared" \
      cvmfs="true" \
      cpus="4" \
      memory="16000" \
      gpus="0" \
      privileges="sys_admin" \
      devices="/dev/fuse" \
      organization="icecube-buildbot" \
      name="worker-iceprod-condor-centos7" \
      version="0.2"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc gcc-c++ gcc-gfortran autoconf automake make m4 bison \
        libtool patch binutils unzip git subversion wget curl \
        libpng-devel openssl-devel libX11-devel bzip2-devel \
        ncurses-devel readline-devel libXext-devel libXi-devel \
        libXfixes-devel libXft-devel libXmu-devel libXpm-devel \
        libXrandr-devel libXt-devel freeglut-devel libffi-devel \
        file which python-devel gawk fuse fuse-libs attr \
        policycoreutils-python && \
    rpm -ivh https://cvmrepo.web.cern.ch/cvmrepo/yum/cvmfs-release-latest.noarch.rpm && \
    yum -y install cvmfs cvmfs-config-default && \
    cvmfs_config setup && \
    echo -e "CVMFS_REPOSITORIES='icecube.opensciencegrid.org'\nCVMFS_HTTP_PROXY='DIRECT'" > /etc/cvmfs/default.local && \
    mkdir -p /cvmfs/icecube.opensciencegrid.org && \
    yum clean all && \
    mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd && \
    ln -s /usr/local/cuda/lib64/libcudart.so.9.0 /usr/lib64/libcudart.so && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    mkdir /shared && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot && \
    wget -O /buildbot/condor.tar.gz http://prod-exe.icecube.wisc.edu/htcondor/condor-8.7.2-x86_64_RedHat7-stripped.tar.gz && \
    mkdir -p /buildbot/condor-8.7.2/local && \
    tar -C /buildbot -zxf /buildbot/condor.tar.gz && \
    cd /buildbot/condor-8.7.2;HOSTNAME="worker-iceprod-condor-centos7.svc.cluster.local" /buildbot/condor-8.7.2-x86_64_RedHat7-stripped/condor_install --owner buildbot --local-dir=/buildbot/condor-8.7.2 --make-personal-condor && \
    rm -rf /buildbot/condor.tar.gz /buildbot/condor-8.7.2-x86_64_RedHat7-stripped && \
    echo -e "use FEATURE : GPUs\nuse FEATURE : PartitionableSlot\nNUM_CPUS=4\nMEMORY=16000" >> /buildbot/condor-8.7.2/etc/condor_config && \
    echo -e "#!/bin/bash\nsource /buildbot/condor-8.7.2/condor.sh;\ncondor_master;\ntwistd -ny buildbot.tac" > /buildbot/start.sh && \
    chmod +x /buildbot/start.sh && \
    chown -R buildbot /buildbot

USER root

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash", "-c", "mount -t cvmfs icecube.opensciencegrid.org /cvmfs/icecube.opensciencegrid.org; su buildbot start.sh"]
