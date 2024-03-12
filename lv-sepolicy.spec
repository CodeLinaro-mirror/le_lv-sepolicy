%global selinuxtype targeted

Summary: Qcom vendor selinux policy
Name:    lv-sepolicy
Version: 1.0
Release: r0
License: BSD-3-Clause-Clear
Source0: %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  checkpolicy, selinux-policy-devel
Requires:       selinux-policy-%{selinuxtype}, setools-console
Requires(post): selinux-policy-%{selinuxtype}
%{?selinux_requires}

%description
Qcom selinux policy package.

%define fileList() \
%defattr(-,root,root) \
%{_datadir}/selinux/packages/%1/*.pp \
%{_datadir}/selinux/devel/include/distributed/*.if \
%verify(not md5 size mtime) %{_datadir}/selinux/%{selinuxtype}/qti-modules.lst \
%nil

%define CompileVendorModule() \
vendor_modules=`cat ../vendor_module_list` \
for module in $vendor_modules; do \
    %make_build -f %{_datadir}/selinux/devel/Makefile ${module}.pp \
done;

%define InstallVendorModule() \
vendor_modules=`cat ../vendor_module_list` \
install -D -p -m 0644 ../vendor_module_list %{buildroot}%{_datadir}/selinux/%{selinuxtype}/qti-modules.lst \
for module in $vendor_modules; do \
    install -D -m 0644 ${module}.pp %{buildroot}%{_datadir}/selinux/packages/targeted/${module}.pp \
    install -D -p -m 0644 ${module}.if %{buildroot}%{_datadir}/selinux/devel/include/distributed/${module}.if \
done;

%define selinux_relabel_postun() \
%{_sbindir}/restorecon -RF /usr/bin &> /dev/null \
%nil

%pre
%selinux_relabel_pre -s %{selinuxtype}

%prep
%setup -q -n lv-sepolicy
mkdir -p compile
mask_modules="qti_adbd"
for i in `find ./lrh -name *.te`;do
    MODULE_DIR="$(basename $(dirname $i))"
    MODULE_NAME=$(basename $i .te)
    if [[ "${mask_modules}" =~ "${MODULE_NAME}" ]];then
        echo "Don't compile this module"
        continue
    fi
    cp -r lrh/${MODULE_DIR}/${MODULE_NAME}.*[^0-9] compile
    echo ${MODULE_NAME} >> vendor_module_list
done

%build
cd compile
%CompileVendorModule

%install
%{__rm} -fR %{buildroot}
mkdir -p %{buildroot}%{_datadir}/selinux/packages/targeted
cd compile
%InstallVendorModule

%post
vendor_modules=`cat %{_datadir}/selinux/%{selinuxtype}/qti-modules.lst`
Modules_String=""
for module in $vendor_modules; do
    Modules_String="${Modules_String} %{_datadir}/selinux/packages/%{selinuxtype}/${module}.pp"
done;
%selinux_modules_install -s %{selinuxtype} -p 100 ${Modules_String}
%selinux_relabel_post -s %{selinuxtype}
selinuxmode="enforcing"
if [[ "${selinuxmode}" = "permissive" ]];then
    if grep -q "SELINUX=enforcing" %{_sysconfdir}/selinux/config;then
        sed -i -e "s:SELINUX=enforcing:SELINUX=permissive:g" %{_sysconfdir}/selinux/config
    fi
fi

%preun
vendor_modules=`cat %{_datadir}/selinux/%{selinuxtype}/qti-modules.lst`
%selinux_modules_uninstall -s %{selinuxtype} -p 100 ${vendor_modules}

%postun
%selinux_relabel_postun

%files
%fileList targeted
