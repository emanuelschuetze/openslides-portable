#!/usr/bin/env python

import errno
import glob
import os
import re
import shutil
import sys
import zlib
zlib.Z_DEFAULT_COMPRESSION = zlib.Z_BEST_COMPRESSION
import zipfile

import distutils.ccompiler
import distutils.sysconfig

import pkg_resources

import wx

import openslides
import openslides_gui

COMMON_EXCLUDE = [
    r".pyc$",
    r".pyo$",
    r".po$",
    r".egg-info",
    r"\blocale/(?!de/|en/|fr/)[^/]+/"
]

LIBEXCLUDE = [
    r"^site-packages/",
    r"^test/",
    r"^curses/",
    r"^idlelib/",
    r"^lib2to3/",
    r"^lib-tk/",
    r"^msilib/",
]


SITE_PACKAGES = {
    "beautifulsoup4": {
        "copy": ["bs4"],
    },
    "bleach": {
        "copy": ["bleach"],
    },
    "html5lib": {
        "copy": ["html5lib"],
    },
    "django": {
        "copy": ["django"],
        "exclude": [
            r"^django/contrib/admindocs/",
            r"^django/contrib/comments/",
            r"^django/contrib/databrowse/",
            r"^django/contrib/flatpages/",
            r"^django/contrib/formtools/",
            r"^django/contrib/gis/",
            r"^django/contrib/localflavor/",
            r"^django/contrib/markup/",
            r"^django/contrib/redirects/",
            r"^django/contrib/sitemaps/",
            r"^django/contrib/syndication/",
            r"^django/contrib/webdesign/",
        ]
    },
    "django_ckeditor_updated": {
        "copy": ["ckeditor"],
    },
    "django-haystack": {
        "copy": ["haystack"],
    },
    "djangorestframework": {
        "copy": ["rest_framework"],
    },
    "jsonfield": {
        "copy": ["jsonfield"],
    },
    "reportlab": {
        "copy": [
            "reportlab",
        ],
    },
    "roman": {
        "copy": ["roman.py"],
    },
    "setuptools": {
        "copy": [
            "pkg_resources",
            "setuptools",
            "easy_install.py",
        ],
    },
    "six": {
        "copy": ["six.py"],
    },
    "sockjs-tornado": {
        "copy": ["sockjs"],
    },
    "tornado": {
        "copy": ["tornado"],
    },
    "natsort": {
        "copy": ["natsort"],
    },
    "whoosh": {
        "copy": ["whoosh"],
    },
    "wxpython-phoenix": {
        "copy": ["wx"],
        "exclude": [
            r"^wx/lib/",
            r"^wx/py/",
            r"^wx/tools/",
            r"wx/adv.pi",
            r"wx/core.pi",
            r"wx/dataview.pi",
            r"wx/dataview.py",
            r"wx/_dataview.pyd",
            r"wx/freetype6.dll",
            r"wx/glcanvas.pi",
            r"wx/glcanvas.py",
            r"wx/_glcanvas.pyd",
            r"wx/grid.pi",
            r"wx/grid.py",
            r"wx/_grid.pyd",
            r"wx/html.pi",
            r"wx/html.py",
            r"wx/_html.pyd",
            r"wx/html2.pi",
            r"wx/html2.py",
            r"wx/_html2.pyd",
            r"wx/libcairo-2.dll",
            r"wx/libcairo-gobject-2.dll",
            r"wx/libcairo-script-interpreter-2.dll",
            r"wx/libexpat-1.dll",
            r"wx/libfontconfig-1.dll",
            r"wx/libpng14-14.dll",
            r"wx/stc.pi",
            r"wx/stc.py",
            r"wx/_stc.pyd",
            r"wx/richtext.pi",
            r"wx/richtext.py",
            r"wx/_richtext.pyd",
            r"wx/webkit.pi",
            r"wx/webkit.py",
            r"wx/wxmsw30u_aui_vc100.dll",
            r"wx/wxmsw30u_gl_vc100.dll",
            r"wx/wxmsw30u_html_vc100.dll",
            r"wx/wxmsw30u_media_vc100.dll",
            r"wx/wxmsw30u_propgrid_vc100.dll",
            r"wx/wxmsw30u_qa_vc100.dll",
            r"wx/wxmsw30u_ribbon_vc100.dll",
            r"wx/wxmsw30u_richtext_vc100.dll",
            r"wx/wxmsw30u_stc_vc100.dll",
            r"wx/wxmsw30u_webview_vc100.dll",
            r"wx/wxmsw30u_xml_vc100.dll",
            r"wx/wxmsw30u_xrc_vc100.dll",
            r"wx/xrc.pi",
            r"wx/xrc.py",
            r"wx/_xrc.pyd",
            r"wx/xml.pi",
            r"wx/xml.py",
            r"wx/_xml.pyd",
            r"wx/zlib1.dll",
        ],
    },
    "openslides": {
        "copy": ["openslides"],
    },
    "openslides_gui": {
        "copy": ["openslides_gui"],
    },
    "psutil": {
        "copy": ["psutil"],
    },
}

