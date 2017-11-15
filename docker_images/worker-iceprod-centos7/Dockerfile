# iceprod_buildbot/worker-iceprod-centos7

FROM centos:7

LABEL description="IceCube - iceprod buildbot worker running centos:7" \
      mounts="shared" \
      cvmfs="true" \
      cpus="1" \
      memory="1000" \
      gpus="0" \
      privileges="sys_admin" \
      devices="/dev/fuse" \
      organization="icecube-buildbot" \
      name="worker-iceprod-centos7" \
      version="0.1"

COPY buildbot.tac /buildbot/buildbot.tac

RUN \
    yum clean all && \
    yum -y install gcc make unzip git subversion wget curl \
        patch binutils file which libffi python-devel \
        gawk fuse fuse-libs attr policycoreutils-python && \
    rpm -ivh https://cvmrepo.web.cern.ch/cvmrepo/yum/cvmfs-release-latest.noarch.rpm && \
    yum -y install cvmfs cvmfs-config-default && \
    cvmfs_config setup && \
    echo -e "CVMFS_REPOSITORIES='icecube.opensciencegrid.org'\nCVMFS_HTTP_PROXY='DIRECT'" > /etc/cvmfs/default.local && \
    mkdir -p /cvmfs/icecube.opensciencegrid.org && \
    yum clean all && \
    curl "https://bootstrap.pypa.io/get-pip.py" | python && \
    pip --no-cache-dir install dumb-init 'twisted[tls]' buildbot-worker && \
    mkdir /shared && \
    useradd -ms /bin/bash buildbot && chown -R buildbot /buildbot

USER root

WORKDIR /buildbot

ENTRYPOINT ["/usr/bin/dumb-init", "--"]

CMD ["bash", "-c", "mount -t cvmfs icecube.opensciencegrid.org /cvmfs/icecube.opensciencegrid.org; su buildbot twistd -ny buildbot.tac"]
