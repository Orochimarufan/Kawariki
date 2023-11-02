from os import unlink, chmod
from pathlib import Path
from shutil import rmtree
from tarfile import TarFile, TarInfo
from tarfile import open as taropen
from tempfile import NamedTemporaryFile
from typing import IO, Callable, Optional, Sequence
from urllib.error import URLError
from urllib.request import urlopen
from zipfile import ZipFile, ZipInfo

from .app import App
from .distribution import Distribution
from .misc import ErrorCode, size_str


def download_progress_tar(app: App, url: str, dest: Path, description: str="Downloading file...",
        *, modify_entry: Optional[Callable]=None):
    """
    Download and directly extract a tar archive
    :param app: The global app instance
    :param url: The url to download
    :param dest: Path to extract into
    :param description: Description text for the progress dialog
    :param modify_entry: May be a function (entry: TarInfo)->None to modify archive entries before extracting
    """
    with app.show_progress(f"{description}\n\nConnecting") as p:
        try:
            with urlopen(url) as f:
                maxi = p.maximum = int(f.info().get("content-length", 0))
                with taropen(mode="r|*", fileobj=f, encoding="utf-8") as tar:
                    dest.mkdir(parents=True)
                    while info := tar.next():
                        if modify_entry is not None:
                            if modify_entry(info) is False:
                                continue
                        p.text = f"{description}\n\nExtracting '{info.name}'"
                        # Make sure we never go over 100%
                        if info.offset >= maxi:
                            p.maximum = info.offset + 1
                        p.progress = info.offset
                        # Actually do the work
                        tar.extract(info, dest)
        except URLError as e:
            app.show_error(f"Could not connect to '{url}':\n{e.reason}")
            raise
        except:
            import traceback
            app.show_error(f"Error downloading from '{url}':\n\n{traceback.format_exc()}")
            rmtree(dest, ignore_errors=True)
            raise


def download_dist_progress_tar(app: App, dist: Distribution):
    strip_prefix: Optional[Callable]
    if dist.strip_leading is True:
        def strip_prefix(entry):
            try:
                index = entry.name.index("/")
            except ValueError:
                # Skip files in archive root
                return False
            entry.name = entry.name[index+1:]
    elif dist.strip_leading is not False:
        def strip_prefix(entry):
            # Figure out filename, strip prefix
            # there isn't really a good way of figuring out a common prefix in stream mode
            # so just strip the leading path component if it starts with a known prefix for now
            if '/' in entry.name:
                dir, name = entry.name.split("/", 1)
                if dir.startswith(dist.strip_leading):
                    entry.name = name
    else:
        strip_prefix = None

    download_progress_tar(app, dist.url, dist.path,
        description=f"Downloading distribution '{dist.name}'",
        modify_entry=strip_prefix)


def download_progress(app: App, url: str, dest: IO[bytes], description: str="Downloading file...",
        buffer_size: int=16384):
    """
    Download and directly extract a tar archive
    :param app: The global app instance
    :param url: The url to download
    :param dest: The destination file object
    :param description: Description text for the progress dialog
    """
    with app.show_progress(f"{description}\n\nConnecting") as p:
        try:
            with urlopen(url) as f:
                length = p.maximum = int(f.info().get("content-length", 0))
                fmt = f"{description}\n\nDownloading {{size}}/{size_str(length)}..."
                p.text = fmt.format(size="0")
                buffer = bytearray(buffer_size)
                bytes = 0
                read = f.readinto(buffer)
                while read > 0:
                    dest.write(buffer)
                    bytes += read
                    p.update(text=fmt.format(size=size_str(bytes)), progress=bytes)
                    read = f.readinto(buffer)
        except URLError as e:
            app.show_error(f"Could not connect to '{url}':\n{e.reason}")
            raise
        except:
            import traceback
            app.show_error(f"Error downloading from '{url}':\n\n{traceback.format_exc()}")
            raise


def download_dist_progress_zip(app: App, dist: Distribution):
    strip_prefix: Optional[Callable]
    if dist.strip_leading is True:
        def strip_prefix(entry):
            try:
                index = entry.filename.index("/")
            except ValueError:
                # Skip files in archive root
                return False
            entry.filename = entry.filename[index+1:]
    elif dist.strip_leading is not False:
        def strip_prefix(entry):
            # Figure out filename, strip prefix
            # there isn't really a good way of figuring out a common prefix in stream mode
            # so just strip the leading path component if it starts with a known prefix for now
            if '/' in entry.filename:
                dir, name = entry.filename.split("/", 1)
                if dir.startswith(dist.strip_leading):
                    entry.filename = name
    else:
        strip_prefix = None

    # Download file first
    with NamedTemporaryFile("w+b") as tmp:
        download_progress(app, dist.url, tmp,
            description=f"Downloading distribution '{dist.name}'")

        tmp.seek(0)

        text = f"Extracting distribution '{dist.name}'\n\n"
        with app.show_progress(text) as p:
            try:
                with ZipFile(tmp, 'r') as zf:
                    infos = zf.infolist()
                    p.maximum = len(infos)
                    dist.path.mkdir(parents=True)
                    for i in infos:
                        if strip_prefix is not None:
                            if strip_prefix(i) is False:
                                continue
                        p.text = f"{text}{i.filename}"
                        zf.extract(i, dist.path)
                        if i.create_system == 3 or i.create_system == 19: # ZIP_CREATE_UNIX/OS_X
                            chmod(dist.path / i.filename, (i.external_attr >> 16) & 0o777)
                        p.progress += 1
            except:
                rmtree(dist.path, ignore_errors=True)
                raise

def download_dist_progress_archive(app: App, dist: Distribution):
    # TODO: Decide from content-type instead and unify d/l logic
    try:
        url = dist.url
    except KeyError:
        app.show_error(f"Cannot download distribution '{dist.name}': No download URL specified")
        raise ErrorCode(10)
    if url.endswith(".zip"):
        download_dist_progress_zip(app, dist)
    else:
        download_dist_progress_tar(app, dist)