PY_DLLS = [
    "unicodedata.pyd",
    "sqlite3.dll",
    "_sqlite3.pyd",
    "_socket.pyd",
    "select.pyd",
    "_ctypes.pyd",
    "_ssl.pyd",
    "_multiprocessing.pyd",
    "pyexpat.pyd",
]


OPENSLIDES_RC_TMPL = """
#include <winresrc.h>

#define ID_ICO_OPENSLIDES 1

ID_ICO_OPENSLIDES ICON "openslides.ico"

VS_VERSION_INFO VERSIONINFO
  FILEVERSION {version[0]},{version[1]},{version[2]},{version[4]}
  PRODUCTVERSION {version[0]},{version[1]},{version[2]},{version[4]}
  FILEFLAGSMASK VS_FFI_FILEFLAGSMASK
  FILEFLAGS {file_flags}
  FILEOS VOS__WINDOWS32
  FILETYPE VFT_APP
  FILESUBTYPE VFT2_UNKNOWN

  BEGIN
    BLOCK "StringFileInfo"
    BEGIN
      BLOCK "040904E4"
      BEGIN
        VALUE "CompanyName", "OpenSlides team\\0"
        VALUE "FileDescription", "OpenSlides\\0"
        VALUE "FileVersion", "{version_str}\\0"
        VALUE "InternalName", "OpenSlides\\0"
        VALUE "LegalCopyright", "Copyright \\251 2011-2015\\0"
        VALUE "OriginalFilename", "openslides.exe\\0"
        VALUE "ProductName", "OpenSlides\\0"
        VALUE "ProductVersion", "{version_str}\\0"
      END
    END

    BLOCK "VarFileInfo"
    BEGIN
      VALUE "Translation", 0x409, 0x4E4
    END
  END
"""


def compile_re_list(patterns):
    expr = "|".join("(?:{0})".format(x) for x in patterns)
    return re.compile(expr)


def relpath(base, path, addslash=False):
    b = os.path.normpath(os.path.abspath(base))
    p = os.path.normpath(os.path.abspath(path))
    if p == b:
        p = "."
        if addslash:
            p += "/"
        return p

    b += os.sep
    if not p.startswith(b):
        raise ValueError("{0!r} is not relative to {1!r}".format(path, base))
    p = p[len(b):].replace(os.sep, "/")
    if addslash:
        p += "/"

    return p


def filter_excluded_dirs(exclude_pattern, basedir, dirpath, dnames):
    i, l = 0, len(dnames)
    while i < l:
        rp = relpath(basedir, os.path.join(dirpath, dnames[i]), True)
        if exclude_pattern.search(rp):
            del dnames[i]
            l -= 1
        else:
            i += 1


def copy_dir_exclude(exclude, basedir, srcdir, destdir):
    for dp, dnames, fnames in os.walk(srcdir):
        filter_excluded_dirs(exclude, basedir, dp, dnames)

        rp = relpath(basedir, dp)
        target_dir = os.path.join(destdir, rp)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        for fn in fnames:
            fp = os.path.join(dp, fn)
            rp = relpath(basedir, fp)
            if exclude.search(rp):
                continue

            shutil.copyfile(fp, os.path.join(destdir, rp))


