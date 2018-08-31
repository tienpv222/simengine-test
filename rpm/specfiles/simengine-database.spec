Name:      simengine-database
Version:   1
Release:   2
Summary:   SimEngine - Databases
URL:       https://github.com/Seneca-CDOT/simengine
License:   GPLv3+

Source0:   %{name}-%{version}.tar.gz
BuildArch: noarch

Requires:  neo4j, cypher-shell, redis, python-neo4j-driver, python-redis

%description
Installs the SimEngine database configuration for Neo4j.

%pre
systemctl stop neo4j

%prep
%autosetup -c %{name}

%build

%install
mkdir -p %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/
cp -fp auth %{buildroot}%{_sharedstatedir}/neo4j/data/dbms/

%files
%attr(0644, neo4j, neo4j) %{_sharedstatedir}/neo4j/data/dbms/auth

%post
systemctl enable neo4j --now
systemctl enable redis --now
sleep 10
echo "CREATE CONSTRAINT ON (n:Asset) ASSERT (n.key) IS UNIQUE;" | cypher-shell -u simengine -p simengine

%changelog
* Thu Aug 16 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- Updated package dependencies, converted SPEC file to encompass all database work (previously simegine-neo4jdb)

* Mon Jul 23 2018 Chris Johnson <chris.johnson@senecacollege.ca>
- First alpha flight