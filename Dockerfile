# The base image for circleci
FROM fedora:32 AS upgrade

WORKDIR /simengine_setup
# Upgrade Fedora
RUN dnf upgrade -y

# Install RPM dependencies
FROM upgrade AS rpm_dependencies
RUN dnf install -y 'dnf-command(builddep)'
RUN dnf install -y rpmdevtools
RUN dnf install -y fedora-packager
RUN dnf install -y wget
RUN dnf install -y python3-pip

# Add neo4j repo
FROM rpm_dependencies AS add_neo4j_repo
COPY ./setup/install-simengine/add-neo4j-repo .
RUN ./add-neo4j-repo

# Install spec files required packages
FROM add_neo4j_repo AS specs_requires
COPY rpm/specfiles/*.spec specfiles/
RUN dnf builddep specfiles/*.spec -y
RUN requires_list=($(rpm --requires --specfile specfiles/*.spec | \
    sed --regexp-extended 's/[[:space:]]+[<>=]+[[:space:]]+/-/')) \
    && for requires_item in "${requires_list[@]}"; \
    do echo "DEPENDENCY=[$requires_item]"; sudo dnf --assumeyes install "$requires_item"; done

FROM specs_requires AS pip_dependencies
# # COPY enginecore/requirements.txt .
# COPY enginecore/dev-requirements.txt .
# # RUN pip install -r ./requirements.txt
# RUN pip install -r ./dev-requirements.txt

FROM pip_dependencies AS python2
RUN dnf install -y python2

FROM python2 AS repo
COPY . repo

FROM repo AS pip
RUN cd ./repo/enginecore && pip install -r ./requirements.txt
RUN pip install -r repo/enginecore/dev-requirements.txt

FROM pip AS entry_point
COPY docker-entrypoint.sh .
ENTRYPOINT ["/simengine_setup/docker-entrypoint.sh"]