def collect_lib(libdir, odir):
    exclude = compile_re_list(COMMON_EXCLUDE + LIBEXCLUDE)
    copy_dir_exclude(exclude, libdir, libdir, os.path.join(odir, "Lib"))


def get_pkg_exclude(name, extra=()):
    exclude = COMMON_EXCLUDE[:]
    exclude.extend(SITE_PACKAGES.get(name, {}).get("exclude", []))
    exclude.extend(extra)
    return compile_re_list(exclude)


def copy_package(name, info, odir):
    copy_things = info.get("copy", [])
    if not copy_things:
        return

    dist = pkg_resources.get_distribution(name)
    exclude = get_pkg_exclude(name)

    site_dir = dist.location
    for thing in copy_things:
        fp = os.path.join(site_dir, thing)
        if not os.path.isdir(fp):
            rp = relpath(site_dir, fp)
            ofp = os.path.join(odir, rp)
            shutil.copyfile(fp, ofp)
        else:
            copy_dir_exclude(exclude, site_dir, fp, odir)


def collect_site_packages(sitedir, odir):
    if not os.path.exists(odir):
        os.makedirs(odir)

    for name, info in SITE_PACKAGES.items():
        copy_package(name, info, odir)


def compile_openslides_launcher():
    try:
        cc = distutils.ccompiler.new_compiler()
        if not cc.initialized:
            cc.initialize()
    except distutils.errors.DistutilsError:
        return False

    cc.add_include_dir(distutils.sysconfig.get_python_inc())
    cc.define_macro("_CRT_SECURE_NO_WARNINGS")

    gui_data_dir = os.path.dirname(openslides_gui.__file__)
    gui_data_dir = os.path.join(gui_data_dir, "data")
    shutil.copyfile(
        os.path.join(gui_data_dir, "openslides.ico"),
        "openslides.ico")
    rcfile = "openslides.rc"
    openslides_version = get_openslides_version()
    with open(rcfile, "w") as f:
        if openslides_version[3] == "final":
            file_flags = "0"
        else:
            file_flags = "VS_FF_PRERELEASE"

        f.write(OPENSLIDES_RC_TMPL.format(
            version=openslides_version,
            version_str=openslides.__version__,
            file_flags=file_flags))

    objs = cc.compile([
        "openslides.c",
        rcfile,
    ])

    cc.link_executable(
        objs, "openslides",
        extra_preargs=["/subsystem:windows", "/nodefaultlib:python34.lib", "/manifest"],
        libraries=["user32", "shell32"]
    )
    return True


def openslides_launcher_update_version_resource():
    try:
        import win32api
        import win32verstamp
    except ImportError:
        sys.stderr.write(
            "Using precompiled executable and pywin32 is not available - "
            "version resource may be out of date!\n")
        return False
    import struct

    openslides_version = get_openslides_version()

    sys.stdout.write("Updating version resource")
    # code based on win32verstamp.stamp() with some minor differences in
    # version handling
    major, minor, sub = openslides_version[:3]
    build = openslides_version[4]
    pre_release = openslides_version[3] != "final"
    version_str = openslides.__version__

    sdata = {
        "CompanyName": "OpenSlides team",
        "FileDescription": "OpenSlides",
        "FileVersion": version_str,
        "InternalName": "OpenSlides",
        "LegalCopyright": u"Copyright \xa9 2011-2015",
        "OriginalFilename": "openslides.exe",
        "ProductName": "OpenSlides",
        "ProductVersion": version_str,
    }
    vdata = {
        "Translation": struct.pack("hh", 0x409, 0x4e4),
    }

    vs = win32verstamp.VS_VERSION_INFO(
        major, minor, sub, build, sdata, vdata, pre_release, False)
    h = win32api.BeginUpdateResource("openslides.exe", 0)
    win32api.UpdateResource(h, 16, 1, vs)
    win32api.EndUpdateResource(h, 0)


def copy_dlls(odir):
    dll_src = os.path.join(sys.exec_prefix, "DLLs")
    dll_dest = os.path.join(odir, "DLLs")
    if not os.path.exists(dll_dest):
        os.makedirs(dll_dest)

    for dll_name in PY_DLLS:
        src = os.path.join(dll_src, dll_name)
        dest = os.path.join(dll_dest, dll_name)
        shutil.copyfile(src, dest)

    pydllname = "python{0}{1}.dll".format(*sys.version_info[:2])
    src = os.path.join(os.environ["WINDIR"], "System32", pydllname)
    dest = os.path.join(dll_dest, pydllname)
    shutil.copyfile(src, dest)


def write_package_info_content(outfile):
    """
    Writes a list of all included packages into outfile.
    """
    text = ['Included Packages\n', 17 * '=' + '\n', '\n']
    for pkg in sorted(SITE_PACKAGES):
        if pkg == "wx":
            # wxpython comes from an installer and has no distribution
            # --> handle it separately
            text.append("wxpython-{0}\n".format(wx.__version__))
        else:
            dist = pkg_resources.get_distribution(pkg)
            text.append("{0}-{1}\n".format(dist.project_name, dist.version))
    with open(outfile, "w") as f:
        f.writelines(text)


def write_metadatafile(infile, outfile):
    """
    Writes content from metadata files like README, AUTHORS and LICENSE into
    outfile.
    """
    with open(infile, "rU") as f:
        text = [l for l in f]
    with open(outfile, "w") as f:
        f.writelines(text)


def main():
    prefix = os.path.dirname(sys.executable)
    libdir = os.path.join(prefix, "Lib")
    sitedir = os.path.join(libdir, "site-packages")
    odir = "dist/openslides-{0}-portable".format(openslides.__version__)

    try:
        shutil.rmtree(odir)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise

    os.makedirs(odir)
    out_site_packages = os.path.join(odir, "Lib", "site-packages")

    collect_lib(libdir, odir)
    collect_site_packages(sitedir, out_site_packages)

    exclude = get_pkg_exclude("openslides")
    copy_dir_exclude(exclude, ".", "openslides", out_site_packages)

    if not compile_openslides_launcher():
        sys.stdout.write("Using prebuild openslides.exe\n")
        openslides_launcher_update_version_resource()

    shutil.copyfile(
        "openslides.exe",
        os.path.join(odir, "openslides.exe"))

    copy_dlls(odir)

    # Info on included packages
    shutil.copytree(
        "licenses",
        os.path.join(odir, "packages-info"))
    write_package_info_content(os.path.join(odir, 'packages-info', 'PACKAGES.txt'))

    # Create plugins directory with README.txt
    plugindir = os.path.join(odir, "openslides", "plugins")
    os.makedirs(plugindir)
    readmetext = ["Please copy your plugin directory into this directory.\n", "\n",
        "For more information about OpenSlides plugins see:\n",
        "https://github.com/OpenSlides/OpenSlides/wiki/De%3APlugins\n"]
    with open(os.path.join(plugindir, 'README.txt'), "w") as readme:
        readme.writelines(readmetext)

    # Add LICENSE and README
    write_metadatafile('LICENSE', os.path.join(odir, 'LICENSE.txt'))
    write_metadatafile('README.rst', os.path.join(odir, 'README.txt'))

    zip_fp = os.path.join(
        "dist", "openslides-{0}-portable.zip".format(
        openslides.__version__))


    with zipfile.ZipFile(zip_fp, "w", zipfile.ZIP_DEFLATED) as zf:
        for dp, dnames, fnames in os.walk(odir):
            for fn in fnames:
                fp = os.path.join(dp, fn)
                rp = relpath(odir, fp)
                zf.write(fp, rp)

    print("Successfully build {0}".format(zip_fp))

def get_openslides_version():
    dist = pkg_resources.get_distribution("openslides")
    state = "dev" if dist.parsed_version.is_prerelease else "final"
    parts = [int(x, 10) for x in dist.parsed_version.base_version.split(".")]
    # we always want 3 parts, filling with 0 if necessary
    parts = (parts + 3 * [0])[:3]
    parts.append(state)
    # always use 0 as build number
    parts.append(0)
    return tuple(parts)


if __name__ == "__main__":
    main()
